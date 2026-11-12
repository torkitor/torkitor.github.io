"""Validate the static site and generated publication/review records with the stdlib."""
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
        self.review_text, self.review_rows = [], []
        self.review_markers = {"data-review-total": [], "data-review-journals": []}
        self.review_section_depth = self.review_marker_depth = 0
        self.review_marker = self.review_row = self.review_count = None

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
        if tag == "section" and a.get("id") == "peer-review":
            assert not self.review_section_depth, f"Nested peer-review section: {self.path}"
            self.review_section_depth = 1
        elif tag == "section" and self.review_section_depth:
            self.review_section_depth += 1
        for marker in self.review_markers:
            if marker in a:
                assert self.review_section_depth, f"Review metric outside its section: {self.path}"
                assert self.review_marker is None, f"Nested review metrics: {self.path}"
                capture = []
                self.review_markers[marker].append(capture)
                self.review_marker = (tag, capture)
                self.review_marker_depth = 0
        if self.review_marker and tag == self.review_marker[0]:
            self.review_marker_depth += 1
        if tag == "tr" and "data-review-journal" in a:
            assert self.review_section_depth, f"Review table outside its section: {self.path}"
            assert self.review_row is None, f"Nested review table rows: {self.path}"
            self.review_row = {"name": a["data-review-journal"], "text": [], "counts": [], "dates": []}
            self.review_rows.append(self.review_row)
        if self.review_row is not None:
            if tag == "td" and "review-count" in a.get("class", "").split():
                self.review_count = []
                self.review_row["counts"].append(self.review_count)
            if tag == "time":
                self.review_row["dates"].append(a.get("datetime"))

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
        if self.review_marker and tag == self.review_marker[0]:
            self.review_marker_depth -= 1
            if self.review_marker_depth == 0:
                self.review_marker = None
        if tag == "td":
            self.review_count = None
        if tag == "tr":
            self.review_row = None
        if tag == "section" and self.review_section_depth:
            self.review_section_depth -= 1

    def handle_data(self, data):
        if self.publication is not None:
            self.publication["text"].append(data)
            if self.strong_depth:
                self.publication["strong"].append(data)
            if self.in_details:
                self.publication["details"].append(data)
        if self.metric:
            self.metrics[self.metric].append(data)
        if self.review_section_depth:
            self.review_text.append(data)
        if self.review_marker:
            self.review_marker[1].append(data)
        if self.review_row is not None:
            self.review_row["text"].append(data)
        if self.review_count is not None:
            self.review_count.append(data)


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


def check_peer_review(records, home, about):
    updated = date.fromisoformat(records["updated"])
    assert records.get("source", "").strip(), "Missing peer-review source attribution"
    journals, additional = records["journals"], records["additional_journals"]
    assert journals, "Empty peer-review journal list"
    names = set()
    for journal in journals:
        name, count = journal["name"], journal["manuscripts"]
        assert isinstance(name, str) and clean(name), "Missing review journal name"
        key = clean(name).casefold()
        assert key not in names, f"Duplicate peer-review journal: {name}"
        names.add(key)
        assert type(count) is int and count >= 0, f"Invalid manuscript count: {name}"
        assert date.fromisoformat(journal["updated"]) <= updated, f"Future review journal date: {name}"
    for name in additional:
        assert isinstance(name, str) and clean(name), "Additional journals must be names without counts"
        key = clean(name).casefold()
        assert key not in names, f"Duplicate or already-counted additional journal: {name}"
        names.add(key)
    total = sum(journal["manuscripts"] for journal in journals)
    expected_metrics = {"data-review-total": total, "data-review-journals": len(journals)}
    for page in (home, about):
        assert "peer-review" in page.ids, f"Missing peer-review section: {page.path}"
        for marker, number in expected_metrics.items():
            captures = page.review_markers[marker]
            assert len(captures) == 1, f"Missing/duplicate {marker}: {page.path}"
            assert clean("".join(captures[0])) == str(number), f"Review metric disagrees with counted journal data: {marker}, {page.path}"
    assert "about/#peer-review" in home.links, "Missing homepage link to peer-review details"
    expected = {journal["name"]: journal for journal in journals}
    rendered = [row["name"] for row in about.review_rows]
    assert len(rendered) == len(set(rendered)), "Duplicate rendered peer-review journal"
    assert set(rendered) == set(expected), "Peer-review table differs from counted journal data"
    for row in about.review_rows:
        journal = expected[row["name"]]
        assert clean(journal["name"]) in clean(" ".join(row["text"])), f"Missing displayed review journal: {journal['name']}"
        assert len(row["counts"]) == 1, f"Missing/duplicate manuscript count cell: {journal['name']}"
        assert clean("".join(row["counts"][0])) == str(journal["manuscripts"]), f"Wrong displayed manuscript count: {journal['name']}"
        assert row["dates"] == [journal["updated"]], f"Wrong displayed review date: {journal['name']}"
    review_text = clean(" ".join(about.review_text))
    for name in additional:
        assert clean(name) in review_text, f"Missing additional review journal: {name}"
    return total, len(journals), len(additional)


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
    reviews = json.loads((ROOT / "data/peer-review.json").read_text(encoding="utf-8"))
    total, counted, additional = check_peer_review(reviews, pages[ROOT / "index.html"], pages[ROOT / "about/index.html"])
    print(f"PASS: {len(pages)} pages; {links_checked} local links and anchors; metadata and navigation.")
    print(f"PASS: {len(works)} unique works; years {dict(sorted(years.items(), reverse=True))}; complete ordered authors, DOI versions, filters, homepage metrics and BibTeX.")
    print(f"PASS: {total} manuscript reviews across {counted} counted journals; {additional} additional journals excluded from totals; homepage/About metrics, complete table counts and dates.")


if __name__ == "__main__":
    main()
