# Clemente García-Hidalgo · Personal website

Academic website in English at [torkitor.github.io](https://torkitor.github.io/).
Static HTML and CSS, with optional JavaScript bibliography filters. The complete
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
- `data/peer-review.json`: journal-level reviewing counts and their source dates.
- `build_site.py`: home-page content, publication rendering, BibTeX generation
  and the generated peer-review section on About.
- `index.html`, `publications/index.html`, `publications/publications.bib`:
  generated outputs. Edit their sources above and rebuild.
- `about/index.html`: education, professional service and distinctions. Keep the
  peer-review block's generation markers intact; edit its data and rebuild.
- `software/index.html`: public research projects.
- `assets/style.css`: shared layout and responsive styles.
- `assets/publications.js`: search, year, topic and first-author filters.
- `assets/portrait.jpg`: portrait supplied by the author.

The generated pages share navigation in `build_site.py`. About and Software
retain their own navigation and footer; update those too if the site structure
changes.

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

## Maintain the reviewing record

`data/peer-review.json` records counts supplied by the author from the Springer
Nature reviewer dashboard. The 12 November 2026 snapshot contains 127 reviewed
manuscripts across 29 journals. Each journal's `updated` date records the source's
last update, not the date on which all of its reviews took place.

Keep unquantified service in `additional_journals`. JMIR, Insights into Imaging
and European Radiology Experimental are listed there because their counts were
not supplied; they are excluded from the 127-manuscript total. The record is
author-provided, and the underlying review certificates have not been
independently verified. Do not infer review rounds, acceptance decisions or
additional totals from these data. Rebuild after changing the record; the
About section is generated between its existing HTML markers.

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

The checker derives counts from the data, so new works do not require changing
fixed totals in the validation script. It verifies consistency, not the truth of
external sources. Check those sources when editing facts. Before publishing,
preview desktop and mobile layouts and exercise search, combined filters,
reset, no-results and keyboard navigation. The static checker does not execute
JavaScript or test remote-server availability.

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
- Peer-review counts and additional reviewing service were supplied by the
  author on 12 November 2026; provenance is retained in `data/peer-review.json`.
- Public repository READMEs linked from the Software page.

The current editorial design takes inspiration from the
[Inspora website gallery](https://www.inspora.design/websites), including the
Brikken + Co reference viewed there. The first layout was inspired by
[Swann Bessa's academic website](https://swannbessa.github.io/). The implementation
and personal content were prepared independently. No institutional logos,
unpublished manuscripts or private repository contents are included.
