from html.parser import HTMLParser
from pathlib import Path


class EvidenceScope(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_scope = False
        self.scope = []
        self.evidence_title = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.in_scope = self.in_scope or attributes.get("class") == "scope-note"
        self.evidence_title = self.evidence_title or attributes.get("id") == "evidence-title"

    def handle_data(self, data):
        if self.in_scope:
            self.scope.append(data)


page = Path(__file__).resolve().parents[3] / "website/index.html"
parser = EvidenceScope()
parser.feed(page.read_text(encoding="utf-8"))
scope = " ".join(parser.scope).lower()
assert parser.evidence_title
assert "static instruction-context" in scope
assert "product-wide" not in scope
