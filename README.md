# Clemente García-Hidalgo · Personal website

Academic website in English, published at https://torkitor.github.io/.
Plain HTML and CSS: no build step, JavaScript, analytics or package dependencies.

## Edit

- `index.html`: introduction, research interests and recent highlights.
- `publications/index.html`: selected publications and DOI links.
- `software/index.html`: public research projects.
- `about/index.html`: academic profile and editorial service.
- `assets/style.css`: typography, colours and responsive layout.
- `assets/portrait.jpg`: professional portrait.

The navigation and footer are repeated in four HTML files; update all four when changing them.

## Preview and check

```sh
python check_site.py
python -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/. The static check validates local links, anchors, basic metadata and image alternatives; it does not check remote servers.

## GitHub Pages

Publish the `main` branch from `/ (root)` in repository Settings → Pages.
The `.nojekyll` file keeps the source buildless.
See [GitHub's instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

## Content provenance

Professional details and publication records checked on 11–12 November 2026:

- [GitHub profile](https://github.com/torkitor) and [ORCID](https://orcid.org/0009-0001-6672-2714).
- [Bellvitge institutional news: ESNR award and doctoral research](https://bellvitgehospital.cat/es/actualidad/noticia/la-esnr-premia-una-investigacion-sobre-tumores-cerebrales-dirigida-por-el-equipo).
- [Radiology: AI editorial board announcement](https://radiologyai.substack.com/p/welcome-to-our-newest-trainee-editorial).
- [European Radiology 2026 fellows](https://journals.myesr.org/eur-radiol/news/new-year-new-fellows-welcome-the-recipients-of-yves-menu-review-fellowships-2026/): professional headshot, identified by the adjacent biography. Image source: https://journals.myesr.org/eur-radiol/wp-content/uploads/sites/2/migrated/2025/12/Garcia-Hidalgo-1-300x300.jpg. Photograph retains its existing rights; replace it with a preferred authorised portrait when appropriate.
- Publisher and PubMed records linked alongside each selected publication.
- Public repository READMEs linked from the Software page.

The layout is inspired by [Swann Bessa's academic website](https://swannbessa.github.io/); this site uses original HTML/CSS and independently sourced personal content. No institutional logos, unpublished manuscripts or private repository contents are included.
