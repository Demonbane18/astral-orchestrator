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
    "docs": WEBSITE / "docs" / "index.html",
    "docs-getting-started": WEBSITE / "docs" / "getting-started" / "index.html",
    "docs-modes": WEBSITE / "docs" / "modes" / "index.html",
    "docs-routing": WEBSITE / "docs" / "routing" / "index.html",
    "docs-safety": WEBSITE / "docs" / "safety" / "index.html",
    "docs-evidence": WEBSITE / "docs" / "evidence" / "index.html",
    "docs-maintenance": WEBSITE / "docs" / "maintenance" / "index.html",
    "docs-contributing": WEBSITE / "docs" / "contributing" / "index.html",
}

EXPECTED_DESTINATIONS = {
    "home": {"./", "docs/", "install/", "support/", "privacy/", "terms/"},
    "install": {"../", "../docs/", "./", "../support/", "../privacy/", "../terms/"},
    "support": {"../", "../docs/", "./", "../install/", "../privacy/", "../terms/"},
    "privacy": {"../", "../docs/", "../install/", "../support/", "./", "../terms/"},
    "terms": {"../", "../docs/", "../install/", "../support/", "../privacy/", "./"},
    "docs": {"../", "./", "../install/", "../support/", "../privacy/", "../terms/"},
    "docs-getting-started": {
        "../../", "../", "../../install/", "../../support/", "../../privacy/", "../../terms/",
    },
    "docs-modes": {
        "../../", "../", "../../install/", "../../support/", "../../privacy/", "../../terms/",
    },
    "docs-routing": {
        "../../", "../", "../../install/", "../../support/", "../../privacy/", "../../terms/",
    },
    "docs-safety": {
        "../../", "../", "../../install/", "../../support/", "../../privacy/", "../../terms/",
    },
    "docs-evidence": {
        "../../", "../", "../../install/", "../../support/", "../../privacy/", "../../terms/",
    },
    "docs-maintenance": {
        "../../", "../", "../../install/", "../../support/", "../../privacy/", "../../terms/",
    },
    "docs-contributing": {
        "../../", "../", "../../install/", "../../support/", "../../privacy/", "../../terms/",
    },
}

DOC_PAGE_NAMES = tuple(name for name in PAGES if name.startswith("docs"))
DOC_SECTIONS = (
    "getting-started",
    "modes",
    "routing",
    "safety",
    "evidence",
    "maintenance",
    "contributing",
)

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
        self.ids = []
        self._style_block = None

    def handle_starttag(self, tag, attrs):
        attributes = {name.lower(): value for name, value in attrs}
        if "id" in attributes:
            self.ids.append(attributes["id"])
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


def resolve_internal_page_link(source: Path, href: str):
    """Resolve a local clean-URL page link and return its page plus fragment."""
    if "\\" in href:
        raise ValueError(f"link must use URL slashes: {href!r}")

    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith("//"):
        return None, parsed.fragment

    website_root = WEBSITE.resolve()
    link_path = unquote(parsed.path)
    candidate = (
        website_root / link_path.lstrip("/")
        if link_path.startswith("/")
        else source.parent / link_path
    ).resolve()
    if not link_path:
        candidate = source.resolve()
    elif candidate.is_dir() or not candidate.suffix:
        candidate = candidate / "index.html"

    try:
        candidate.relative_to(website_root)
    except ValueError as error:
        raise ValueError(f"link escapes website/: {href!r}") from error
    if not candidate.is_file():
        raise ValueError(f"link does not resolve to a website page: {href!r}")
    return candidate, unquote(parsed.fragment)


class WebsiteContractTests(unittest.TestCase):
    def test_all_public_pages_exist_and_have_one_h1(self):
        self.assertEqual(
            set(PAGES),
            {
                "home",
                "install",
                "support",
                "privacy",
                "terms",
                "docs",
                "docs-getting-started",
                "docs-modes",
                "docs-routing",
                "docs-safety",
                "docs-evidence",
                "docs-maintenance",
                "docs-contributing",
            },
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

    def test_every_page_has_global_docs_navigation(self):
        docs_hrefs = {
            "home": "docs/",
            "install": "../docs/",
            "support": "../docs/",
            "privacy": "../docs/",
            "terms": "../docs/",
            "docs": "./",
            **{name: "../" for name in DOC_PAGE_NAMES if name != "docs"},
        }
        for name, path in PAGES.items():
            with self.subTest(page=name):
                page = page_text(path)
                self.assertIn(f'href="{docs_hrefs[name]}">Docs</a>', page)

    def test_docs_pages_have_complete_local_navigation(self):
        for name in DOC_PAGE_NAMES:
            with self.subTest(page=name):
                page = page_text(PAGES[name])
                links = set(parse_page(PAGES[name]).links)
                self.assertIn('aria-label="Documentation"', page)
                expected = {"./", *[f"{section}/" for section in DOC_SECTIONS]}
                if name != "docs":
                    current = name.removeprefix("docs-")
                    expected = {
                        "./" if section == current else f"../{section}/"
                        for section in DOC_SECTIONS
                    }
                    expected.add("../")
                self.assertTrue(
                    expected.issubset(links),
                    f"{name} is missing documentation navigation destinations",
                )

    def test_every_page_has_unique_ids_and_resolvable_internal_links(self):
        for name, path in PAGES.items():
            with self.subTest(page=name):
                parser = parse_page(path)
                self.assertEqual(
                    len(parser.ids), len(set(parser.ids)), f"{name} has duplicate ids"
                )
                for href in parser.links:
                    with self.subTest(page=name, href=href):
                        target, fragment = resolve_internal_page_link(path, href)
                        if target is None:
                            continue
                        if fragment:
                            self.assertIn(
                                fragment,
                                parse_page(target).ids,
                                f"{href!r} points to a missing fragment",
                            )

    def test_homepage_explains_routing_and_links_the_repository(self):
        home = page_text(PAGES["home"])
        for phrase in (
            "Sol",
            "Astra takes difficult reasoning",
            "Luna",
            "Sol",
            "fresh Sol review",
            "https://github.com/Demonbane18/astral-orchestrator",
        ):
            self.assertIn(phrase, home)

    def test_homepage_presents_exactly_eight_modes(self):
        home = page_text(PAGES["home"])
        self.assertIn("Eight modes", home)
        self.assertIn("Eight delivery modes", home)
        self.assertEqual(
            len(re.findall(r'<article class="mode-card(?: [^"]+)?"', home)),
            8,
        )
        expected_tags = {
            "comet": "Comet",
            "orbit": "Orbit · default",
            "event-horizon": "Event Horizon",
            "singularity": "Singularity · explicit",
            "pulsar": "Pulsar · opt-in",
            "morph": "Morph · explicit",
            "constellation": "Constellation · capacity-aware",
            "hypernova": "Hypernova · explicit",
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
            "one verified sol, luna, or astra primary",
            "no subagents or fresh reviewer",
            "does not claim every host supports multi-agent orchestration",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_homepage_contrasts_singularity_with_hypernova(self):
        home = " ".join(page_text(PAGES["home"]).lower().split())
        for phrase in (
            "opposite of singularity",
            "explicit opt-in",
            "sol max",
            "maximum safely available concurrency",
            "host-advertised capacity",
            "primary consumes one slot",
            "native multiagentsv2 only",
            "no downgrade or fallback",
            "speed and throughput over token efficiency",
            "safety still applies",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_current_version_copy_is_v3_11_0_on_current_pages(self):
        for page in ("home", "install", "support", "docs"):
            with self.subTest(page=page):
                content = page_text(PAGES[page])
                self.assertIn("v3.12.0", content)
        for path in WEBSITE.rglob("*.html"):
            with self.subTest(no_stale_version=path.relative_to(WEBSITE)):
                self.assertNotIn("v3.7.0", page_text(path))

    def test_homepage_explains_live_astral_status(self):
        home = " ".join(page_text(PAGES["home"]).lower().split())
        for phrase in (
            "live astral status",
            "requested and observed",
            "model and effort",
            "first user-facing progress update",
            "before and after every child launch",
            "final handoff",
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

    def test_docs_migrate_exact_install_update_uninstall_and_contributor_commands(self):
        getting_started = page_text(PAGES["docs-getting-started"])
        maintenance = page_text(PAGES["docs-maintenance"])
        contributing = page_text(PAGES["docs-contributing"])
        evidence = page_text(PAGES["docs-evidence"])
        routing = page_text(PAGES["docs-routing"])

        commands_by_page = {
            "getting-started": (
                "codex plugin marketplace add Demonbane18/astral-orchestrator --ref main",
                "codex plugin add astral-orchestrator@astral-orchestrator",
                "git clone https://github.com/Demonbane18/astral-orchestrator.git",
                "cd astral-orchestrator",
                "sh scripts/setup.sh --dry-run",
                "sh scripts/setup.sh",
            ),
            "maintenance": (
                "codex plugin marketplace upgrade astral-orchestrator",
                "codex plugin add astral-orchestrator@astral-orchestrator",
                "sh scripts/setup.sh --refresh",
                "codex plugin remove astral-orchestrator@astral-orchestrator",
                "sh plugins/astral-orchestrator/scripts/install-agents.sh --remove",
                "codex plugin marketplace remove astral-orchestrator",
                "codex plugin list --marketplace astral-orchestrator",
            ),
            "contributing": (
                "python3 -B -m unittest discover -s tests -v",
                "sh plugins/astral-orchestrator/scripts/verify.sh",
                "sh scripts/setup.sh --dry-run",
                "git diff --check",
            ),
            "evidence": (
                "python3 plugins/astral-orchestrator/scripts/benchmark-scorecard.py benchmarks/trials.jsonl",
                "python3 plugins/astral-orchestrator/scripts/benchmark-scorecard.py --format json benchmarks/trials.jsonl",
            ),
            "routing": (
                "sh scripts/configure-effort.sh --show",
                "sh scripts/configure-effort.sh --astra medium",
                "sh scripts/configure-effort.sh --astra medium --luna max --sol high --reviewer high",
                "sh scripts/configure-effort.sh --reset",
            ),
        }
        content_by_page = {
            "getting-started": getting_started,
            "maintenance": maintenance,
            "contributing": contributing,
            "evidence": evidence,
            "routing": routing,
        }
        for page, commands in commands_by_page.items():
            for command in commands:
                with self.subTest(page=page, command=command):
                    self.assertIn(command, content_by_page[page])

    def test_docs_preserve_mode_default_opt_in_and_legacy_alias_contracts(self):
        modes = " ".join(page_text(PAGES["docs-modes"]).lower().split())
        for phrase in (
            "orbit (default)",
            "singularity (explicit opt-in)",
            "pulsar (explicit opt-in)",
            "morph (explicit opt-in)",
            "constellation (explicit opt-in)",
            "hypernova (explicit opt-in)",
            "quick maps to comet",
            "guided maps to orbit",
            "careful maps to event horizon",
            "measured maps to pulsar",
            "legacy alias never changes",
            "raises safeguards",
            "does not broaden the work",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, modes)

    def test_docs_define_the_full_hypernova_contract(self):
        modes = " ".join(page_text(PAGES["docs-modes"]).lower().split())
        routing = " ".join(page_text(PAGES["docs-routing"]).lower().split())
        hypernova = modes.split('id="hypernova"', 1)[1].split("</section>", 1)[0]
        for phrase in (
            "explicit opt-in",
            "opposite of singularity",
            "gpt-6-sol",
            "gpt-6-astra",
            "max",
            "every implementation lane",
            "mandatory fresh",
            "built-in-default reviewer",
            "maximum safely available concurrency",
            "host-advertised capacity",
            "primary consumes one slot",
            'fork_turns: "none"',
            "native multiagentsv2 only",
            "no legacy exact-process fallback",
            "no serial fallback",
            "no self-review fallback",
            "no model or effort downgrade",
            "speed and throughput over token efficiency",
            "event horizon confirmation gates",
            "does not bypass safety or authorization",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, hypernova)
        self.assertNotIn('model: "gpt-6-luna"', hypernova)
        self.assertNotIn("terra", hypernova)
        self.assertIn("--require-sol-ultra", routing)
        self.assertIn("--require-astra-ultra", routing)

    def test_docs_preserve_routing_models_controls_and_status_truthfulness(self):
        routing = " ".join(page_text(PAGES["docs-routing"]).lower().split())
        for phrase in (
            "gpt-6-sol",
            "gpt-6-astra",
            "gpt-6-luna",
            "gpt-6-sol",
            "astra medium",
            "sol high",
            "luna max",
            "sol high",
            "reviewer sol high",
            "agent_type",
            "task_name",
            "model",
            "reasoning_effort",
            "fork_turns",
            "requested is not observed",
            "task name is not proof",
            "allowlisted route fields",
            "mismatch or invalid result blocks",
            "astral_orchestrator_route",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, routing)

    def test_docs_disclose_morph_external_provider_and_safety_limits(self):
        routing = " ".join(page_text(PAGES["docs-routing"]).lower().split())
        safety = " ".join(page_text(PAGES["docs-safety"]).lower().split())
        for phrase in (
            "provider may be external",
            "bounded worker packet",
            "provider traffic is local",
            "does not install opencodex",
            "does not handle credentials",
            "native effort semantics",
            "failure blocks the worker",
        ):
            with self.subTest(route_phrase=phrase):
                self.assertIn(phrase, routing)
        for phrase in (
            "no analytics collection",
            "no extra network client",
            "no api key",
            "no background service",
            "explicit confirmation gate",
            "workspace-write with no special isolation",
            "never overwritten",
            "only shipped files that still match exactly",
            "https://github.com/demonbane18/astral-orchestrator/blob/main/license",
            "https://github.com/demonbane18/astral-orchestrator/blob/main/notice.md",
        ):
            with self.subTest(safety_phrase=phrase):
                self.assertIn(phrase, safety)

    def test_docs_preserve_committed_benchmarks_and_caveats(self):
        evidence = " ".join(page_text(PAGES["docs-evidence"]).split())
        for phrase in (
            "3,403",
            "4,722",
            "10,223",
            "12,401",
            "5,501",
            "53.8%",
            "static instruction-context measurements",
            "not task quality, latency, price, or total-run tokens",
            "published v3.6.0 measurement",
            "100+ automated tests",
            "package verification",
            "does not prove Astral beats single-Sol",
            "invalid exploratory evidence",
            "fresh review found protocol defects",
            "No valid outcome comparison exists.",
            "does not publish outcome, token, time, or quality numbers",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, evidence)

    def test_docs_contributing_page_preserves_license_and_attribution_links(self):
        contributing = page_text(PAGES["docs-contributing"]).lower()
        for link in (
            "https://github.com/demonbane18/astral-orchestrator/blob/main/license",
            "https://github.com/demonbane18/astral-orchestrator/blob/main/notice.md",
            "https://github.com/dannymac180/sol-advisor",
            "https://github.com/blavkgokuvnn/single-agent-skills",
            "https://openrouter.ai/ori/eval",
        ):
            with self.subTest(link=link):
                self.assertIn(link, contributing)

    def test_getting_started_describes_public_clone_and_download_options(self):
        getting_started = page_text(PAGES["docs-getting-started"]).lower()
        self.assertIn("public repository", getting_started)
        self.assertIn("download the public repository", getting_started)
        self.assertIn(
            "git clone https://github.com/demonbane18/astral-orchestrator.git",
            getting_started,
        )
        self.assertNotIn("private repository", getting_started)
        self.assertNotIn("private github repository", getting_started)
        self.assertNotIn("repository is currently private", getting_started)

    def test_support_page_links_to_public_help_routes_without_support_promises(self):
        support = page_text(PAGES["support"]).lower()
        self.assertIn(
            "https://github.com/demonbane18/astral-orchestrator/issues", support
        )
        self.assertIn("../docs/", support)
        self.assertIn("../docs/maintenance/", support)
        self.assertNotIn("readme", support)
        self.assertIn("useful issue", support)
        self.assertNotIn("guaranteed support", support)
        self.assertNotIn("private support", support)

    def test_install_and_support_use_canonical_docs_instead_of_the_readme(self):
        install = page_text(PAGES["install"]).lower()
        support = page_text(PAGES["support"]).lower()
        self.assertIn("../docs/getting-started/", install)
        self.assertIn("../docs/maintenance/", install)
        self.assertIn("../docs/", support)
        self.assertIn("../docs/maintenance/", support)
        self.assertNotIn("readme", install)
        self.assertNotIn("readme", support)

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

    def test_docs_css_is_responsive_focus_visible_and_overflow_safe(self):
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        for selector in (
            ".docs-layout",
            ".docs-nav",
            ".doc-content",
            ".table-scroll",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, stylesheet)
        self.assertRegex(
            stylesheet,
            r"\.table-scroll\s*\{[^}]*overflow-x:\s*auto;",
        )
        self.assertRegex(stylesheet, r"pre\s*\{[^}]*overflow-x:\s*auto;")
        self.assertRegex(
            stylesheet,
            r"\.docs-nav a\s*\{[^}]*min-height:\s*2\.75rem;",
        )
        self.assertIn(":focus-visible", stylesheet)
        self.assertIn("@media (max-width: 48rem)", stylesheet)
        self.assertRegex(
            stylesheet,
            r"@media \(max-width: 48rem\)\s*\{[\s\S]*?\.docs-layout\s*\{[^}]*grid-template-columns:\s*1fr;",
        )

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
            "published v3.6.0 measurement",
            "local Codex and project environment",
            "runs locally on your supplied trials",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_homepage_explains_the_explicit_opt_in_pulsar_mode(self):
        home = page_text(PAGES["home"])
        for phrase in (
            "v3.6.0",
            "Eight modes",
            "Comet",
            "Orbit · default",
            "Event Horizon",
            "Singularity · explicit",
            "Pulsar · opt-in",
            "deliberately slower, evidence-oriented",
            "never auto-selected",
            "One fixed graph, parallel ready items",
            "one canonical dependency graph",
            "deterministic Astra/Luna/Sol routing",
            "identical read-only probes",
            "private, resumable evidence",
            "fresh Sol review",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, home)

    def test_canonical_pages_publish_the_current_instruction_context_measurements(self):
        public_evidence = {
            "docs": " ".join(page_text(PAGES["docs-evidence"]).split()),
            "homepage": " ".join(page_text(PAGES["home"]).split()),
        }
        benchmark = json.loads(
            page_text(ROOT / "benchmarks" / "context-footprint-2026-08-21.json")
        )
        expected_bundles = {
            "core": 3403,
            "quick": 4722,
            "guided": 10223,
            "measured": 12401,
        }
        self.assertEqual(
            {name: benchmark["bundles"][name]["tokens"] for name in expected_bundles},
            expected_bundles,
        )
        self.assertEqual(benchmark["quick_vs_full"]["tokens_avoided"], 5501)
        self.assertEqual(benchmark["quick_vs_full"]["percent_avoided"], 53.8)
        for document, evidence in public_evidence.items():
            for figure in ("3,403", "4,722", "10,223", "12,401", "5,501", "53.8%"):
                with self.subTest(document=document, figure=figure):
                    self.assertIn(figure, evidence)
            for scope_statement in (
                "Comet loads the core skill and mode/risk reference only",
                "static instruction-context measurements",
                "not task quality, latency, price, or total-run tokens",
                "published v3.6.0 measurement",
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

        docs = public_evidence["docs"]
        homepage = public_evidence["homepage"]
        for link in (
            "https://github.com/Demonbane18/astral-orchestrator/blob/main/benchmarks/README.md",
            "https://github.com/Demonbane18/astral-orchestrator/blob/main/benchmarks/context-footprint-2026-08-21.json",
            "https://github.com/Demonbane18/astral-orchestrator/blob/main/benchmarks/results/2026-08-04-invalid-pilot/INVALID.md",
        ):
            for document, evidence in (("docs", docs), ("homepage", homepage)):
                with self.subTest(document=document, link=link):
                    self.assertIn(link, evidence)

    def test_homepage_instruction_context_bar_widths_match_current_evidence(self):
        benchmark = json.loads(
            page_text(ROOT / "benchmarks" / "context-footprint-2026-08-21.json")
        )
        stylesheet = page_text(WEBSITE / "assets" / "site.css")
        pulsar_tokens = benchmark["bundles"]["measured"]["tokens"]

        for css_name, bundle_name in (
            ("pulsar", "measured"),
            ("full", "full"),
            ("comet", "quick"),
            ("core", "core"),
        ):
            with self.subTest(css_name=css_name):
                match = re.search(
                    rf"\.chart-bar--{css_name}\s*\{{(?P<body>.*?)\}}",
                    stylesheet,
                    re.DOTALL,
                )
                self.assertIsNotNone(match)
                width = re.search(r"width:\s*([0-9.]+)%", match.group("body"))
                self.assertIsNotNone(width)
                expected = round(benchmark["bundles"][bundle_name]["tokens"] / pulsar_tokens * 100, 1)
                self.assertEqual(float(width.group(1)), expected)

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
                if name == "home":
                    icon_prefix = "assets/"
                elif name.startswith("docs-"):
                    icon_prefix = "../../assets/"
                else:
                    icon_prefix = "../assets/"
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
