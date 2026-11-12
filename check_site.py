"""Validate the static site and generated bibliography using only the stdlib."""
from collections import Counter
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


def clean(value):
    return " ".join(value.split())


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path, self.ids, self.links = path, set(), []
        self.h1 = self.current = 0
        self.lang = self.viewport = self.description = self.canonical = False
        self.publications, self.options, self.metrics = [], {}, {}
        self.publication = self.select = self.metric = None
        self.metric_depth = self.strong_depth = 0
        self.in_details = False

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
        if tag == "article" and "data-publication" in a:
            assert self.publication is None, "Nested publication articles"
            self.publication = {"attrs": a, "text": [], "strong": [], "links": [], "details": []}
            self.publications.append(self.publication)
        if self.publication is not None:
            self.strong_depth += tag == "strong"
            if tag == "div" and "pub-details" in a.get("class", "").split():
                self.in_details = True
            if tag == "a":
                self.publication["links"].append(a.get("href", ""))
        if tag == "select":
            self.select = a.get("id")
            self.options[self.select] = []
        if tag == "option" and self.select:
            self.options[self.select].append(a.get("value", ""))
        if "data-metric" in a:
            assert self.metric is None, "Nested metrics"
            self.metric = a["data-metric"]
            self.metric_depth = 0
            self.metrics[self.metric] = []
        if self.metric:
            self.metric_depth += 1

    def handle_endtag(self, tag):
        if self.publication is not None:
            self.strong_depth -= tag == "strong"
            if tag == "div":
                self.in_details = False
            if tag == "article":
                self.publication = None
        if tag == "select":
            self.select = None
        if self.metric:
            self.metric_depth -= 1
            if self.metric_depth == 0:
                self.metric = None

    def handle_data(self, data):
        if self.publication is not None:
            self.publication["text"].append(data)
            if self.strong_depth:
                self.publication["strong"].append(data)
            if self.in_details:
                self.publication["details"].append(data)
        if self.metric:
            self.metrics[self.metric].append(data)


def validate_data(catalog):
    date.fromisoformat(catalog["updated"])
    assert catalog.get("scope"), "Missing bibliography scope"
    works, all_dois = catalog["works"], set()
    assert works, "Empty bibliography"
    for work in works:
        doi = work["doi"]
        for identifier in [doi] + work["doi_aliases"]:
            identifier = identifier.lower()
            assert re.fullmatch(r"10\.\d{4,9}/\S+", identifier), f"Invalid DOI: {identifier}"
            assert identifier not in all_dois, f"Duplicate work or translation DOI: {identifier}"
            all_dois.add(identifier)
        assert work["title"].strip() and work["journal"].strip(), f"Missing citation title/journal: {doi}"
        assert work["category"] and work["topics"], f"Missing classification: {doi}"
        assert len(work["topics"]) == len(set(work["topics"])), f"Duplicate topics: {doi}"
        assert isinstance(work["year"], int), f"Invalid year: {doi}"
        assert isinstance(work.get("citation_year", work["year"]), int), f"Invalid citation year: {doi}"
        stamp = work["sort_date"]
        assert re.fullmatch(r"\d{4}(?:-\d{2}){0,2}", stamp), f"Invalid date precision: {doi}"
        parts = list(map(int, stamp.split("-")))
        date(*(parts + [1] * (3 - len(parts))))
        assert parts[0] == work["year"], f"Year/sort-date disagreement: {doi}"
        authors = work["authors"]
        assert authors and all(a["name"].strip() for a in authors), f"Missing authors: {doi}"
        positions = [i for i, author in enumerate(authors) if author["self"]]
        assert len(positions) == 1, f"Expected one identified profile author: {doi}"
        assert work["first_author"] == (positions == [0]), f"First-author flag disagrees with author order: {doi}"
        assert work["sole_author"] == (len(authors) == 1), f"Sole-author flag disagrees with author list: {doi}"
        assert work["sources"] and all(urlsplit(s).scheme == "https" for s in work["sources"]), f"Missing/invalid provenance: {doi}"
        assert not work.get("pmid") or str(work["pmid"]).isdigit(), f"Invalid PMID: {doi}"
    return works


def check_catalog(catalog, page, home, bib):
    works = validate_data(catalog)
    expected = {work["doi"].lower(): work for work in works}
    rendered = [p["attrs"]["data-doi"].lower() for p in page.publications]
    assert len(rendered) == len(set(rendered)), "Duplicate publication rendered"
    assert set(rendered) == set(expected), "Rendered publications differ from the catalog"
    for article in page.publications:
        a = article["attrs"]
        work = expected[a["data-doi"].lower()]
        assert a["data-year"] == str(work["year"]), f"Wrong rendered year: {work['doi']}"
        assert a["data-first"] == str(work["first_author"]).lower(), f"Wrong authorship filter: {work['doi']}"
        assert set(a["data-topics"].split("|")) == set(work["topics"]), f"Wrong topic filters: {work['doi']}"
        text = clean(" ".join(article["text"]))
        assert clean(work["title"].rstrip(".")) in text, f"Missing full title: {work['doi']}"
        citation = clean(" ".join(article["details"]))
        assert re.match(rf"{work.get('citation_year', work['year'])}\b", citation), f"Wrong displayed citation year: {work['doi']}"
        offset = 0
        for author in work["authors"]:
            name = clean(author["name"])
            position = text.find(name, offset)
            assert position >= offset, f"Missing or reordered author {name}: {work['doi']}"
            offset = position + len(name)
            if author["self"]:
                assert name in clean(" ".join(article["strong"])), f"Profile author not highlighted: {work['doi']}"
        links = {link.lower() for link in article["links"]}
        for doi in [work["doi"]] + work["doi_aliases"]:
            assert f"https://doi.org/{doi.lower()}" in links, f"Missing DOI/version link: {doi}"
        if work.get("pmid"):
            assert f"https://pubmed.ncbi.nlm.nih.gov/{work['pmid']}/" in links, f"Missing PubMed link: {work['doi']}"
    required = {"publication-filters", "publication-search", "publication-year", "publication-topic", "first-author", "reset-filters", "result-count", "no-results"}
    assert required <= page.ids, "Missing publication filter controls or status"
    years = Counter(work["year"] for work in works)
    assert {f"year-{year}" for year in years} <= page.ids, "Missing publication year groups"
    assert set(filter(None, page.options["publication-year"])) == {str(y) for y in years}, "Year filter differs from catalog"
    topics = {topic for work in works for topic in work["topics"]}
    assert set(filter(None, page.options["publication-topic"])) == topics, "Topic filter differs from catalog"
    metrics = {"publications": len(works), "recent": years[int(catalog["updated"][:4])], "first": sum(w["first_author"] for w in works), "sole": sum(w["sole_author"] for w in works)}
    for key, value in metrics.items():
        numbers = re.findall(r"\b\d+\b", " ".join(home.metrics.get(key, [])))
        assert numbers and int(numbers[0]) == value, f"Homepage metric {key} disagrees with catalog"
    entries = re.split(r"(?m)^@\w+\s*\{", bib)[1:]
    assert len(entries) == len(works), "BibTeX entry count differs from catalog"
    bib_dois, keys = set(), set()
    for entry in entries:
        key = entry.split(",", 1)[0].strip()
        assert key and key not in keys, f"Duplicate BibTeX key: {key}"
        keys.add(key)
        match = re.search(r"\bdoi\s*=\s*\{([^}]+)\}", entry, re.I)
        assert match, f"Missing BibTeX DOI: {key}"
        doi = match[1].lower()
        assert doi in expected and doi not in bib_dois, f"Unexpected/duplicate BibTeX DOI: {doi}"
        bib_dois.add(doi)
        year = re.search(r"\byear\s*=\s*\{(\d{4})\}", entry)
        work = expected[doi]
        assert year and int(year[1]) == work.get("citation_year", work["year"]), f"Wrong BibTeX year: {doi}"
        author = re.search(r"\bauthor\s*=\s*\{([^}]+)\}", entry)
        assert author, f"Missing BibTeX authors: {doi}"
        names = [a["family"] + ", " + a["given"] for a in work["authors"]]
        decoded = re.sub(r"\\([&%_#])", r"\1", author[1])
        assert decoded.split(" and ") == names, f"Missing or reordered BibTeX authors: {doi}"
    assert bib_dois == set(expected), "BibTeX works differ from catalog"
    return works, years


def main():
    pages = {}
    for path in ROOT.rglob("*.html"):
        page = Page(path)
        page.feed(path.read_text(encoding="utf-8"))
        assert page.h1 == page.current == 1, f"Heading/navigation issue: {path}"
        assert all((page.lang, page.viewport, page.description, page.canonical)), f"Metadata issue: {path}"
        pages[path.resolve()] = page
    assert pages, "No public HTML pages"
    links_checked = 0
    for path, page in pages.items():
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                assert url.scheme in {"https", "mailto"}, f"Unexpected external link: {href}"
                continue
            target = (ROOT / unquote(url.path).lstrip("/") if url.path.startswith("/") else path.parent / unquote(url.path)).resolve() if url.path else path
            assert target.is_relative_to(ROOT), f"Link escapes site: {href}"
            if target.is_dir():
                target /= "index.html"
            assert target.is_file(), f"Broken local link in {path}: {href}"
            if url.fragment:
                assert target in pages and unquote(url.fragment) in pages[target].ids, f"Broken anchor: {href}"
            links_checked += 1
    catalog = json.loads((ROOT / "data/publications.json").read_text(encoding="utf-8"))
    works, years = check_catalog(catalog, pages[ROOT / "publications/index.html"], pages[ROOT / "index.html"], (ROOT / "publications/publications.bib").read_text(encoding="utf-8"))
    print(f"PASS: {len(pages)} pages; {links_checked} local links and anchors; metadata and navigation.")
    print(f"PASS: {len(works)} unique works; years {dict(sorted(years.items(), reverse=True))}; complete ordered authors, DOI versions, filters, homepage metrics and BibTeX.")


if __name__ == "__main__":
    main()
