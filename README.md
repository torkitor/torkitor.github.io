# Clemente García-Hidalgo · Personal website

Academic website in English at [torkitor.github.io](https://torkitor.github.io/).
Static HTML and CSS, with optional JavaScript filters and animation. The complete
publication list and links work without JavaScript. No package dependencies,
analytics, server-side application or external fonts are required.

## Update the site

Python 3.9 or newer is sufficient. From the repository root:

```sh
python build_site.py
python check_site.py
python -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/ to preview. Commit the generated files alongside the
source changes; GitHub Pages serves those files directly and does not run Python.

- `data/publications.json`: curated bibliography and public source URLs.
- `data/peer-review.json`: journal names, editorial or reviewing roles, and links.
- `data/highlights.json`: homepage press coverage, awards, source dates and image
  provenance.
- `data/journey.json`: career timeline, milestone text, source links and photographs.
- `build_site.py`: home-page content, career timeline, publication rendering,
  BibTeX generation and the generated journal-service section on About.
- `index.html`, `journey/index.html`, `publications/index.html`, `publications/publications.bib`:
  generated outputs. Edit their sources above and rebuild.
- `about/index.html`: education, professional service and distinctions. Keep the
  peer-review block's generation markers intact; edit its data and rebuild.
- `software/index.html`: public research projects.
- `assets/style.css`: shared layout, responsive styles and reduced-motion rules.
- `assets/publications.js`: search, year, topic and first-author filters.
- `assets/knowledge-cloud.css`, `assets/knowledge-cloud.js`: homepage knowledge
  map and its optional animation. Preserve keyboard controls, the pause button
  and the reduced-motion alternative when editing it.
- `assets/journey.css`, `assets/journey.js`: career timeline, chapter navigation
  and optional scroll reveals. Preserve readable content without JavaScript and
  when reduced motion is requested.
- `assets/portrait.jpg`: portrait supplied by the author.
- `assets/news/commurcia-interview.jpg`: photograph from the medical college's
  interview, with its source and credit recorded in `data/highlights.json`.

The generated pages share navigation in `build_site.py`. About and Software
retain their own navigation and footer; update those too if the site structure
changes.

The site has five main pages: Home, Journey, Publications, Software and About.
The checker compares their navigation, including each page's current-page link.

## Maintain the bibliography

Each work has one canonical `doi`. Put translated editions in `doi_aliases`,
rather than adding duplicate works. Preserve the complete, ordered `authors`
list, including the publisher's given/family spelling and initials when full
names are unavailable. Exactly one author has `self: true`; `first_author` and
`sole_author` must agree with that author's position and the list length.

`year` groups works by their earliest evidenced publication year. `sort_date`
retains the supported precision (`YYYY`, `YYYY-MM` or `YYYY-MM-DD`); do not invent
an exact day from month-only metadata. When the cited journal edition belongs
to a different year, add `citation_year` for the displayed citation and BibTeX.
Document online-first, issue and translated-edition distinctions in `note`.

Retain source URLs in `sources`, add a PMID only when verified, and distinguish
articles, letters, perspectives, opinion pieces, reviews and case reports using
`category`. Topic labels populate the filters automatically. Update the top-level
`updated` date when the bibliography is reconciled. Research notes, downloaded
source records and private files belong outside the public repository.

Counts represent unique journal publications, including the identified
publication types. Translations count once. Conference abstracts, repository
software/data deposits, preprints and unpublished manuscripts are excluded.
No citation-count, h-index or journal-impact metrics are inferred.

## Maintain the journal-service record

`data/peer-review.json` describes journal service without manuscript or journal
totals. Preserve each role's wording: the Yves Menu Review Fellowship at
European Radiology, the Trainee Editorial Board at Radiology: Artificial
Intelligence, and reviewer service at the other listed journals are distinct.
Fellowship participation does not imply editorial-board membership.

Roles draw on the author's supplied record and the linked institutional
announcements. The underlying review certificates have not been independently
verified. Retain the source links, update the record's date when editing it,
and rebuild. The homepage and About journal sections are generated from this
file; keep the About section's existing HTML markers intact. Do not restore
reviewing totals from earlier data or repository history.

Set `featured` for the journals highlighted on the homepage and About. Other
reviewer roles appear in About's expandable journal list. The public data store
only `name`, `role`, `url` and `featured` for each entry; use `null` when there is
no source or journal URL. A link to a journal homepage identifies the journal,
whereas an institutional announcement substantiates the stated appointment.

## Maintain news and awards

Edit `data/highlights.json` and rebuild. `features` contains press coverage and
interviews; `recognition` contains the shorter award entries. Keep the source URL
and publication date with each feature. A news article's publication date is not
necessarily the date on which its reported award was presented.

For a feature image, retain its local `image` path, dimensions, descriptive
`alt` text, displayed `credit` and original `image_source` URL. Keep institutional
announcements in the optional secondary link when they supplement press coverage.

## Maintain the career timeline

Edit `data/journey.json` and rebuild. Keep dates at the precision supported by the
source: an announcement date does not establish an award-ceremony date, and an
expected doctoral completion date does not establish a completed qualification.
The current research affiliation and degree-awarding institution serve different
purposes; preserve PhD-candidate status and the author's requested lab attribution.

Distinguish personal awards, team distinctions, editorial appointments, training
scholarships and achievements credited to a mentor. Avoid duplicating a prize
and its associated scholarship. Preserve links and image attribution with the
milestone. Full social-post archives and uncurated evidence remain outside the
public repository.

`chapters` sets the timeline order and chapter anchors. Keep each chapter's `id`
unique and stable. Its `images` and the top-level `hero_images` refer to the
`images` dictionary, which retains local paths, dimensions, alt text, captions,
credits and public source URLs. Use public post links, not account analytics or
campaign-management links. Keep the readable dates and their supported precision
in `date`; `year` and `index_label` supply the chapter navigation.

## Validation

`check_site.py` checks:

- Local links and fragments, page metadata, navigation, image descriptions and
  duplicate HTML IDs.
- Unique work and translation DOIs, date precision, provenance URLs and
  authorship flags against the ordered author lists.
- Every rendered publication, full author order, profile-author emphasis,
  publication years, DOI/PMID links, topic/year filters and home-page counts
  against the curated data.
- BibTeX entry count, unique keys/DOIs, citation years and complete author order.
- Rendered journal names and roles against their source data, with no reviewing
  counts or retired count markup.
- Career milestone order, dates and source text against the timeline data;
  chapter anchors, local photographs and displayed photo attribution.

The checker derives counts from the data, so new works do not require changing
fixed totals in the validation script. It verifies consistency, not the truth of
external sources. Check those sources when editing facts. Before publishing,
preview desktop and mobile layouts and exercise search, combined filters,
reset, no-results, reduced-motion settings and keyboard navigation. The static
checker does not execute JavaScript or test remote-server availability.

With Node.js installed, run the dependency-free interaction checks:

```sh
node test_knowledge_cloud.js
node test_journey.js
```

These check the knowledge map's geometry and controller behaviour, and the
timeline's chapter selection, reveal lifecycle, anchors and motion preferences.
Their simulated browser objects catch logic regressions; they do not establish
visual quality or real-device gesture behaviour. Keep the browser preview step.

## GitHub Pages

Publish the `main` branch from `/ (root)` in repository Settings → Pages.
`.nojekyll` keeps GitHub from processing the static files with Jekyll.
See [GitHub's publishing instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

## Content provenance

The professional profile and bibliography were reconciled on 12 November 2026
against LinkedIn, publisher records, PubMed, Crossref, ORCID and institutional
sources. Publication-level source URLs are in `data/publications.json`; direct
publisher and PubMed links appear with each citation. Professional roles and
awards are linked to their sources on the About page. Team awards retain their
team attribution. Education and current training status are distinct from
completed qualifications.

- [GitHub profile](https://github.com/torkitor),
  [ORCID](https://orcid.org/0009-0001-6672-2714) and
  [LinkedIn](https://www.linkedin.com/in/clementegarciahidalgo/).
- [Bellvitge: ESNR award and doctoral research](https://bellvitgehospital.cat/es/actualidad/noticia/la-esnr-premia-una-investigacion-sobre-tumores-cerebrales-dirigida-por-el-equipo).
- [Radiology: AI trainee editorial board announcement](https://radiologyai.substack.com/p/welcome-to-our-newest-trainee-editorial).
- [European Radiology 2026 fellows](https://journals.myesr.org/eur-radiol/news/new-year-new-fellows-welcome-the-recipients-of-yves-menu-review-fellowships-2026/):
  source for the Yves Menu Review Fellowship.
- The current portrait comes from the author's supplied 1280 × 853 photograph,
  replacing the earlier headshot sourced from the fellowship announcement.
- The interview photograph is from the
  [Colegio de Médicos de la Región de Murcia interview](https://commurcia.es/noticia?id=2235),
  published 18 May 2026. This website credits the medical college; the original
  [image URL](https://commurcia.es/Z_data/publicaciones/_dsc6266-1_2235.jpg)
  is retained in `data/highlights.json`.
- [La Vanguardia / El Llobregat coverage of the ESNR award](https://www.lavanguardia.com/elllobregat/sociedad/20261101/11673413/investigacion-dirigida-bellvitge-recibe-premio-europeo-nuevos-biomarcadores-tumores-cerebrales.html),
  published 1 November 2026, is linked alongside the IDI institutional announcement.
- Reviewing service was supplied by the author on 12 November 2026; public
  journal roles and their links are retained in `data/peer-review.json`.
- Career milestones combine the author's profile and posts, institutional
  announcements and supplied clarifications. `data/journey.json` retains the
  public links and photographic sources; source snapshots and editorial notes
  remain in the private research folder. Distinguish author-provided claims
  from independently documented institutional statements when updating them.
- Public repository READMEs linked from the Software page.

The current editorial design takes inspiration from the
[Inspora website gallery](https://www.inspora.design/websites), including the
Brikken + Co reference viewed there. The first layout was inspired by
[Swann Bessa's academic website](https://swannbessa.github.io/). The implementation
and personal content were prepared independently. No unpublished manuscripts
or private repository contents are included.
