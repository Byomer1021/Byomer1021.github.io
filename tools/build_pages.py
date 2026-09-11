"""Assemble the site's pages from one shared shell and per-page bodies.

The published site is still plain static HTML — nothing runs on the server, and
GitHub Pages serves the generated files directly. This exists only so the seven
pages cannot drift apart: they share a header, footer, meta block and script
tags, and hand-maintaining seven copies of that is how a nav link ends up wrong
on one page and right on the others.

    python tools/build_pages.py

Bodies live in tools/bodies/<name>.html and are written into the output path
each page declares below. A page may also carry <name>.head.html (injected into
<head>) and <name>.script.js (inlined before </body>).
"""

import pathlib
import sys

NL = chr(10)

ROOT = pathlib.Path(__file__).resolve().parent.parent
BODIES = ROOT / "tools" / "bodies"
SITE = "https://omercanatli.com"

NAV = [
    ("index", "/", "01 // ABOUT"),
    ("projects", "/projects/", "02 // PROJECTS"),
    ("method", "/method/", "03 // METHOD"),
    ("cv", "/cv/", "04 // CV"),
    ("contact", "/contact/", "05 // TERMINAL"),
]

# name, output path, nav slug to highlight, <title>, meta description
PAGES = [
    ("index", "index.html", "index",
     "Ömer Can Atlı — Computer Engineer",
     "Final-year Computer Engineering student at Gebze Technical University. Backend systems, AI pipelines, and the full-stack and mobile apps built on top of them."),
    ("method", "method/index.html", "method",
     "Method — Ömer Can Atlı",
     "Four engineering rules learned by getting a number wrong first, and the table of every measurement that changed a decision."),
    ("cv", "cv/index.html", "cv",
     "CV — Ömer Can Atlı",
     "Education, work experience, project experience and technical skills of Ömer Can Atlı."),
    ("contact", "contact/index.html", "contact",
     "Contact — Ömer Can Atlı",
     "Get in touch with Ömer Can Atlı — email, LinkedIn, GitHub and Hugging Face."),
    ("projects", "projects/index.html", "projects",
     "Projects — Ömer Can Atlı",
     "Four open-source projects with public code and measurements, and the products behind private repositories."),
    ("otonomarac", "projects/otonomarac/index.html", "projects",
     "otonomarac — Ömer Can Atlı",
     "Monocular driving perception and bird's-eye-view mapping: detection, tracking, depth, segmentation and time-to-collision, with a live demo."),
    ("trafikisaret", "projects/trafikisaret/index.html", "projects",
     "trafikisaret — Ömer Can Atlı",
     "A Turkish traffic-sign dataset labelled from scratch on own dashcam footage, and the two-stage recogniser trained on it."),
    ("smart-city", "projects/smart-city/index.html", "projects",
     "smart-city-traffic-analysis — Ömer Can Atlı",
     "38.3 million New York taxi trips modelled as a graph to find the structural bottlenecks in the city's traffic."),
    ("plakatanima", "projects/plakatanima/index.html", "projects",
     "plakatanima — Ömer Can Atlı",
     "Turkish licence plate recognition measured end to end: 18 of 34 plates read fully automatically, a constrained decoder in C++, and TensorRT FP16 on a T4."),
    ("payflow", "projects/payflow/index.html", "projects",
     "payflow — Ömer Can Atlı",
     "A programming language for subscription billing: hand-written lexer, parser, type checker and interpreter, running live in the browser."),
    ("shorties", "projects/shorties/index.html", "projects",
     "Shorties — Ömer Can Atlı",
     "An exam-preparation ecosystem of three separate apps on one shared architecture. YKS is live on the App Store and Google Play."),
    ("respos", "projects/respos/index.html", "projects",
     "respos — Ömer Can Atlı",
     "A multi-tenant SaaS point-of-sale system for restaurants: one backend, many tenants, isolated data and per-restaurant module access."),
]


# The order a visitor walks the project pages in, matching the card grid on
# /projects/. Each page's footer links to the next one and the last wraps to
# the first, so the ring is closed by construction.
#
# This used to be hand-written into every body, which meant adding a project
# required editing the one before it -- and payflow was added without that,
# so nothing linked to it. Keep this list in the grid's order and the footers
# follow.
PROJECT_RING = [
    ("otonomarac", "otonomarac"),
    ("trafikisaret", "trafikisaret"),
    ("smart-city", "smart-city"),
    ("plakatanima", "plakatanima"),
    ("payflow", "payflow"),
    ("shorties", "Shorties"),
    ("respos", "respos"),
]

NEXT_MARKER = "<!-- NEXT -->"

NEXT_NAV = """<!-- ============================ NEXT ============================ -->
<nav class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-space-md p-space-lg rounded-xl bg-surface-container-low reveal" style="border: 1px solid rgba(255,255,255,0.08);">
<a class="inline-flex items-center gap-space-2xs font-label-code-sm text-label-code-sm text-outline hover:text-primary transition-colors tracking-widest uppercase" href="/projects/">
<span class="material-symbols-outlined text-[14px]">arrow_back</span>
<span data-lang="en">ALL PROJECTS</span><span data-lang="tr">TÜM PROJELER</span>
</a>
<a class="inline-flex items-center gap-space-2xs font-label-code-sm text-label-code-sm text-primary hover:text-white transition-colors tracking-widest uppercase" href="/projects/{slug}/">
<span data-lang="en">NEXT — {label}</span><span data-lang="tr">SONRAKİ — {label}</span>
<span class="material-symbols-outlined text-[14px]">arrow_forward</span>
</a>
</nav>"""


def next_nav(name):
    """The footer nav for project page `name`, pointing at the next in the ring."""
    slugs = [s for s, _ in PROJECT_RING]
    if name not in slugs:
        return None
    slug, label = PROJECT_RING[(slugs.index(name) + 1) % len(PROJECT_RING)]
    return NEXT_NAV.format(slug=slug, label=label)


def nav_links(active, mobile=False):
    out = []
    for slug, href, label in NAV:
        if mobile:
            cls = ("px-space-sm py-space-xs rounded font-label-code-sm text-label-code-sm "
                   "tracking-wider text-on-surface-variant hover:bg-surface-container-high")
        else:
            cls = ("px-space-sm py-space-2xs rounded-full font-label-code-sm text-label-code-sm "
                   "tracking-wider text-on-surface-variant hover:text-on-surface "
                   "hover:bg-surface-container-high transition-all")
        out.append(f'<a class="{cls}" data-nav="{slug}" href="{href}">{label}</a>')
    return "\n".join(out)


SHELL = """<!DOCTYPE html>
<html class="dark" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{title}</title>
<meta name="description" content="{desc}"/>
<link href="{url}" rel="canonical"/>
<meta content="website" property="og:type"/>
<meta content="{url}" property="og:url"/>
<meta content="{title}" property="og:title"/>
<meta content="{desc}" property="og:description"/>
<meta content="{site}/assets/img/og-card.jpg" property="og:image"/>
<meta content="1200" property="og:image:width"/>
<meta content="630" property="og:image:height"/>
<meta content="Ömer Can Atlı" property="og:site_name"/>
<meta content="summary_large_image" name="twitter:card"/>
<meta content="{title}" name="twitter:title"/>
<meta content="{desc}" name="twitter:description"/>
<meta content="{site}/assets/img/og-card.jpg" name="twitter:image"/>
<meta content="#0e0e12" name="theme-color"/>
<link href="/assets/img/favicon.svg" rel="icon" type="image/svg+xml"/>
<link href="/favicon.ico" rel="alternate icon" sizes="16x16 32x32 48x48"/>
<link href="/assets/img/apple-touch-icon.png" rel="apple-touch-icon" sizes="180x180"/>
<link href="/site.webmanifest" rel="manifest"/>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet"/>
<link href="/assets/css/base.css" rel="stylesheet"/>
{head_extra}
<script src="https://cdn.tailwindcss.com"></script>
<script src="/assets/js/tw-config.js"></script>
</head>
<body class="bg-surface-container-lowest font-body-md text-body-md text-on-surface antialiased selection:bg-primary-container selection:text-on-primary-container min-h-screen flex flex-col justify-between">
<canvas aria-hidden="true" id="bg-canvas"></canvas>

<header class="fixed top-0 inset-x-0 z-50 bg-surface-container-lowest/80 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
<div class="h-16 max-w-[1200px] mx-auto px-gutter-mobile lg:px-gutter-desktop flex items-center justify-between gap-space-md">
<a class="flex items-center gap-space-xs group shrink-0" href="/">
<span class="w-2 h-2 rounded-full bg-primary-container group-hover:scale-125 transition-transform shadow-[0_0_8px_#00f5ff]"></span>
<span class="font-label-code-md text-label-code-md tracking-wider text-primary font-bold uppercase">OCA.DEV</span>
<span class="font-label-code-sm text-label-code-sm text-outline hidden sm:inline-block tracking-widest uppercase">// SOFTWARE &amp; AI</span>
</a>
<nav class="hidden xl:flex items-center gap-space-xs p-space-3xs bg-surface-container-low/70 rounded-full shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
{nav}
</nav>
<div class="flex items-center gap-space-sm">
<div class="flex items-center gap-space-3xs p-space-3xs rounded-full bg-surface-container-low" style="border: 1px solid rgba(255,255,255,0.08);">
<button class="px-space-xs py-space-3xs rounded-full font-label-code-sm text-label-code-sm tracking-widest uppercase text-outline transition-colors" data-lang-btn="en" type="button">EN</button>
<button class="px-space-xs py-space-3xs rounded-full font-label-code-sm text-label-code-sm tracking-widest uppercase text-outline transition-colors" data-lang-btn="tr" type="button">TR</button>
</div>
<div class="hidden lg:flex items-center gap-space-xs px-space-sm py-space-2xs rounded-full bg-surface-container-low" style="border: 1px solid rgba(255,255,255,0.08);">
<span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary-container opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-tertiary-fixed-dim"></span></span>
<span class="font-label-code-sm text-label-code-sm text-on-surface-variant tracking-wider uppercase">GTU • CLASS OF 2027</span>
</div>
<button aria-expanded="false" aria-label="Menu" class="xl:hidden w-9 h-9 rounded-full bg-surface-container-low flex items-center justify-center" id="nav-toggle" style="border: 1px solid rgba(255,255,255,0.08);" type="button">
<span class="material-symbols-outlined text-[18px] text-on-surface-variant">menu</span>
</button>
</div>
</div>
<div class="xl:hidden bg-surface-container-lowest/95 backdrop-blur-xl px-gutter-mobile pb-space-md flex flex-col gap-space-2xs" hidden id="nav-drawer" style="border-top: 1px solid rgba(255,255,255,0.06);">
{nav_mobile}
</div>
</header>

<main class="w-full pt-16 bg-surface-container-lowest flex-1">
{body}
</main>

<footer class="w-full bg-surface-container-lowest/90 backdrop-blur-xl py-space-xl" style="border-top: 1px solid rgba(255,255,255,0.06);">
<div class="max-w-[1200px] mx-auto px-gutter-mobile lg:px-gutter-desktop flex flex-col md:flex-row items-center justify-between gap-space-lg">
<div class="flex flex-col sm:flex-row items-center gap-space-md text-center sm:text-left">
<div class="flex items-center gap-space-xs font-label-code-sm text-label-code-sm text-on-surface-variant">
<span class="material-symbols-outlined text-[14px] text-primary-fixed-dim">schedule</span>
<span id="local-clock">--:--:--</span>
</div>
<div class="hidden sm:inline-block text-outline-variant font-label-code-sm text-label-code-sm">/</div>
<div class="flex items-center gap-space-xs font-label-code-sm text-label-code-sm text-on-surface-variant">
<span class="material-symbols-outlined text-[14px] text-secondary">location_on</span>
<span>MALTEPE, İSTANBUL • TR</span>
</div>
</div>
<div class="flex items-center gap-space-sm">
<div class="flex items-center gap-space-xs px-space-sm py-space-2xs rounded-full bg-surface-container-low" style="border: 1px solid rgba(255,255,255,0.08);">
<span class="w-1.5 h-1.5 rounded-full bg-secondary-fixed-dim"></span>
<span class="font-label-code-sm text-label-code-sm text-on-surface-variant tracking-wider uppercase">.NET • SPRING BOOT • PYTORCH • FLUTTER</span>
</div>
<button aria-pressed="true" class="flex items-center gap-space-2xs px-space-sm py-space-2xs rounded-full bg-surface-container-low text-primary hover:bg-surface-container-high transition-colors" data-motion-toggle="" style="border: 1px solid rgba(255,255,255,0.08);" type="button">
<span class="material-symbols-outlined text-[14px]">motion_photos_on</span>
<span class="font-label-code-sm text-label-code-sm tracking-wider uppercase" data-lang="en">MOTION</span>
<span class="font-label-code-sm text-label-code-sm tracking-wider uppercase" data-lang="tr">HAREKET</span>
</button>
</div>
<div class="flex items-center gap-space-lg font-label-code-sm text-label-code-sm">
<a class="text-on-surface-variant hover:text-primary transition-colors uppercase tracking-wider" href="https://github.com/Byomer1021" rel="noreferrer" target="_blank">GITHUB</a>
<a class="text-on-surface-variant hover:text-primary transition-colors uppercase tracking-wider" href="https://www.linkedin.com/in/%C3%B6mer-can-atli-8a9b491b5/" rel="noreferrer" target="_blank">LINKEDIN</a>
<a class="text-on-surface-variant hover:text-primary transition-colors uppercase tracking-wider" href="/contact/">CONTACT</a>
</div>
</div>
</footer>

<script src="/assets/js/site.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js"></script>
<script defer src="/assets/js/bg-three.js"></script>
{page_script}</body>
</html>
"""


def check_inline_scripts(path, text):
    """A bare apostrophe inside a single-quoted JS string ends it early.

    Turkish suffixes attach with one ("Play'de", "18'i"), so this has broken the
    terminal three times. Flag it at build time rather than in the browser.
    """
    import re
    problems = []
    for block in re.findall(r"<script(?![^>]*'\ssrc=)[^>]*>(.*?)</script>", text, re.S):
        for n, line in enumerate(block.split(NL), 1):
            t = line.strip()
            if len(t) > 2 and t.startswith(chr(39)) and t.rstrip(",").endswith(chr(39)):
                inner = t.rstrip(",")[1:-1]
                if chr(39) in inner.replace(chr(92) + chr(39), ""):
                    problems.append((n, t[:70]))
    for n, t in problems:
        print(f"  !! {path}: line {n} has a stray apostrophe in a JS string: {t}",
              file=sys.stderr)
    return not problems


def build():
    written = []
    ok_scripts = True
    for name, out_path, active, title, desc in PAGES:
        body_file = BODIES / f"{name}.html"
        if not body_file.exists():
            print(f"  MISSING BODY: {body_file}", file=sys.stderr)
            continue
        parent = str(pathlib.PurePosixPath(out_path).parent)
        url = SITE + "/" if parent == "." else SITE + "/" + parent + "/"

        head_file = BODIES / f"{name}.head.html"
        head_extra = ""
        if head_file.exists():
            head_extra = head_file.read_text(encoding="utf-8").rstrip() + NL

        script_file = BODIES / f"{name}.script.js"
        page_script = ""
        if script_file.exists():
            page_script = (
                "<script>\n"
                + script_file.read_text(encoding="utf-8").rstrip()
                + "\n</script>\n"
            )
        body = body_file.read_text(encoding="utf-8").rstrip()

        # Expand the project footer from PROJECT_RING.
        ring_nav = next_nav(name)
        if NEXT_MARKER in body:
            if ring_nav is None:
                print(f"  !! {name}: has {NEXT_MARKER} but is not in PROJECT_RING",
                      file=sys.stderr)
                ok_scripts = False
            body = body.replace(NEXT_MARKER, ring_nav)
        elif ring_nav is not None:
            print(f"  !! {name}: in PROJECT_RING but its body has no {NEXT_MARKER}",
                  file=sys.stderr)
            ok_scripts = False

        html = SHELL.format(
            title=title, desc=desc, url=url, site=SITE,
            nav=nav_links(active), nav_mobile=nav_links(active, mobile=True),
            body=body,
            page_script=page_script,
            head_extra=head_extra,
        )
        dest = ROOT / out_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        if not check_inline_scripts(out_path, html):
            ok_scripts = False
        written.append(out_path)
        print(f"  wrote {out_path}")

    # Every bilingual block must carry both languages or one will render blank.
    print()
    for out_path in written:
        s = (ROOT / out_path).read_text(encoding="utf-8")
        en, tr = s.count('data-lang="en"'), s.count('data-lang="tr"')
        flag = "" if en == tr else "   <-- MISMATCH"
        print(f"  {out_path:42s} en={en:3d} tr={tr:3d}{flag}")
    if not ok_scripts:
        sys.exit(1)


if __name__ == "__main__":
    build()
