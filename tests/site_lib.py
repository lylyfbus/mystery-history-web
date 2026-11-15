"""Read helpers for the Past Mystery static site. Used by the tests and by tools/."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

GROUPS = {
    "ancient-mysteries": "Ancient Mysteries",
    "interesting-history": "Interesting History",
    "unknown-phenomena": "Unknown Phenomena",
}

MENU = [
    ("/", "Home"),
    ("/archive", "All Stories"),
    ("/about", "About"),
    ("/editorial-policy", "Editorial Policy"),
    ("/contact", "Contact"),
]

FOOTER = ["/archive", "/about", "/editorial-policy", "/contact", "/privacy-policy"]


def all_pages():
    return sorted(p for p in SRC.rglob("*.html") if not p.name.startswith("google"))


def post_slugs():
    return sorted(p.stem for p in (SRC / "posts").glob("*.html"))


def strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def body_html(page_html):
    """The story part of a post: after the post header, before the sources."""
    start = page_html.find("</header>", page_html.find('class="post-header"'))
    end = page_html.find('<div class="post-sources"')
    if start < 0 or end < 0:
        return ""
    return page_html[start + len("</header>"):end]


def article_html(page_html):
    start = page_html.find("<article")
    end = page_html.find('<div class="post-sources"')
    return page_html[start:end] if start >= 0 and end >= 0 else ""


def _first(pattern, text, flags=re.S):
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


def read_post(slug):
    page = (SRC / "posts" / f"{slug}.html").read_text(encoding="utf-8")
    hero = re.search(r'<img\b[^>]*class="hero-image"[^>]*>', page)
    hero_tag = hero.group(0) if hero else ""
    crumb = _first(r'<nav class="breadcrumb"[^>]*>(.*?)</nav>', page) or ""
    return {
        "slug": slug,
        "html": page,
        "title": strip_tags(_first(r'<h1 class="post-title">(.*?)</h1>', page) or ""),
        "group": strip_tags(_first(r'class="post-category">(.*?)</span>', page) or ""),
        "breadcrumb_group": strip_tags(_first(r'<a href="/categories/[^"]*"[^>]*>(.*?)</a>', crumb) or ""),
        "breadcrumb_href": _first(r'<a href="(/categories/[^"]*)"', crumb),
        "schema_group": _first(r'"position":\s*2,\s*"name":\s*"([^"]*)"', page),
        "schema_group_item": _first(r'"position":\s*2,\s*"name":\s*"[^"]*",\s*"item":\s*"([^"]*)"', page),
        "paragraphs": [strip_tags(p) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", body_html(page), re.S)],
        "hero_src": _first(r'src="([^"]*)"', hero_tag),
        "hero_alt": html.unescape(_first(r'alt="([^"]*)"', hero_tag) or ""),
        "description": html.unescape(_first(r'<meta name="description" content="([^"]*)"', page) or ""),
    }


_ABBREV = r"(?:Mr|Mrs|Ms|Dr|St|Sr|Jr|Lt|Col|Gen|Capt|Sgt|Prof|Rev|Gov|No|vs|ca|c|U\.S|U\.K|B\.C|A\.D|a\.m|p\.m|e\.g|i\.e|[A-Z])"
_SPLIT = re.compile(r"""([.!?]["'\u201d\u2019)]*)\s+(?=["'\u201c\u2018(]?[A-Z0-9])""")


def sentences(text):
    """Split plain text into sentences. Does not split after titles or initials."""
    out, buf = [], ""
    for piece in _SPLIT.sub(lambda m: m.group(1) + "\n", text).split("\n"):
        buf = f"{buf} {piece}".strip() if buf else piece.strip()
        if re.search(rf"(?:^|[\s(\"“]){_ABBREV}\.$", buf):
            continue
        out.append(buf)
        buf = ""
    if buf:
        out.append(buf)
    return [s for s in out if s]


def word_count(text):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’,.\-]*", text))


def resolve(page, href):
    """Map an internal href/src to a file. None means: external, do not check."""
    href = href.split("#")[0].split("?")[0]
    if not href or href.startswith(("http:", "https:", "mailto:", "//", "data:", "tel:", "/_vercel/")):
        return None
    base = SRC if href.startswith("/") else page.parent
    target = (base / href.lstrip("/")).resolve()
    if target.is_dir():
        return target / "index.html"
    if target.exists():
        return target
    return target.with_name(target.name + ".html")  # Vercel cleanUrls


def menu_links(page_html):
    nav = _first(r'<nav class="site-nav">(.*?)</nav>', page_html) or ""
    return [(h, strip_tags(t)) for h, t in re.findall(r'<a href="([^"]*)"[^>]*>(.*?)</a>', nav, re.S)]


def footer_links(page_html):
    foot = _first(r'<footer class="site-footer">(.*?)</footer>', page_html) or ""
    return re.findall(r'<a href="([^"]*)"', foot)


def listed_slugs(path, pattern=r'href="/posts/([a-z0-9-]+)"'):
    return re.findall(pattern, (SRC / path).read_text(encoding="utf-8"))


def post_dates():
    return json.loads((SRC / "post-dates.json").read_text(encoding="utf-8"))
