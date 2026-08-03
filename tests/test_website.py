import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"

PAGES = {
    "home": WEBSITE / "index.html",
    "support": WEBSITE / "support" / "index.html",
    "privacy": WEBSITE / "privacy" / "index.html",
    "terms": WEBSITE / "terms" / "index.html",
}

EXPECTED_DESTINATIONS = {
    "home": {"./", "support/", "privacy/", "terms/"},
    "support": {"../", "./", "../privacy/", "../terms/"},
    "privacy": {"../", "../support/", "./", "../terms/"},
    "terms": {"../", "../support/", "../privacy/", "./"},
}

RESOURCE_ATTRIBUTES = {
    "audio": ("src",),
    "embed": ("src",),
    "frame": ("src",),
    "iframe": ("src",),
    "image": ("href", "xlink:href"),
    "img": ("src", "srcset"),
    "input": ("src",),
    "link": ("href",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "track": ("src",),
    "use": ("href", "xlink:href"),
    "video": ("src", "poster"),
}

CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_URL = re.compile(
    r"url\(\s*(?P<quote>['\"]?)(?P<url>[^)'\"]*?)(?P=quote)\s*\)",
    re.IGNORECASE,
)
CSS_STRING_IMPORT = re.compile(
    r"@import\s+(?P<quote>['\"])(?P<url>[^'\"]*)(?P=quote)",
    re.IGNORECASE,
)


class ResourceReference(NamedTuple):
    tag: str
    attribute: str
    url: str


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.links = []
        self.resources = []
        self.inline_styles = []
        self.style_blocks = []
        self._style_block = None

    def handle_starttag(self, tag, attrs):
        attributes = {name.lower(): value for name, value in attrs}
        if tag in {"h1", "h2", "h3"}:
            self.headings.append(tag)
        if tag == "a" and "href" in attributes:
            self.links.append(attributes["href"])
        for attribute in RESOURCE_ATTRIBUTES.get(tag, ()):
            if attribute in attributes:
                for url in urls_from_attribute(attribute, attributes[attribute] or ""):
                    self.resources.append(ResourceReference(tag, attribute, url))
        if "style" in attributes:
            self.inline_styles.append(attributes["style"] or "")
        if tag == "style":
            self._style_block = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self._style_block is not None:
            self._style_block.append(data)

    def handle_endtag(self, tag):
        if tag == "style" and self._style_block is not None:
            self.style_blocks.append("".join(self._style_block))
            self._style_block = None


def urls_from_attribute(attribute: str, value: str):
    """Yield each URL from a resource-bearing HTML attribute."""
    if attribute != "srcset":
        yield value
        return

    candidates = [candidate.strip() for candidate in value.split(",")]
    for candidate in candidates:
        if candidate:
            yield candidate.split(maxsplit=1)[0]
    if not any(candidates):
        yield ""


def css_resource_urls(css: str):
    """Yield URLs referenced by CSS url() and quoted @import rules."""
    uncommented = CSS_COMMENT.sub("", css)
    for match in CSS_URL.finditer(uncommented):
        yield match.group("url").strip()
    for match in CSS_STRING_IMPORT.finditer(uncommented):
        yield match.group("url").strip()


def resolve_local_resource(source: Path, resource: str):
    """Resolve one website resource or reject a network URL and escaped path."""
    if "\\" in resource:
        raise ValueError(f"resource must use URL slashes: {resource!r}")

    parsed = urlsplit(resource)
    if parsed.scheme or parsed.netloc or resource.startswith("//"):
        raise ValueError(f"remote or protocol-relative resource is not allowed: {resource!r}")

    resource_path = unquote(parsed.path)
    if not resource_path and parsed.fragment:
        return None
    if not resource_path:
        raise ValueError(f"resource must name a local file: {resource!r}")

    website_root = WEBSITE.resolve()
    candidate = (
        website_root / resource_path.lstrip("/")
        if resource_path.startswith("/")
        else source.parent / resource_path
    ).resolve()
    try:
        candidate.relative_to(website_root)
    except ValueError as error:
        raise ValueError(f"resource escapes website/: {resource!r}") from error
    if not candidate.is_file():
        raise ValueError(f"resource is not an existing regular file: {resource!r}")
    return candidate


def page_text(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required website page is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(page_text(path))
    return parser


class WebsiteContractTests(unittest.TestCase):
    def test_four_public_pages_exist_and_have_one_h1(self):
        self.assertEqual(set(PAGES), {"home", "support", "privacy", "terms"})
        for name, path in PAGES.items():
            with self.subTest(page=name):
                parser = parse_page(path)
                self.assertEqual(parser.headings.count("h1"), 1)

    def test_every_page_links_to_the_four_relative_public_destinations(self):
        for name, path in PAGES.items():
            with self.subTest(page=name):
                links = set(parse_page(path).links)
                self.assertTrue(
                    EXPECTED_DESTINATIONS[name].issubset(links),
                    f"{name} is missing navigation destinations",
                )

    def test_homepage_explains_routing_and_has_copyable_install_command(self):
        home = page_text(PAGES["home"])
        for phrase in (
            "Sol",
            "Luna",
            "Terra",
            "fresh Sol review",
            "git clone https://github.com/Demonbane18/astral-orchestrator.git",
            "sh scripts/setup.sh --dry-run",
            "https://github.com/Demonbane18/astral-orchestrator",
        ):
            self.assertIn(phrase, home)

    def test_readme_describes_public_clone_and_download_options(self):
        readme = page_text(ROOT / "README.md").lower()
        self.assertIn("public repository", readme)
        self.assertIn("download the public repository", readme)
        self.assertIn(
            "git clone https://github.com/demonbane18/astral-orchestrator.git", readme
        )
        self.assertNotIn("private repository", readme)
        self.assertNotIn("private github repository", readme)
        self.assertNotIn("repository is currently private", readme)

    def test_support_page_links_to_public_help_routes_without_support_promises(self):
        support = page_text(PAGES["support"]).lower()
        self.assertIn(
            "https://github.com/demonbane18/astral-orchestrator/issues", support
        )
        self.assertIn("readme", support)
        self.assertIn("useful issue", support)
        self.assertNotIn("guaranteed support", support)
        self.assertNotIn("private support", support)

    def test_privacy_policy_states_the_local_no_collection_posture(self):
        privacy = page_text(PAGES["privacy"]).lower()
        for phrase in (
            "2026-08-03",
            "no analytics",
            "no cookies",
            "no accounts",
            "no forms",
            "first-party data collection",
            "vercel",
            "request metadata",
            "no project-operated backend",
            "prompts",
            "files",
            "api keys",
            "usage analytics",
            "codex/openai",
            "github",
            "their own terms",
        ):
            self.assertIn(phrase, privacy)

    def test_terms_state_independence_mit_and_user_responsibilities(self):
        terms = page_text(PAGES["terms"]).lower()
        for phrase in (
            "2026-08-03",
            "mit license",
            "website",
            "use at your own risk",
            "no warranty",
            "commands and permissions",
            "john paul furigay fusin",
            "independent open-source project",
            "not legal advice",
        ):
            self.assertIn(phrase, terms)
        self.assertNotIn("officially endorsed by openai", terms)

    def test_pages_load_only_existing_local_resources(self):
        for name, path in PAGES.items():
            with self.subTest(page=name):
                parser = parse_page(path)
                for resource in parser.resources:
                    with self.subTest(
                        page=name,
                        tag=resource.tag,
                        attribute=resource.attribute,
                        resource=resource.url,
                    ):
                        resolve_local_resource(path, resource.url)
                for css in (*parser.inline_styles, *parser.style_blocks):
                    for resource in css_resource_urls(css):
                        with self.subTest(page=name, css_resource=resource):
                            resolve_local_resource(path, resource)

        for stylesheet in WEBSITE.rglob("*.css"):
            with self.subTest(stylesheet=stylesheet.relative_to(ROOT)):
                for resource in css_resource_urls(page_text(stylesheet)):
                    with self.subTest(stylesheet=stylesheet.relative_to(ROOT), resource=resource):
                        resolve_local_resource(stylesheet, resource)

    def test_site_javascript_does_not_use_network_capable_browser_apis(self):
        # This is a source-level regression guard for this small static site, not a
        # complete proof that browser code cannot communicate over the network.
        script = page_text(WEBSITE / "assets" / "site.js")
        prohibited_patterns = {
            "fetch": r"\bfetch\s*\(",
            "XMLHttpRequest": r"\bXMLHttpRequest\b",
            "WebSocket": r"\bWebSocket\b",
            "EventSource": r"\bEventSource\b",
            "sendBeacon": r"\bsendBeacon\s*\(",
            "remote dynamic import": r"\bimport\s*\(\s*['\"`](?:https?:)?//",
        }
        for api, pattern in prohibited_patterns.items():
            with self.subTest(api=api):
                self.assertNotRegex(script, pattern)

    def test_resource_parser_covers_common_browser_loader_attributes(self):
        parser = PageParser()
        parser.feed(
            """
            <link href="site.css" rel="stylesheet">
            <script src="site.js"></script>
            <img src="image.png" srcset="image-2x.png 2x">
            <embed src="document.pdf">
            <frame src="legacy.html">
            <iframe src="frame.html"></iframe>
            <object data="object.bin"></object>
            <audio src="audio.mp3"></audio>
            <video src="video.mp4" poster="poster.png"></video>
            <source src="video.webm" srcset="image.webp 1x">
            <track src="captions.vtt">
            <input src="button.png" type="image">
            <image href="vector.svg"></image>
            <use href="sprite.svg#mark"></use>
            """
        )
        self.assertEqual(
            {(resource.tag, resource.attribute, resource.url) for resource in parser.resources},
            {
                ("link", "href", "site.css"),
                ("script", "src", "site.js"),
                ("img", "src", "image.png"),
                ("img", "srcset", "image-2x.png"),
                ("embed", "src", "document.pdf"),
                ("frame", "src", "legacy.html"),
                ("iframe", "src", "frame.html"),
                ("object", "data", "object.bin"),
                ("audio", "src", "audio.mp3"),
                ("video", "src", "video.mp4"),
                ("video", "poster", "poster.png"),
                ("source", "src", "video.webm"),
                ("source", "srcset", "image.webp"),
                ("track", "src", "captions.vtt"),
                ("input", "src", "button.png"),
                ("image", "href", "vector.svg"),
                ("use", "href", "sprite.svg#mark"),
            },
        )

    def test_local_resource_resolver_rejects_network_and_invalid_paths(self):
        page = PAGES["home"]
        self.assertEqual(
            resolve_local_resource(page, "assets/site.css"),
            WEBSITE / "assets" / "site.css",
        )
        for resource in (
            "https://example.test/site.js",
            "//example.test/site.js",
            "../README.md",
            "assets/",
            "assets/missing.css",
        ):
            with self.subTest(resource=resource):
                with self.assertRaises(ValueError):
                    resolve_local_resource(page, resource)

    def test_vercel_configuration_is_valid_json_and_sets_security_headers(self):
        path = WEBSITE / "vercel.json"
        config = json.loads(page_text(path))
        self.assertEqual(config.get("cleanUrls"), True)
        catch_all_rules = [
            rule for rule in config.get("headers", []) if rule.get("source") == "/(.*)"
        ]
        self.assertEqual(len(catch_all_rules), 1)
        headers = {
            header["key"].lower(): header["value"]
            for header in catch_all_rules[0].get("headers", [])
        }
        self.assertEqual(
            headers.get("content-security-policy"),
            "default-src 'self'; base-uri 'self'; connect-src 'self'; "
            "font-src 'self'; form-action 'none'; frame-ancestors 'none'; "
            "img-src 'self'; object-src 'none'; script-src 'self'; "
            "style-src 'self'; upgrade-insecure-requests",
        )
        self.assertEqual(headers.get("x-frame-options"), "DENY")
        self.assertEqual(headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(
            headers.get("referrer-policy"), "strict-origin-when-cross-origin"
        )
        self.assertEqual(
            headers.get("permissions-policy"),
            "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=(), usb=()",
        )
        self.assertEqual(headers.get("cross-origin-opener-policy"), "same-origin")


if __name__ == "__main__":
    unittest.main()
