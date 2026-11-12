"""Small dependency-free check of the static site's internal links and metadata."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path, self.ids, self.links = path, set(), []
        self.h1 = self.current = 0
        self.lang = self.viewport = self.description = self.canonical = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            assert a["id"] not in self.ids, f"Duplicate id in {self.path}: {a['id']}"
            self.ids.add(a["id"])
        self.h1 += tag == "h1"
        self.current += tag == "a" and a.get("aria-current") == "page"
        self.lang |= tag == "html" and a.get("lang") == "en"
        self.viewport |= tag == "meta" and a.get("name") == "viewport"
        self.description |= tag == "meta" and a.get("name") == "description" and bool(a.get("content"))
        self.canonical |= tag == "link" and a.get("rel") == "canonical" and a.get("href", "").startswith("https://torkitor.github.io/")
        if tag == "img":
            assert a.get("alt"), f"Missing image description: {self.path}"
        for key in ("href", "src"):
            if key in a:
                assert a[key].strip(), f"Empty {key}: {self.path}"
                self.links.append(a[key])


pages = {}
for path in ROOT.rglob("*.html"):
    page = Page(path)
    page.feed(path.read_text(encoding="utf-8"))
    assert page.h1 == page.current == 1, f"Heading/navigation issue: {path}"
    assert all((page.lang, page.viewport, page.description, page.canonical)), f"Metadata issue: {path}"
    pages[path.resolve()] = page

assert len(pages) == 4, "Expected four public pages"
links_checked = 0
for path, page in pages.items():
    for href in page.links:
        url = urlsplit(href)
        if url.scheme or url.netloc:
            assert url.scheme in {"https", "mailto"}, f"Unexpected external link: {href}"
            continue
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        assert target.is_relative_to(ROOT), f"Link escapes site: {href}"
        if target.is_dir():
            target /= "index.html"
        assert target.is_file(), f"Broken local link in {path}: {href}"
        if url.fragment:
            assert target in pages and unquote(url.fragment) in pages[target].ids, f"Broken anchor: {href}"
        links_checked += 1
print(f"PASS: {len(pages)} pages; {links_checked} local links and anchors; metadata and navigation.")
