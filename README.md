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

## Deployment

GitHub Pages, custom domain in `CNAME`.
