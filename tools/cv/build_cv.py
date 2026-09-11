"""Render the CV to HTML, then to PDF with headless Chrome.

Two versions from one content file:

    omer-can-atli-cv.pdf         two pages, the full record
    omer-can-atli-cv-1page.pdf   one page, for applications that ask for one

Single column on purpose: applicant tracking systems parse multi-column CVs
badly, and the text has to survive being read by a machine before a person ever
sees the layout. Chrome's print-to-pdf keeps the text selectable, so it does.

    python tools/cv/build_cv.py

Needs the local server running (python -m http.server 4173) only if you want to
preview the HTML; the PDF step loads the file directly.
"""

import html
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cv_content as C  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "assets" / "cv"
BUILD = pathlib.Path(__file__).resolve().parent / "build"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser",
]

CSS_TEMPLATE = """
@page { size: A4; margin: @PAGE_MARGIN@; }
* { box-sizing: border-box; }
body {
  margin: 0; font-family: "Inter", "Segoe UI", Arial, sans-serif;
  font-size: @BASE@pt; line-height: @LH@; color: #1a1a1a; background: #fff;
}
/* Links stay black and are marked by a hairline underline instead of a colour,
   so the page prints the same in mono and still reads as clickable. */
a { color: inherit; text-decoration: underline; text-decoration-thickness: 0.4pt;
    text-underline-offset: 1.6pt; }
h1 { font-size: 21pt; margin: 0 0 1mm; letter-spacing: -0.4pt; font-weight: 700; }
.title { font-size: 10pt; color: #444; margin: 0 0 2.4mm; }
/* Flex-wrap, not inline text: joining the items with a separator element and
   no whitespace leaves the browser no break opportunity, so the line runs off
   the page instead of wrapping. */
.contact {
  font-size: 8.4pt; color: #333; margin: 0;
  display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 0; row-gap: 0.6mm;
}
.contact > span { white-space: nowrap; }
.sep { color: #aaa; padding: 0 1.7mm; }
hr { border: 0; border-top: 0.7pt solid #222; margin: 3.2mm 0 2.6mm; }
h2 {
  font-size: 9pt; text-transform: uppercase; letter-spacing: 1.1pt;
  margin: @H2TOP@mm 0 1.6mm; padding-bottom: 0.7mm; font-weight: 700;
  border-bottom: 0.5pt solid #bbb;
}
h2:first-of-type { margin-top: 0; }
.entry { margin-bottom: @ENTRYGAP@mm; page-break-inside: avoid; }
.entry-head { display: flex; justify-content: space-between; gap: 6mm; align-items: baseline; }
.entry-name { font-weight: 700; font-size: 10pt; }
.entry-meta { font-size: 8.6pt; color: #555; white-space: nowrap; }
.entry-sub { font-size: 9pt; color: #333; margin-top: 0.3mm; font-style: italic; }
ul { margin: 1.1mm 0 0; padding-left: 4.4mm; }
li { margin-bottom: 0.7mm; }
.stack { font-size: 8.4pt; color: #555; margin-top: 1.0mm; }
.skills-row { display: flex; gap: 3mm; margin-bottom: 1.1mm; }
.skills-key { font-weight: 700; min-width: 34mm; }
.inline-list { color: #222; }
.summary { margin: 0 0 1mm; text-align: justify; }
"""


def css(short):
    values = {
        "@PAGE_MARGIN@": "10mm 12mm" if short else "13mm 14mm",
        "@BASE@": "8.5" if short else "9.4",
        "@LH@": "1.30" if short else "1.42",
        "@H2TOP@": "2.7" if short else "4.2",
        "@ENTRYGAP@": "1.8" if short else "2.8",
    }
    out = CSS_TEMPLATE
    for token, value in values.items():
        out = out.replace(token, value)
    return out


def esc(s):
    return html.escape(str(s), quote=False)


def contact_line():
    c = C.CONTACT
    parts = [
        f'<span><a href="https://{c["site"]}">{esc(c["site"])}</a></span>',
        f'<span><a href="mailto:{c["email"]}">{esc(c["email"])}</a></span>',
        f'<span>{esc(c["phone"])}</span>',
        f'<span>{esc(c["location"])}</span>',
        f'<span><a href="https://{c["github"]}">{esc(c["github"])}</a></span>',
        f'<span><a href="{c["linkedin_url"]}">{esc(c["linkedin"])}</a></span>',
    ]
    return '<span class="sep">·</span>'.join(parts)


def bullets(items):
    return "<ul>" + "".join(f"<li>{esc(b)}</li>" for b in items) + "</ul>"


def render(short=False):
    p = []
    p.append(f'<h1>{esc(C.CONTACT["name"])}</h1>')
    p.append(f'<p class="title">{esc(C.CONTACT["title"])}</p>')
    p.append(f'<p class="contact">{contact_line()}</p>')
    p.append("<hr/>")

    p.append(f'<p class="summary">{esc(C.SUMMARY_SHORT if short else C.SUMMARY)}</p>')

    p.append("<h2>Work Experience</h2>")
    for e in C.EXPERIENCE:
        p.append('<div class="entry">')
        p.append('<div class="entry-head">'
                 f'<span class="entry-name">{esc(e["role"])}</span>'
                 f'<span class="entry-meta">{esc(e["dates"])}</span></div>')
        p.append(f'<div class="entry-sub">{esc(e["org"])}</div>')
        p.append(bullets(e["short"] if short and e.get("short") else e["bullets"]))
        p.append("</div>")

    p.append("<h2>Products</h2>")
    for pr in C.PRODUCTS:
        p.append('<div class="entry">')
        link = ""
        if pr["link"]:
            label = esc(pr["link"])
            inner = f'<a href="{pr["url"]}">{label}</a>' if pr.get("url") else label
            link = f' <span class="entry-meta">{inner}</span>' 
        p.append('<div class="entry-head">'
                 f'<span class="entry-name">{esc(pr["name"])}{link}</span>'
                 f'<span class="entry-meta">{esc(pr["role"])}</span></div>')
        p.append(bullets(pr["short"] if short and pr.get("short") else pr["bullets"]))
        if not short:
            p.append(f'<div class="stack">{esc(pr["stack"])}</div>')
        p.append("</div>")

    p.append(f'<h2>Open-Source Projects <span style="font-weight:400;text-transform:none;'
             f'letter-spacing:0;color:#666">— <a href="https://{C.CONTACT["github"]}">'
             f'{esc(C.CONTACT["github"])}</a></span></h2>')
    for o in C.OPEN_SOURCE:
        if short and not o.get("short"):
            continue          # entry is full-CV only; see cv_content.py
        p.append('<div class="entry">')
        name = esc(o["name"])
        if o.get("url"):
            name = f'<a href="{o["url"]}">{name}</a>'
        if o.get("demo"):
            name += f' <span class="entry-meta">· <a href="{o["demo"]}">live demo</a></span>'
        p.append('<div class="entry-head">'
                 f'<span class="entry-name">{name}</span>'
                 f'<span class="entry-meta">{esc(o["stack"])}</span></div>')
        if short:
            p.append(f'<div style="margin-top:0.6mm">{esc(o["short"])}</div>')
        else:
            p.append(f'<div class="entry-sub">{esc(o["tagline"])}</div>')
            p.append(bullets(o["bullets"]))
        p.append("</div>")

    p.append("<h2>Education</h2>")
    for e in C.EDUCATION:
        p.append('<div class="entry" style="margin-bottom:1.6mm">')
        p.append('<div class="entry-head">'
                 f'<span class="entry-name">{esc(e["school"])}</span>'
                 f'<span class="entry-meta">{esc(e["dates"])} · {esc(e["where"])}</span></div>')
        p.append(f'<div class="entry-sub">{esc(e["detail"])}</div>')
        p.append("</div>")

    p.append("<h2>Technical Skills</h2>")
    for key, val in C.SKILLS:
        p.append(f'<div class="skills-row"><span class="skills-key">{esc(key)}</span>'
                 f'<span class="inline-list">{esc(val)}</span></div>')

    p.append("<h2>Languages</h2>")
    p.append(f'<div class="inline-list">{esc(C.LANGUAGES)}</div>')

    p.append("<h2>Volunteer Work &amp; Extracurriculars</h2>")
    p.append('<div class="inline-list">'
             + '<span class="sep">·</span>'.join(
                 esc(v) for v in (C.VOLUNTEER_SHORT if short else C.VOLUNTEER))
             + "</div>")

    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'/>"
        f"<title>{esc(C.CONTACT['name'])} — CV</title>"
        "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap' rel='stylesheet'/>"
        f"<style>{css(short)}</style></head><body>" + "\n".join(p) + "</body></html>"
    )


def find_chrome():
    for c in CHROME_CANDIDATES:
        if pathlib.Path(c).exists() or shutil.which(c):
            return c
    return None


def to_pdf(chrome, html_path, pdf_path):
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
        "--virtual-time-budget=8000", html_path.as_uri(),
    ], check=True, capture_output=True)


def page_count(pdf_path):
    """Number of pages in a PDF, or None if pypdf is not installed."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    return len(PdfReader(str(pdf_path)).pages)


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # (name, short, output, pages it must have)
    #
    # The one-page CV exists because some applications ask for one page; if an
    # entry pushes it onto a second, it silently stops being the thing it is
    # named after. Check rather than assume.
    jobs = [("cv-full", False, "omer-can-atli-cv.pdf", 2),
            ("cv-short", True, "omer-can-atli-cv-1page.pdf", 1)]

    chrome = find_chrome()
    if not chrome:
        print("  no Chrome found; wrote HTML only", file=sys.stderr)

    wrong = []
    for name, short, pdf_name, want_pages in jobs:
        html_path = BUILD / f"{name}.html"
        html_path.write_text(render(short=short), encoding="utf-8")
        print(f"  {html_path.relative_to(ROOT)}")
        if chrome:
            pdf_path = OUT_DIR / pdf_name
            to_pdf(chrome, html_path, pdf_path)
            got = page_count(pdf_path)
            pages = "?" if got is None else str(got)
            print(f"  {pdf_path.relative_to(ROOT)}  "
                  f"({pdf_path.stat().st_size // 1024} KB, {pages} pages)")
            if got is not None and got != want_pages:
                wrong.append(f"{pdf_name}: {got} pages, expected {want_pages}")

    if wrong:
        print(file=sys.stderr)
        for w in wrong:
            print(f"  !! {w}", file=sys.stderr)
        print("  shorten an entry, or drop one from the short CV.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
