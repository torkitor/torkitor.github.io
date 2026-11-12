"""Render the home page, complete bibliography and BibTeX from curated public data."""
import json
import re
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'data/publications.json').read_text(encoding='utf-8'))
REVIEWS = json.loads((ROOT / 'data/peer-review.json').read_text(encoding='utf-8'))
WORKS = sorted(DATA['works'], key=lambda w: (w['year'], w['sort_date'], w['doi']), reverse=True)
YEAR = int(DATA['updated'][:4])
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
    script = '<script src="../assets/publications.js?v=20261112-r3" defer></script>' if active == 'Publications' else '<link rel="stylesheet" href="assets/knowledge-cloud.css?v=20261112-r3"><script src="assets/knowledge-cloud.js?v=20261112-r3" defer></script>'
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
  <meta property="og:image" content="https://torkitor.github.io/assets/portrait.jpg?v=20261112-r3">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}assets/style.css?v=20261112-r3">
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
        ('publications', len(WORKS), 'Journal publications', ''),
        ('first', FIRST, 'First-author works', 'Including sole authorship'),
        ('sole', SOLE, 'Sole-author works', '')])
    return f'''
      <div class="hero">
        <div class="hero-copy">
          <p class="eyebrow">MD, MSc · PhD candidate</p>
          <h1>Clemente<br>García-Hidalgo</h1>
          <p class="subtitle">Radiology, Medical Imaging and AI</p>
          <p class="affiliation">Radiology resident at Hospital Morales Meseguer, Murcia.<br>Doctoral research at the University of Murcia and IDIBELL–Bellvitge. MSc in Bioinformatics.</p>
          <div class="hero-actions"><a class="button" href="publications/">Publications <span aria-hidden="true">↗</span></a><a href="about/">Academic profile <span aria-hidden="true">↗</span></a></div>
          <div class="links-row" aria-label="Professional profiles and contact"><a href="https://orcid.org/0009-0001-6672-2714">ORCID</a><a href="https://github.com/torkitor">GitHub</a><a href="https://www.linkedin.com/in/clementegarciahidalgo/">LinkedIn</a><a href="mailto:clemente292@gmail.com">Email</a></div>
        </div>
        <figure><img class="portrait" src="assets/portrait.jpg?v=20261112-r3" width="1280" height="853" fetchpriority="high" alt="Clemente García-Hidalgo"></figure>
      </div>

      <div class="metrics" aria-label="Publication record">{metrics}</div>
      {highlights()}
      {peer_review(compact=True)}
      <section id="knowledge-map" aria-labelledby="knowledge-heading">
        <div class="section-heading"><h2 id="knowledge-heading">Research fields</h2></div>
        <div class="knowledge-stage" hidden><canvas id="knowledge-canvas" tabindex="0" role="img" aria-label="Interactive three-dimensional map of six research fields" aria-describedby="knowledge-help"></canvas><div class="knowledge-toolbar"><p id="knowledge-help">Drag horizontally to rotate. Arrow keys also move the view.</p><button id="knowledge-pause" type="button">Pause rotation</button></div></div>
        <div class="knowledge-fields" role="group" aria-label="Choose a research field" hidden><button type="button" data-field="mri">Quantitative MRI</button><button type="button" data-field="oncology">Neuro-oncology</button><button type="button" data-field="radiomics">Radiomics</button><button type="button" data-field="ai">Medical AI</button><button type="button" data-field="statistics">Biostatistics</button><button type="button" data-field="software">Research software</button></div>
        <div class="knowledge-selection" hidden><div id="knowledge-detail" aria-live="polite" aria-atomic="true"><h3>Quantitative MRI</h3><p>Perfusion imaging and the interpretation of vascular and metabolic biomarkers in brain tumours.</p></div><a id="knowledge-link" href="publications/?topic=Neuroimaging">Explore related publications</a></div>
        <div class="knowledge-fallback"><p>My work connects quantitative MRI and neuro-oncology with radiomics, medical AI, biostatistics and research software.</p><div class="links-row"><a href="publications/?topic=Neuroimaging">MRI &amp; neuro-oncology</a><a href="publications/?topic=Radiomics%20%26%20methods">Radiomics &amp; biostatistics</a><a href="publications/?topic=Medical%20AI">Medical AI</a><a href="software/">Research software</a></div></div>
      </section>
      <section aria-labelledby="selected-heading"><div class="section-heading"><h2 id="selected-heading">Selected publications</h2><a href="publications/">All {len(WORKS)} publications →</a></div>{''.join(entries)}</section>
      <section class="contact" aria-labelledby="contact-heading"><h2 id="contact-heading">Contact</h2><p><a href="mailto:clemente292@gmail.com">clemente292@gmail.com</a></p><p>For research collaborations and scientific correspondence.</p></section>
    '''


def highlights():
    data = json.loads((ROOT / 'data/highlights.json').read_text(encoding='utf-8'))
    features = []
    for item in data['features']:
        photo = ''
        if item.get('image'):
            photo = f'<figure><img src="{e(item["image"])}" width="{item["width"]}" height="{item["height"]}" loading="lazy" alt="{e(item["alt"])}"><figcaption>{e(item["credit"])}</figcaption></figure>'
        secondary = f'<a class="text-link" href="{e(item["secondary_url"])}">{e(item["secondary_label"])} ↗</a>' if item.get('secondary_url') else ''
        features.append(f'<article class="press-feature">{photo}<p class="eyebrow">{e(item["label"])}</p><h3><a href="{e(item["url"])}">{e(item["title"])}</a></h3><p>{e(item["text"])}</p><p class="meta">{e(item["source"])} · {e(item["date"])}</p><div class="press-links"><a class="text-link" href="{e(item["url"])}">Read the coverage ↗</a>{secondary}</div></article>')
    awards = ''.join(f'<li><h3><a href="{e(item["url"])}">{e(item["title"])}</a></h3><p>{e(item["detail"])}</p></li>' for item in data['recognition'])
    return f'''<section id="awards-news" aria-labelledby="awards-news-heading"><div class="section-heading"><h2 id="awards-news-heading">Awards &amp; in the news</h2><a href="about/#recognition">Full recognition history ↗</a></div><div class="press-grid">{''.join(features)}</div><ul class="award-list">{awards}</ul></section>'''


def peer_review(compact=False):
    entries = []
    for journal in REVIEWS['journals']:
        if journal['featured']:
            name = f'<a href="{e(journal["url"])}">{e(journal["name"])}</a>' if journal.get('url') else e(journal['name'])
            entries.append(f'<article data-review-journal="{e(journal["name"])}"><h3>{name}</h3><p class="journal-role">{e(journal["role"])}</p></article>')
    others = '<a class="text-link" href="about/#peer-review">More editorial and reviewing service ↗</a>' if compact else ''
    if not compact:
        names = ''.join(f'<li data-review-journal="{e(j["name"])}">{e(j["name"])}</li>' for j in REVIEWS['journals'] if not j['featured'])
        others = f'<details class="archive"><summary>Other journals reviewed</summary><ul class="journal-list">{names}</ul></details>'
    section_class = 'editorial-feature' if compact else 'editorial-profile'
    content = f'''<section class="{section_class}" id="peer-review" aria-labelledby="peer-review-heading"><h2 id="peer-review-heading">Editorial work &amp; peer review</h2><div class="journal-grid">{''.join(entries)}</div>{others}</section>'''
    return content if compact else '<!-- PEER REVIEW START -->\n      ' + content + '\n      <!-- PEER REVIEW END -->'


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
    (ROOT / 'index.html').write_text(page('Radiology, Medical Imaging and AI',
        f'Clemente García-Hidalgo, MD, MSc. Radiology, medical imaging and AI. {len(WORKS)} journal publications; {FIRST} first-author works.', home(), 'Home'), encoding='utf-8')
    (ROOT / 'publications/index.html').write_text(page('Publications',
        f'{len(WORKS)} journal publications by Clemente García-Hidalgo, including {FIRST} first-author and {SOLE} sole-author works. Search the complete bibliography and download BibTeX.', catalogue(), 'Publications'), encoding='utf-8')
    (ROOT / 'publications/publications.bib').write_text(bibliography(), encoding='utf-8')
    print(f'Built home, {len(WORKS)}-work catalogue and BibTeX bibliography.')
