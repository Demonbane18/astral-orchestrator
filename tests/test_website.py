import json
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"

PAGES = {
    "home": WEBSITE / "index.html",
    "install": WEBSITE / "install" / "index.html",
    "support": WEBSITE / "support" / "index.html",
    "privacy": WEBSITE / "privacy" / "index.html",
    "terms": WEBSITE / "terms" / "index.html",
}

EXPECTED_DESTINATIONS = {
    "home": {"./", "install/", "support/", "privacy/", "terms/"},
    "install": {"../", "./", "../support/", "../privacy/", "../terms/"},
    "support": {"../", "./", "../install/", "../privacy/", "../terms/"},
    "privacy": {"../", "../install/", "../support/", "./", "../terms/"},
    "terms": {"../", "../install/", "../support/", "../privacy/", "./"},
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


def css_variables(stylesheet: str, selector: str):
    """Return hexadecimal custom properties declared in one CSS selector."""
    match = re.search(
        rf"{re.escape(selector)}\s*\{{(?P<body>.*?)^\}}", stylesheet, re.DOTALL | re.MULTILINE
    )
    if not match:
        raise AssertionError(f"CSS selector is missing: {selector}")
    return dict(
        re.findall(
            r"^\s*(--[\w-]+):\s*(#[0-9a-fA-F]{6});",
            match.group("body"),
            re.MULTILINE,
        )
    )


def relative_luminance_channels(channels):
    """Calculate WCAG relative luminance from normalized sRGB channels."""
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def relative_luminance(color: str):
    """Calculate WCAG relative luminance for one #RRGGBB color."""
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    return relative_luminance_channels(channels)


def contrast_ratio(foreground: str, background: str):
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def alpha_composited_contrast(foreground: str, alpha: float, background: str):
    """Calculate contrast after compositing a hexadecimal foreground over a background."""
    foreground_channels = [
        int(foreground[index : index + 2], 16) / 255 for index in (1, 3, 5)
    ]
    background_channels = [
        int(background[index : index + 2], 16) / 255 for index in (1, 3, 5)
    ]
    composite = [
        foreground_channel * alpha + background_channel * (1 - alpha)
        for foreground_channel, background_channel in zip(
            foreground_channels, background_channels
        )
    ]
    lighter, darker = sorted(
        (
            relative_luminance_channels(composite),
            relative_luminance_channels(background_channels),
        ),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def contrast_against_composited_background(
    foreground: str, background: str, alpha: float, underlay: str
):
    """Calculate foreground contrast against an alpha-composited background."""
    foreground_channels = [
        int(foreground[index : index + 2], 16) / 255 for index in (1, 3, 5)
    ]
    background_channels = [
        int(background[index : index + 2], 16) / 255 for index in (1, 3, 5)
    ]
    underlay_channels = [
        int(underlay[index : index + 2], 16) / 255 for index in (1, 3, 5)
    ]
    composite = [
        background_channel * alpha + underlay_channel * (1 - alpha)
        for background_channel, underlay_channel in zip(
            background_channels, underlay_channels
        )
    ]
    lighter, darker = sorted(
        (
            relative_luminance_channels(foreground_channels),
            relative_luminance_channels(composite),
        ),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


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
    def test_all_public_pages_exist_and_have_one_h1(self):
        self.assertEqual(
            set(PAGES), {"home", "install", "support", "privacy", "terms"}
        )
        for name, path in PAGES.items():
            with self.subTest(page=name):
                parser = parse_page(path)
                self.assertEqual(parser.headings.count("h1"), 1)

    def test_pages_do_not_skip_heading_levels(self):
        heading_level = {"h1": 1, "h2": 2, "h3": 3}
        for name, path in PAGES.items():
            with self.subTest(page=name):
                levels = [heading_level[tag] for tag in parse_page(path).headings]
                for previous, current in zip(levels, levels[1:]):
                    self.assertLessEqual(
                        current,
                        previous + 1,
                        f"{name} skips from h{previous} to h{current}",
                    )

    def test_every_page_links_to_the_relative_public_destinations(self):
        for name, path in PAGES.items():
            with self.subTest(page=name):
                links = set(parse_page(path).links)
                self.assertTrue(
                    EXPECTED_DESTINATIONS[name].issubset(links),
                    f"{name} is missing navigation destinations",
                )

    def test_homepage_explains_routing_and_links_the_repository(self):
        home = page_text(PAGES["home"])
        for phrase in (
            "Sol",
            "Luna",
            "Terra",
            "fresh Sol review",
            "https://github.com/Demonbane18/astral-orchestrator",
        ):
            self.assertIn(phrase, home)

    def test_homepage_presents_exactly_six_modes(self):
        home = page_text(PAGES["home"])
        self.assertIn("Six modes", home)
        self.assertEqual(
            len(re.findall(r'<article class="mode-card(?: [^"]+)?"', home)),
            6,
        )
        expected_tags = {
            "quick": "Quick",
            "guided": "Guided · default",
            "careful": "Careful",
            "measured": "Measured · opt-in",
            "morph": "Morph · explicit",
            "constellation": "Constellation · capacity-aware",
        }
        for mode, label in expected_tags.items():
            with self.subTest(mode=mode):
                self.assertEqual(
                    len(re.findall(rf'class="mode-tag mode-tag--{mode}"', home)),
                    1,
                )
                self.assertEqual(home.count(f">{label}</span>"), 1)

    def test_homepage_explains_primary_checker_morph_and_constellation_boundaries(self):
        home = " ".join(page_text(PAGES["home"]).lower().split())
        for phrase in (
            "automatic primary checker",
            "allowlisted local model/effort evidence",
            "one-time user confirmation",
            "mismatch or invalid evidence blocks",
            "explicitly selected worker model and effort",
            "provider may be external",
            "fresh review is required",
            "independent, non-overlapping cards",
            "host-advertised capacity",
            "one primary consumes a slot",
            "serial fallback",
            "does not claim every provider has native effort semantics",
            "does not claim every host supports multi-agent orchestration",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_current_version_copy_is_v3_5_0_on_current_pages(self):
        for page in ("home", "install", "support"):
            with self.subTest(page=page):
                content = page_text(PAGES[page])
                self.assertIn("v3.5.0", content)

    def test_homepage_explains_live_astral_status(self):
        home = " ".join(page_text(PAGES["home"]).lower().split())
        for phrase in (
            "live astral status",
            "requested and observed",
            "model and effort",
            "sol high is sufficient",
            "sol ultra is not required",
        ):
            self.assertIn(phrase, home)

    def test_verification_copy_uses_future_proof_test_count(self):
        home = page_text(PAGES["home"])
        self.assertIn("100+ automated tests", home)
        self.assertNotIn("109 automated tests", home)

    def test_install_page_has_copyable_install_command(self):
        install = page_text(PAGES["install"])
        for phrase in (
            "codex plugin marketplace add Demonbane18/astral-orchestrator --ref main",
            "codex plugin add astral-orchestrator@astral-orchestrator",
            "bundled exact-process launcher",
            "Optional native-profile setup",
            "https://github.com/Demonbane18/astral-orchestrator",
        ):
            self.assertIn(phrase, install)

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
            "2026-08-16",
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
            "morph",
            "external",
            "bounded work packet",
            "native effort semantics",
        ):
            self.assertIn(phrase, privacy)

    def test_privacy_policy_explains_the_local_theme_preference(self):
        privacy = page_text(PAGES["privacy"]).lower()
        for phrase in (
            "color preference",
            "local storage",
            "does not transmit",
        ):
            self.assertIn(phrase, privacy)

    def test_privacy_policy_states_retention_and_user_controls(self):
        privacy = " ".join(page_text(PAGES["privacy"]).lower().split())
        for phrase in (
            "2026-08-16",
            "retention",
            "until you clear",
            "does not receive or retain",
            "vercel controls",
            "uninstall the plugin",
            "remove local settings",
            "request deletion",
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
            "external-provider terms",
            "multi-agent orchestration",
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

    def test_site_javascript_degrades_without_match_media(self):
        script = page_text(WEBSITE / "assets" / "site.js")
        self.assertIn('typeof window.matchMedia === "function"', script)

    def test_semantic_gold_and_focus_colors_meet_contrast_requirements(self):
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        light = css_variables(stylesheet, ":root")
        dark = css_variables(stylesheet, ':root[data-theme="dark"]')

        for background in (
            "--bg",
            "--bg-soft",
            "--surface",
            "--surface-2",
            "--gold-soft",
        ):
            with self.subTest(color="light gold", background=background):
                self.assertGreaterEqual(
                    contrast_ratio(light["--gold"], light[background]), 4.5
                )

        for palette, backgrounds in (
            (
                light,
                (
                    "--bg",
                    "--bg-soft",
                    "--surface",
                    "--surface-2",
                    "--gold-soft",
                    "--hero-bg",
                    "--code-bg",
                ),
            ),
            (
                dark,
                ("--bg", "--bg-soft", "--surface", "--surface-2", "--hero-bg", "--code-bg"),
            ),
        ):
            for background in backgrounds:
                with self.subTest(color="focus", background=background):
                    self.assertGreaterEqual(
                        contrast_ratio(palette["--focus-ring"], palette[background]),
                        3.0,
                    )

    def test_emphasized_headings_do_not_depend_on_background_clipping(self):
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        fallback = re.search(
            r"^\.gradient-text\s*\{(?P<body>.*?)^\}",
            stylesheet,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(fallback)
        self.assertIn("color: var(--gold);", fallback.group("body"))
        for unsupported_effect in (
            "background:",
            "background-clip",
            "color: transparent",
            "text-fill-color",
        ):
            with self.subTest(fallback_excludes=unsupported_effect):
                self.assertNotIn(unsupported_effect, fallback.group("body"))

        hero_fallback = re.search(
            r"^\.hero \.gradient-text\s*\{(?P<body>.*?)^\}",
            stylesheet,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(hero_fallback)
        self.assertIn("color: var(--gold-bright);", hero_fallback.group("body"))
        self.assertNotIn("background:", hero_fallback.group("body"))

        for unreliable_effect in (
            "background-clip: text",
            "text-fill-color: transparent",
        ):
            with self.subTest(stylesheet_excludes=unreliable_effect):
                self.assertNotIn(unreliable_effect, stylesheet)

    def test_emphasis_and_theme_toggle_hover_colors_meet_contrast_requirements(self):
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        light = css_variables(stylesheet, ":root")
        dark = css_variables(stylesheet, ':root[data-theme="dark"]')

        for theme, palette, backgrounds in (
            (
                "light",
                light,
                ("--bg", "--bg-soft", "--surface", "--surface-2", "--gold-soft"),
            ),
            ("dark", dark, ("--bg", "--bg-soft", "--surface", "--surface-2")),
        ):
            for background in backgrounds:
                with self.subTest(theme=theme, color="--gold", background=background):
                    self.assertGreaterEqual(
                        contrast_ratio(palette["--gold"], palette[background]), 4.5
                    )

            with self.subTest(theme=theme, color="--gold-bright", background="--hero-bg"):
                self.assertGreaterEqual(
                    contrast_ratio(palette["--gold-bright"], palette["--hero-bg"]),
                    3.0,
                )

        self.assertRegex(
            stylesheet,
            r"\.theme-toggle:hover\s*\{\s*color: var\(--gold\);\s*"
            r"border-color: var\(--gold\);",
        )
        for theme, palette in (("light", light), ("dark", dark)):
            with self.subTest(theme=theme, state="theme toggle glyph and border"):
                self.assertGreaterEqual(
                    contrast_ratio(palette["--gold"], palette["--surface"]), 3.0
                )

    def test_route_chevron_and_terminal_caption_meet_contrast_requirements(self):
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        light = css_variables(stylesheet, ":root")
        dark = css_variables(stylesheet, ':root[data-theme="dark"]')

        self.assertRegex(
            stylesheet,
            r"\.route-step summary:hover \.route-chevron\s*\{\s*"
            r"color: var\(--gold\);\s*background: var\(--gold-soft\);",
        )
        for theme, palette in (("light", light), ("dark", dark)):
            with self.subTest(theme=theme, state="route disclosure chevron"):
                self.assertGreaterEqual(
                    contrast_ratio(palette["--gold"], palette["--gold-soft"]), 3.0
                )

        caption = re.search(
            r"\.terminal-bar span\s*\{(?P<body>.*?)^\}", stylesheet, re.DOTALL | re.MULTILINE
        )
        self.assertIsNotNone(caption)
        alpha_match = re.search(
            r"color:\s*rgb\(255 255 255 / (?P<alpha>0?\.\d+)\);",
            caption.group("body"),
        )
        self.assertIsNotNone(alpha_match)
        alpha = float(alpha_match.group("alpha"))
        self.assertGreaterEqual(alpha, 0.46)
        for theme, palette in (("light", light), ("dark", dark)):
            with self.subTest(theme=theme, state="terminal caption"):
                self.assertGreater(
                    alpha_composited_contrast("#ffffff", alpha, palette["--code-bg"]),
                    4.5,
                )

    def test_light_sticky_header_is_legible_above_the_dark_hero(self):
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        light = css_variables(stylesheet, ":root")

        self.assertRegex(
            stylesheet,
            r"\.site-header\s*\{[\s\S]*?background: var\(--header-bg\);",
        )
        self.assertEqual(light["--header-bg"], light["--bg"])
        self.assertGreaterEqual(
            contrast_against_composited_background(
                light["--muted"],
                light["--header-bg"],
                1.0,
                light["--hero-bg"],
            ),
            4.5,
        )

    def test_copy_controls_keep_the_default_label_and_latest_feedback(self):
        script = page_text(WEBSITE / "assets" / "site.js")
        copy_start = script.index('document.querySelectorAll("[data-copy-target]")')
        ready_marker = script.index('root.classList.add("js", "js-ready")', copy_start)
        copy_block = script[copy_start:ready_marker]

        self.assertLess(
            copy_block.index("const originalLabel = button.textContent;"),
            copy_block.index('button.addEventListener("click", async () => {'),
        )
        self.assertIn("let activation = 0;", copy_block)
        self.assertIn("let resetTimer;", copy_block)
        self.assertIn("window.clearTimeout(resetTimer);", copy_block)
        self.assertIn("const currentActivation = ++activation;", copy_block)
        self.assertIn("if (currentActivation !== activation) return;", copy_block)
        self.assertIn("button.textContent = originalLabel;", copy_block)
        self.assertIn("status.textContent = \"\";", copy_block)
        reset_guard = copy_block.index("if (currentActivation !== activation) return;")
        self.assertLess(reset_guard, copy_block.index("status.textContent = \"\";"))
        activation_increment = copy_block.index("const currentActivation = ++activation;")
        self.assertLess(
            activation_increment,
            copy_block.index("await copyToClipboard"),
        )
        self.assertLess(
            copy_block.index("clearResetTimer();", activation_increment),
            copy_block.index("await copyToClipboard"),
        )
        feedback_guard = copy_block.index(
            "if (currentActivation !== activation) return;", activation_increment
        )
        self.assertLess(
            feedback_guard,
            copy_block.index("button.textContent = copyLabel;"),
        )

    def test_system_theme_change_uses_shared_apply_and_sync_path(self):
        script = page_text(WEBSITE / "assets" / "site.js")
        sync_start = script.index("function syncThemeToggles()")
        apply_start = script.index("function applyTheme()")
        system_change_start = script.index("function onSystemThemeChange()")
        system_listener_start = script.index('if (typeof systemQuery.addEventListener === "function")')
        ready_marker = 'root.classList.add("js", "js-ready")'

        sync_body = script[sync_start:apply_start]
        self.assertIn("toggle.dataset.choice = choice;", sync_body)
        self.assertIn('toggle.setAttribute("aria-label", label);', sync_body)
        self.assertIn('toggle.setAttribute("title", label);', sync_body)

        apply_body = script[apply_start:system_change_start]
        self.assertIn("syncThemeToggles();", apply_body)

        system_change_body = script[system_change_start:system_listener_start]
        self.assertIn('if (themeChoice() === "system")', system_change_body)
        self.assertIn("applyTheme();", system_change_body)
        self.assertIn(
            'systemQuery.addEventListener("change", onSystemThemeChange);', script
        )

        registration = script.index("themeToggles.push(toggle);")
        second_apply = script.index("\n    applyTheme();", registration)
        self.assertLess(registration, second_apply)
        self.assertLess(second_apply, script.index(ready_marker))

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for theme runtime coverage")
    def test_theme_controls_work_when_local_storage_access_fails(self):
        harness = r'''
          const failure = process.argv[1];
          let storedTheme = null;
          let systemListener;
          const root = {
            dataset: {},
            classes: new Set(),
            classList: { add(...names) { names.forEach((name) => root.classes.add(name)); } },
          };
          const systemQuery = {
            matches: false,
            addEventListener(event, listener) {
              if (event === "change") systemListener = listener;
            },
          };
          const reducedMotionQuery = { matches: true };
          const meta = { setAttribute(name, value) { this[name] = value; } };
          const toggle = {
            dataset: {},
            attributes: {},
            listeners: {},
            setAttribute(name, value) { this.attributes[name] = value; },
            addEventListener(name, listener) { this.listeners[name] = listener; },
          };
          global.window = {
            matchMedia(query) {
              return query.includes("color-scheme") ? systemQuery : reducedMotionQuery;
            },
            localStorage: {
              getItem() {
                if (failure === "read") throw new Error("read unavailable");
                return storedTheme;
              },
              setItem(key, value) {
                if (failure === "write") throw new Error("write unavailable");
                storedTheme = value;
              },
            },
          };
          global.document = {
            documentElement: root,
            readyState: "complete",
            querySelector(selector) { return selector.includes("theme-color") ? meta : null; },
            querySelectorAll(selector) {
              return selector === "[data-theme-toggle]" ? [toggle] : [];
            },
            getElementById() { return null; },
          };
          require(process.argv[2]);

          function expectTheme(choice, rendered, label) {
            if (toggle.dataset.choice !== choice) {
              throw new Error(`expected ${choice} choice, got ${toggle.dataset.choice}`);
            }
            if (root.dataset.theme !== rendered) {
              throw new Error(`expected ${rendered} rendering, got ${root.dataset.theme}`);
            }
            if (!toggle.attributes["aria-label"].includes(label)) {
              throw new Error(`expected label to include ${label}`);
            }
          }

          expectTheme("system", "light", "currently light");
          toggle.listeners.click();
          expectTheme("light", "light", "Theme: light.");
          toggle.listeners.click();
          expectTheme("dark", "dark", "Theme: dark.");
          toggle.listeners.click();
          expectTheme("system", "light", "currently light");
          if (!systemListener) throw new Error("system theme listener was not registered");
          systemQuery.matches = true;
          systemListener();
          expectTheme("system", "dark", "currently dark");
        '''
        for failure in ("read", "write"):
            with self.subTest(local_storage=failure):
                result = subprocess.run(
                    [
                        "node",
                        "-e",
                        harness,
                        failure,
                        str(WEBSITE / "assets" / "site.js"),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_client_controls_remain_hidden_until_handlers_are_ready(self):
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        script = page_text(WEBSITE / "assets" / "site.js")
        for selector in ("[data-theme-toggle]", "[data-copy-target]"):
            with self.subTest(selector=selector):
                self.assertIn(f":root:not(.js-ready) {selector}", stylesheet)

        ready_marker = 'root.classList.add("js", "js-ready")'
        self.assertIn(ready_marker, script)
        self.assertLess(
            script.index('document.querySelectorAll("[data-copy-target]")'),
            script.index(ready_marker),
        )

    def test_homepage_qualifies_locality_and_instruction_context_claims(self):
        home = page_text(PAGES["home"])
        script = page_text(WEBSITE / "assets" / "site.js")
        for claim in (
            "100% local",
            "Zero network calls",
            "Everything stays on your machine",
            "smaller than most system prompts",
            "nothing leaves your machine",
        ):
            with self.subTest(claim=claim):
                self.assertNotIn(claim, home)
        self.assertNotIn("Everything is local", script)
        for phrase in (
            "local plugin runtime",
            "No project-operated backend",
            "published v3.2.0 measurement",
            "local Codex and project environment",
            "runs locally on your supplied trials",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_homepage_explains_the_explicit_opt_in_measured_mode(self):
        home = page_text(PAGES["home"])
        for phrase in (
            "v3.2.0",
            "Six modes",
            "Quick",
            "Guided · default",
            "Careful",
            "Measured · opt-in",
            "deliberately slower, evidence-oriented",
            "never auto-selected",
            "one canonical work card",
            "deterministic Sol/Luna/Terra routing",
            "identical read-only probes",
            "private, resumable evidence",
            "fresh Sol review",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_homepage_publishes_the_current_instruction_context_measurements(self):
        public_evidence = {
            "README": " ".join(page_text(ROOT / "README.md").split()),
            "homepage": " ".join(page_text(PAGES["home"]).split()),
        }
        benchmark = json.loads(
            page_text(ROOT / "benchmarks" / "context-footprint-2026-08-04.json")
        )
        expected_bundles = {
            "core": 2036,
            "quick": 3696,
            "guided": 5636,
            "measured": 7795,
        }
        self.assertEqual(
            {name: benchmark["bundles"][name]["tokens"] for name in expected_bundles},
            expected_bundles,
        )
        self.assertEqual(benchmark["quick_vs_full"]["tokens_avoided"], 1940)
        self.assertEqual(benchmark["quick_vs_full"]["percent_avoided"], 34.4)
        for document, evidence in public_evidence.items():
            for figure in ("2,036", "3,696", "5,636", "7,795", "1,940", "34.4%"):
                with self.subTest(document=document, figure=figure):
                    self.assertIn(figure, evidence)
            for scope_statement in (
                "static instruction-context measurements",
                "not task quality, latency, price, or total-run tokens",
                "published v3.2.0 measurement",
            ):
                with self.subTest(document=document, scope_statement=scope_statement):
                    self.assertIn(scope_statement, evidence)

        for document, evidence in public_evidence.items():
            for statement in (
                "progressive context loading",
                "exact pinned routes",
                "objective checks plus fresh review",
                "local privacy/no-analytics runtime posture",
                "current repository verification passed",
                "100+ automated tests",
                "package verification",
                "validates behavior and contracts",
                "does not prove Astral beats single-Sol",
                "first end-to-end pilot",
                "invalid exploratory evidence",
                "fresh review found protocol defects",
                "No valid outcome comparison exists.",
                "does not publish outcome, token, time, or quality numbers",
            ):
                with self.subTest(document=document, statement=statement):
                    self.assertIn(statement, evidence)

        readme = public_evidence["README"]
        homepage = public_evidence["homepage"]
        for link in (
            "benchmarks/README.md",
            "benchmarks/context-footprint-2026-08-04.json",
            "benchmarks/results/2026-08-04-invalid-pilot/INVALID.md",
        ):
            with self.subTest(readme_link=link):
                self.assertIn(link, readme)

        for link in (
            "https://github.com/Demonbane18/astral-orchestrator/blob/main/benchmarks/README.md",
            "https://github.com/Demonbane18/astral-orchestrator/blob/main/benchmarks/context-footprint-2026-08-04.json",
            "https://github.com/Demonbane18/astral-orchestrator/blob/main/benchmarks/results/2026-08-04-invalid-pilot/INVALID.md",
        ):
            with self.subTest(homepage_link=link):
                self.assertIn(link, homepage)

    def test_homepage_credits_ori_eval_without_claiming_a_runtime_dependency(self):
        home = page_text(PAGES["home"])
        for phrase in (
            "https://openrouter.ai/ori/eval",
            "https://openrouter.ai/skills/spawn-ori-eval",
            "inspired the pinned/reproducible evaluation and state-tracking method",
            "does not run Ori or OpenRouter",
            "no OpenRouter runtime or API dependency",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_every_public_page_uses_the_current_web_icons(self):
        for name, path in PAGES.items():
            with self.subTest(page=name):
                page = page_text(path)
                icon_prefix = "assets/" if name == "home" else "../assets/"
                self.assertIn(
                    f'<link rel="icon" type="image/png" href="{icon_prefix}astral-orchestrator-favicon-32.png">',
                    page,
                )
                self.assertIn(
                    f'<link rel="apple-touch-icon" href="{icon_prefix}astral-orchestrator-touch-icon.png">',
                    page,
                )

    def test_current_web_icons_exist(self):
        for asset in (
            "astral-orchestrator-favicon-32.png",
            "astral-orchestrator-touch-icon.png",
        ):
            with self.subTest(asset=asset):
                self.assertTrue((WEBSITE / "assets" / asset).is_file())

    def test_github_star_links_do_not_fabricate_a_starred_state(self):
        repository_url = "https://github.com/Demonbane18/astral-orchestrator"
        for name, path in PAGES.items():
            with self.subTest(page=name):
                page = page_text(path)
                self.assertIn(repository_url, page)
                self.assertIn(
                    'aria-label="Open Astral Orchestrator on GitHub in a new tab"',
                    page,
                )

        script = page_text(WEBSITE / "assets" / "site.js")
        self.assertNotIn("astral-starred", script)
        self.assertNotIn("data-star-button", script)
        self.assertNotIn("You starred Astral Orchestrator", script)

    def test_install_copy_controls_have_dedicated_live_feedback(self):
        install = page_text(PAGES["install"])
        for status_id in ("install-command-copy-status", "codex-prompt-copy-status"):
            with self.subTest(status_id=status_id):
                self.assertIn(f'aria-describedby="{status_id}"', install)
                self.assertIn(
                    f'id="{status_id}" role="status" aria-live="polite" aria-atomic="true"',
                    install,
                )

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
