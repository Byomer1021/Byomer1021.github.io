# omercanatli.com

Personal portfolio of Ömer Can Atlı — Computer Engineering at Gebze Technical
University. Backend, AI, web and mobile.

Kişisel portfolyo sitesi. Türkçe için sağ üstteki **TR** anahtarına bas.

## What is here

| Page | Contents |
|---|---|
| `index.html` | About: profile, education, languages, technical skills, work experience |
| `projects.html` | Four open-source projects, their figures and measurements, and the products |
| `architecture.html` | Pipeline diagrams and the code at the decisions that mattered |
| `cv.html` | Full CV, printable to PDF |
| `contact.html` | Contact details behind a small interactive shell |

## Running it

A static site with no build step — open `index.html`, or serve the folder:

```bash
python -m http.server 4173
```

Tailwind comes from a CDN and the design tokens live in `assets/js/tw-config.js`.
Both languages sit in the markup as `[data-lang]` elements and CSS hides the
inactive one, so the page is readable before any script runs.

## Deployment

GitHub Pages, custom domain in `CNAME`.
