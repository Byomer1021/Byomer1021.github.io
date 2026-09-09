# omercanatli.com

Personal portfolio of Ömer Can Atlı — Computer Engineering at Gebze Technical
University. Backend, AI, web and mobile.

Kişisel portfolyo sitesi. Türkçe için sağ üstteki **TR** anahtarına bas.

## What is here

| URL | Contents |
|---|---|
| `/` | About: profile, education, languages, technical skills, work experience |
| `/projects/` | Card grid: four open-source projects and three products |
| `/projects/<name>/` | One page per project: figures, measurements, docs and links |
| `/method/` | Four working rules and the table of measurements that changed a decision |
| `/cv/` | Full CV, downloadable as PDF |
| `/contact/` | Contact details behind a small interactive shell |

## Running it

Serve the folder — the URLs are directory-based, so opening the files directly
will not resolve the links:

```bash
python -m http.server 4173
```

## Editing it

Pages are assembled from one shared shell so the header, footer and meta block
cannot drift apart across eleven pages. Edit the body in `tools/bodies/<name>.html`,
then regenerate:

```bash
python tools/build_pages.py
```

The generated HTML is committed and GitHub Pages serves it directly, so nothing
runs on the server and the build is only needed when editing.

Tailwind comes from a CDN and the design tokens live in `assets/js/tw-config.js`.
Both languages sit in the markup as `[data-lang]` elements and CSS hides the
inactive one, so the page is readable before any script runs.

## The smart-city map

`/projects/smart-city/` carries an interactive Leaflet map built from
`assets/data/smartcity-map.json` — 258 taxi zones on their real coordinates,
the 299 heaviest flows between them, and the node-removal simulation. The data
is exported from the project's own results, not hand-written.

Tiles come from Esri's Dark Gray Canvas, which needs no API key. CARTO's dark
basemap now watermarks every tile with "API KEY REQUIRED" and OpenStreetMap's
own servers block generic clients, so neither is usable here.

## The CV

`tools/cv/cv_content.py` holds the CV once; `python tools/cv/build_cv.py`
renders it to HTML and prints two PDFs with headless Chrome:

| File | Pages | For |
|---|---|---|
| `assets/cv/omer-can-atli-cv.pdf` | 2 | the full record |
| `assets/cv/omer-can-atli-cv-1page.pdf` | 1 | applications that ask for one page |

Single column on purpose — applicant tracking systems parse multi-column CVs
badly, and print-to-pdf keeps the text selectable so they can read it at all.

## Deployment

GitHub Pages, custom domain in `CNAME`.
