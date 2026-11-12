"""Render the home page, complete bibliography and BibTeX from curated public data."""
import json
import re
from collections import Counter
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'data/publications.json').read_text(encoding='utf-8'))
REVIEWS = json.loads((ROOT / 'data/peer-review.json').read_text(encoding='utf-8'))
REVIEW_TOTAL = sum(journal['manuscripts'] for journal in REVIEWS['journals'])
REVIEW_JOURNALS = len(REVIEWS['journals'])
REVIEW_DATE = date.fromisoformat(max(journal['updated'] for journal in REVIEWS['journals']))
WORKS = sorted(DATA['works'], key=lambda w: (w['year'], w['sort_date'], w['doi']), reverse=True)
YEAR = int(DATA['updated'][:4])
UPDATED = date.fromisoformat(DATA['updated'])
UPDATED_LABEL = f'{UPDATED.day} {UPDATED:%B %Y}'
COUNTS = Counter(w['year'] for w in WORKS)
FIRST = sum(w['first_author'] for w in WORKS)
SOLE = sum(w['sole_author'] for w in WORKS)
KINDS = {'journal_article': 'Article', 'letter': 'Letter', 'perspective': 'Perspective',
         'opinion': 'Opinion', 'review': 'Review', 'case_report': 'Case report'}


def e(value):
    return escape(str(value), quote=True)


def page(title, description, body, active):
    prefix = '' if active == 'Home' else '../'
    path = '' if active == 'Home' else 'publications/'
    navigation = ''.join(
        f'<a href="{prefix}{target}"' + (' aria-current="page"' if label == active else '') + f'>{label}</a>'
        for label, target in [('Home', './'), ('Publications', 'publications/'), ('Software', 'software/'), ('About', 'about/')])
    script = '<script src="../assets/publications.js?v=20261112-r2" defer></script>' if active == 'Publications' else ''
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(description)}">
  <title>{e(title)} · Clemente García-Hidalgo</title>
  <link rel="canonical" href="https://torkitor.github.io/{path}">
  <meta property="og:title" content="{e(title)} · Clemente García-Hidalgo">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://torkitor.github.io/{path}">
  <meta property="og:image" content="https://torkitor.github.io/assets/portrait.jpg?v=20261112-r2">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}assets/style.css?v=20261112-r2">
{script}
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="page">
    <header class="site-header"><a class="wordmark" href="{prefix}./" aria-label="Clemente García-Hidalgo, home">CGH /</a><nav aria-label="Main navigation">{navigation}</nav></header>
    <main id="main">{body}</main>
    <footer class="site-footer"><span>© {YEAR} Clemente García-Hidalgo</span><a href="https://github.com/torkitor">GitHub ↗</a></footer>
  </div>
</body>
</html>
'''


def authors(work):
    return ', '.join(f'<strong>{e(a["name"])}</strong>' if a['self'] else e(a['name']) for a in work['authors'])


def citation_details(work):
    value = str(work.get('citation_year', work['year']))
    if work.get('volume'):
        value += '; ' + str(work['volume'])
    if work.get('issue'):
        value += '(' + str(work['issue']) + ')'
    if work.get('pages'):
        value += ': ' + str(work['pages'])
    return value


def publication(work, number):
    badge = 'Sole author' if work['sole_author'] else 'First author' if work['first_author'] else ''
    badge_html = f'<span class="badge">{badge}</span>' if badge else ''
    pmid = f'<a href="https://pubmed.ncbi.nlm.nih.gov/{e(work["pmid"])}/">PubMed ↗</a>' if work.get('pmid') else ''
    translations = ''.join(f'<a href="https://doi.org/{e(doi)}">Spanish edition ↗</a>' for doi in work['doi_aliases'])
    topics = ''.join(f'<span class="topic">{e(topic)}</span>' for topic in work['topics'])
    note = f'<p class="source-note">{e(work["note"])}</p>' if work.get('note') else ''
    return f'''<article class="publication" data-publication data-year="{work['year']}" data-doi="{e(work['doi'])}" data-topics="{e('|'.join(work['topics']))}" data-first="{str(work['first_author']).lower()}" id="paper-{number}">
      <span class="pub-number" aria-hidden="true">{number:02d}</span>
      <div><div class="pub-topline"><span class="venue">{e(work['journal'])}</span>{badge_html}<span class="pub-kind">{KINDS[work['category']]}</span></div>
        <h3><a href="https://doi.org/{e(work['doi'])}">{e(work['title'].rstrip('.'))}</a></h3>
        <p class="authors">{authors(work)}</p>
        <div class="pub-details"><span>{e(citation_details(work))}</span>{topics}</div>
        <div class="links-row"><a href="https://doi.org/{e(work['doi'])}">DOI ↗</a>{pmid}{translations}</div>{note}
      </div>
    </article>'''


def catalogue():
    years = ''.join(f'<option value="{year}">{year} ({COUNTS[year]})</option>' for year in sorted(COUNTS, reverse=True))
    topics = ''.join(f'<option value="{e(topic)}">{e(topic)}</option>' for topic in sorted({t for w in WORKS for t in w['topics']}))
    groups = []
    for year in sorted(COUNTS, reverse=True):
        items = '\n'.join(publication(w, len(WORKS) - i) for i, w in enumerate(WORKS) if w['year'] == year)
        label = 'publication' if COUNTS[year] == 1 else 'publications'
        groups.append(f'<section class="year-group" id="year-{year}" aria-labelledby="heading-{year}"><h2 id="heading-{year}">{year} <span>{COUNTS[year]} {label}</span></h2>{items}</section>')
    return f'''
      <div class="publication-heading"><div><p class="eyebrow">Research record / {min(COUNTS)}–{max(COUNTS)}</p><h1>Publications</h1><p class="subtitle">Neuroimaging, rigorous methods and medical AI.</p></div><div class="publication-total"><span class="total-mark">{len(WORKS)}</span><span class="total-caption">journal publications</span></div></div>
      <p class="catalogue-summary"><strong>{FIRST} first-author publications</strong>, including <strong>{SOLE} sole-author works</strong>. {COUNTS[YEAR]} publications in {YEAR}, across research articles, methodological contributions, perspectives and correspondence.</p>
      <div class="links-row"><a href="publications.bib" download>Download BibTeX ↓</a><a href="https://orcid.org/0009-0001-6672-2714">ORCID ↗</a><a href="https://pubmed.ncbi.nlm.nih.gov/?term=Garcia-Hidalgo+C%5BAuthor%5D">PubMed ↗</a></div>
      <form id="publication-filters" class="filter-panel" aria-label="Filter publications" hidden>
        <div class="filter-grid">
          <div class="filter-field"><label for="publication-search">SEARCH THE BIBLIOGRAPHY</label><input id="publication-search" name="search" type="search" placeholder="Title, author, journal or DOI" autocomplete="off"></div>
          <div class="filter-field"><label for="publication-year">YEAR</label><select id="publication-year" name="year"><option value="">All years</option>{years}</select></div>
          <div class="filter-field"><label for="publication-topic">RESEARCH AREA</label><select id="publication-topic" name="topic"><option value="">All areas</option>{topics}</select></div>
        </div>
        <div class="filter-bottom"><label class="check-label" for="first-author"><input type="checkbox" id="first-author" name="first">First author, including sole author</label><button class="reset" id="reset-filters" type="button">Reset filters</button></div>
      </form>
      <div class="results-row"><span id="result-count" role="status" aria-live="polite" aria-atomic="true">{len(WORKS)} publications</span><span>Newest first · name in bold</span></div>
      <p class="no-results" id="no-results" hidden>No publications match these filters. Try a broader search or reset the filters.</p>
      {''.join(groups)}
      <section aria-labelledby="record-note"><h2 id="record-note">About this record</h2><p class="source-note">Reconciled with publisher records, PubMed, Crossref, ORCID and LinkedIn on {UPDATED_LABEL}. Journal articles, letters, perspectives, opinion pieces, reviews and case reports are identified separately. Translated editions count as one work; year groups use the earliest evidenced publication year, including online-first publication. First authorship means first position in the author list; sole-author works are included in that total. Conference abstracts, repository deposits and unpublished manuscripts are outside these counts.</p></section>
    '''


def home():
    selected = [('10.1016/j.ejrad.2026.113218', 'Quantitative neuroimaging'),
                ('10.1007/s00330-026-12932-7', 'Radiomics & analytical validity'),
                ('10.1007/s10278-026-02421-0', 'Synthetic data & privacy'),
                ('10.2196/106199', 'Medical AI & psychometrics')]
    entries = []
    for doi, label in selected:
        work = next(w for w in WORKS if w['doi'] == doi)
        entries.append(f'<article class="entry"><p class="eyebrow">{e(label)} · {work["year"]}</p><h3><a href="https://doi.org/{e(doi)}">{e(work["title"].rstrip("."))}</a></h3><p class="meta">{e(work["journal"])} · {"Sole author" if work["sole_author"] else "First author"}</p></article>')
    metrics = ''.join(f'<div class="metric" data-metric="{key}"><strong>{value}</strong><span>{label}</span><small>{note}</small></div>' for key, value, label, note in [
        ('publications', len(WORKS), 'Journal publications', f'{min(COUNTS)}–{max(COUNTS)}'),
        ('recent', COUNTS[YEAR], f'Published in {YEAR}', f'Through {UPDATED.day} {UPDATED:%B}'),
        ('first', FIRST, 'First-author works', 'Including sole authorship'),
        ('sole', SOLE, 'Sole-author works', '')])
    additional = ', '.join(e(name) for name in REVIEWS['additional_journals'][:-1]) + ' and ' + e(REVIEWS['additional_journals'][-1])
    return f'''
      <div class="hero">
        <div class="hero-copy">
          <p class="eyebrow">MD, MSc · PhD candidate</p>
          <h1>Clemente<br>García-Hidalgo</h1>
          <p class="subtitle">Physician &amp; bioinformatician.</p>
          <p class="lead">I work on quantitative MRI of brain tumours and the methods used to evaluate medical AI.</p>
          <p class="affiliation">Radiology resident at Hospital Morales Meseguer, Murcia.<br>Doctoral research at the University of Murcia and IDIBELL–Bellvitge. MSc in Bioinformatics, UNIR.</p>
          <div class="hero-actions"><a class="button" href="publications/">Publications <span aria-hidden="true">↗</span></a><a href="about/">Academic profile <span aria-hidden="true">↗</span></a></div>
          <div class="links-row" aria-label="Professional profiles and contact"><a href="https://orcid.org/0009-0001-6672-2714">ORCID</a><a href="https://github.com/torkitor">GitHub</a><a href="https://www.linkedin.com/in/clementegarciahidalgo/">LinkedIn</a><a href="mailto:clemente292@gmail.com">Email</a></div>
        </div>
        <figure><img class="portrait" src="assets/portrait.jpg?v=20261112-r2" width="1280" height="853" fetchpriority="high" alt="Clemente García-Hidalgo"><figcaption>Murcia / Barcelona, Spain</figcaption></figure>
      </div>
      <div class="metrics" aria-label="Publication record">{metrics}</div>
      <p class="metrics-note">Journal publications through {UPDATED_LABEL}, including letters and perspectives. <a href="publications/#record-note">Counting method</a></p>
      <section aria-labelledby="selected-heading"><div class="section-heading"><h2 id="selected-heading">Selected publications</h2><a href="publications/">All {len(WORKS)} publications →</a></div>{''.join(entries)}</section>
      <section class="review-feature" id="peer-review" aria-labelledby="review-heading">
        <div class="review-number"><strong data-review-total>{REVIEW_TOTAL}</strong><small>manuscript reviews</small></div>
        <div class="review-copy"><h2 id="review-heading">Peer review</h2><p>Recorded across <span data-review-journals>{REVIEW_JOURNALS}</span> Springer Nature journals, including <em>BMC Medical Imaging</em>, <em>Scientific Reports</em> and <em>npj Digital Medicine</em>.</p><p>I also review for {additional}.</p><a class="text-link" href="about/#peer-review">View the journal record ↗</a><p class="source-note">Springer Nature reviewer record · updates through {REVIEW_DATE.day} {REVIEW_DATE:%B %Y}. The three additional journals are outside this count.</p></div>
      </section>
      <section aria-labelledby="research-heading"><h2 id="research-heading">Research</h2><div class="research-list">
        <article><p class="research-topic-label">Neuroimaging</p><div><h3>Brain tumour imaging</h3><p>DSC perfusion MRI, vascular and metabolic measurements, and exploratory radiogenomics. My doctoral work examines imaging biomarkers in gliomas and other adult brain tumours.</p></div></article>
        <article><p class="research-topic-label">Methods</p><div><h3>How analysis changes the evidence</h3><p>Analytical leakage, feature selection, model multiplicity, synthetic data and foundation-model representations. I study how these choices affect reported performance and biological interpretation.</p></div></article>
        <article><p class="research-topic-label">Software &amp; education</p><div><h3>Tools, reporting and assessment</h3><p>Image-processing checks, radiograph de-identification, clinical software verification and the evaluation of language models in medical examinations.</p><a class="text-link" href="software/">Public software ↗</a></div></article>
      </div></section>
      <div class="recognition-strip" aria-label="Selected recognition"><article><strong><a href="https://idi.gencat.cat/ca/actualitat/2026/esnr-premia-recerca-tumors-cerebrals">ESNR Scientific Award</a></strong><span>European Society of Neuroradiology · 2026</span></article><article><strong><a href="https://journals.myesr.org/eur-radiol/news/new-year-new-fellows-welcome-the-recipients-of-yves-menu-review-fellowships-2026/">Yves Menu Review Fellow</a></strong><span>European Radiology · 2026</span></article><article><strong><a href="https://radiologyai.substack.com/p/welcome-to-our-newest-trainee-editorial">Trainee Editorial Board</a></strong><span>Radiology: Artificial Intelligence · 2026–2028</span></article></div>
      <section aria-labelledby="news-heading"><h2 id="news-heading">Recent highlights</h2><ul class="news"><li><time datetime="2026-10">Oct 2026</time><span>IDI highlights our <a href="https://idi.gencat.cat/ca/actualitat/2026/esnr-premia-recerca-tumors-cerebrals">ESNR Scientific Award 2026</a> for work on DSC perfusion biomarkers in adult brain tumours.</span></li><li><time datetime="2026-10-29">29 Oct 2026</time><span>New in <a href="https://mededu.jmir.org/2026/1/e106199">JMIR Medical Education</a>: construct validity of frontier language models across four Spanish health professions examinations.</span></li><li><time datetime="2026">2026</time><span>Winner of the <a href="https://iabiomed.org/hackathon-2026/">IABiomed Treelogic challenge</a> on visual de-identification of medical images. <a href="software/">Explore DeID-Rx →</a></span></li><li><time datetime="2026-01">Jan 2026</time><span>Began serving as <a href="https://cbseram.com/2026/01/30/editorial-enero-2026/">General Coordinator of Club Bibliográfico SERAM</a>.</span></li></ul></section>
      <section class="contact" aria-labelledby="contact-heading"><h2 id="contact-heading">Contact</h2><p><a href="mailto:clemente292@gmail.com">clemente292@gmail.com</a></p><p>For research collaborations and scientific correspondence.</p></section>
    '''


def peer_review():
    rows = []
    for journal in sorted(REVIEWS['journals'], key=lambda j: (-j['manuscripts'], j['name'].lower())):
        stamp = date.fromisoformat(journal['updated'])
        rows.append(f'<tr data-review-journal="{e(journal["name"])}"><th scope="row">{e(journal["name"])}</th><td class="review-count">{journal["manuscripts"]}</td><td><time datetime="{stamp.isoformat()}">{stamp.day} {stamp:%b %Y}</time></td></tr>')
    additional = ', '.join(f'<em>{e(name)}</em>' for name in REVIEWS['additional_journals'])
    return f'''<!-- PEER REVIEW START -->
      <section id="peer-review" aria-labelledby="peer-review-heading">
        <h2 id="peer-review-heading">Peer review</h2>
        <p class="review-summary"><strong data-review-total>{REVIEW_TOTAL}</strong> manuscript reviews recorded across <span data-review-journals>{REVIEW_JOURNALS}</span> Springer Nature journals.</p>
        <p>My reviewing activity spans medical imaging, artificial intelligence, biomedical informatics and research methodology.</p>
        <p><strong>Additional reviewing:</strong> {additional}. These journals are not included in the total above.</p>
        <details class="archive"><summary>Journal-by-journal record · {REVIEW_JOURNALS} journals</summary>
          <div class="review-table-wrap"><table class="review-table"><caption>Springer Nature reviewer record · manuscript counts</caption><thead><tr><th scope="col">Journal</th><th scope="col">Count</th><th scope="col">Record updated</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
        </details>
        <p class="source-note">Counts transcribed from my Springer Nature reviewer dashboard. Journal records carry individual update dates, most recently {REVIEW_DATE.day} {REVIEW_DATE:%B %Y}.</p>
      </section>
      <!-- PEER REVIEW END -->'''


def bibtex_value(value):
    return str(value).replace('\\', r'\textbackslash{}').replace('&', r'\&').replace('%', r'\%').replace('_', r'\_').replace('#', r'\#')


def bibliography():
    entries = []
    for w in WORKS:
        fields = {'author': ' and '.join(a['family'] + ', ' + a['given'] for a in w['authors']),
                  'title': '{' + w['title'].rstrip('.') + '}', 'journal': w['journal'], 'year': w.get('citation_year', w['year']),
                  'volume': w.get('volume'), 'number': w.get('issue'), 'pages': w.get('pages'),
                  'doi': w['doi'], 'url': 'https://doi.org/' + w['doi']}
        if w.get('note'):
            fields['note'] = w['note']
        key = 'cgh' + str(w['year']) + '_' + re.sub(r'[^a-z0-9]+', '_', w['doi'].lower())
        content = ',\n'.join(f'  {k} = {{{bibtex_value(v)}}}' for k, v in fields.items() if v)
        entries.append(f'@article{{{key},\n{content}\n}}')
    return '% UTF-8 bibliography; translated editions grouped as one work.\n\n' + '\n\n'.join(entries) + '\n'


if __name__ == '__main__':
    about_path = ROOT / 'about/index.html'
    about = about_path.read_text(encoding='utf-8')
    start, end = '<!-- PEER REVIEW START -->', '<!-- PEER REVIEW END -->'
    assert about.count(start) == about.count(end) == 1, 'Expected one peer-review section in About'
    before, remaining = about.split(start, 1)
    _, after = remaining.split(end, 1)
    about_path.write_text(before + peer_review() + after, encoding='utf-8')
    (ROOT / 'index.html').write_text(page('Neuroimaging & medical AI',
        f'Clemente García-Hidalgo, MD, MSc. Physician and researcher in neuroimaging, machine learning and biostatistics. {len(WORKS)} journal publications; {FIRST} first-author works.', home(), 'Home'), encoding='utf-8')
    (ROOT / 'publications/index.html').write_text(page('Publications',
        f'{len(WORKS)} journal publications by Clemente García-Hidalgo, including {FIRST} first-author and {SOLE} sole-author works. Search the complete bibliography and download BibTeX.', catalogue(), 'Publications'), encoding='utf-8')
    (ROOT / 'publications/publications.bib').write_text(bibliography(), encoding='utf-8')
    print(f'Built home, {len(WORKS)}-work catalogue and BibTeX bibliography.')
