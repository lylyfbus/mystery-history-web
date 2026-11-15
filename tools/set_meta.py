"""Change the title or the description of a post in all places that show it.

Usage:
  python3 tools/set_meta.py <slug> --title "New title"
  python3 tools/set_meta.py <slug> --description "New description (160 characters at most)"

Title places: <title>, og:title, twitter:title, schema headline, the h1, the share links, and the
cards on the home, archive, and group pages. Then run tools/build_feed.py and tools/build_stories.py.
"""
import html
import json
import re
import sys
from urllib.parse import quote

from sitelib import GROUPS, SRC, post_slugs, read_post, write


def set_title(slug, title):
    path = SRC / "posts" / f"{slug}.html"
    page = path.read_text(encoding="utf-8")
    attr = html.escape(title, quote=True)
    text = html.escape(title, quote=False)
    url = f"https://pastmysteries.com/posts/{slug}"
    page = re.sub(r"<title>.*?</title>", lambda m: f"<title>{text} | Past Mystery</title>", page, count=1, flags=re.S)
    page = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + attr, page, count=1)
    page = re.sub(r'(<meta name="twitter:title" content=")[^"]*', lambda m: m.group(1) + attr, page, count=1)
    page = re.sub(r'("headline":\s*)"(?:[^"\\]|\\.)*"', lambda m: m.group(1) + json.dumps(title, ensure_ascii=False), page, count=1)
    page = re.sub(r'(<h1 class="post-title">).*?(</h1>)', lambda m: m.group(1) + text + m.group(2), page, count=1, flags=re.S)
    q = quote(title, safe=":")
    page = re.sub(r'(twitter\.com/intent/tweet\?url=' + re.escape(url) + r'&(?:amp;)?text=)[^"]*', lambda m: m.group(1) + q, page)
    page = re.sub(r'(reddit\.com/submit\?url=' + re.escape(url) + r'&(?:amp;)?title=)[^"]*', lambda m: m.group(1) + q, page)
    page = re.sub(r'(pinterest\.com/pin/create/button/\?url=' + re.escape(url) + r'&(?:amp;)?description=)[^"]*', lambda m: m.group(1) + q, page)
    write(path, page)
    card = re.compile(r'(<a href="/posts/' + re.escape(slug) + r'" class="[a-z-]+">.*?<h3 class="(?:card-title|category-bar-title)">).*?(</h3>)', re.S)
    for p in [SRC / "index.html", SRC / "archive.html"] + [SRC / "categories" / f"{g}.html" for g in GROUPS]:
        old = p.read_text(encoding="utf-8")
        new = card.sub(lambda m: m.group(1) + text + m.group(2), old)
        if new != old:
            write(p, new)


def set_description(slug, description):
    if len(description) > 160:
        raise SystemExit(f"{slug}: description has {len(description)} characters (max 160)")
    path = SRC / "posts" / f"{slug}.html"
    page = path.read_text(encoding="utf-8")
    attr = html.escape(description, quote=True)
    for pattern in (r'(<meta name="description" content=")[^"]*', r'(<meta property="og:description" content=")[^"]*',
                    r'(<meta name="twitter:description" content=")[^"]*'):
        page = re.sub(pattern, lambda m: m.group(1) + attr, page, count=1)
    page = re.sub(r'("headline":[^\n]*\n\s*"description":\s*)"(?:[^"\\]|\\.)*"',
                  lambda m: m.group(1) + json.dumps(description, ensure_ascii=False), page, count=1)
    write(path, page)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[2] not in ("--title", "--description") or sys.argv[1] not in post_slugs():
        raise SystemExit(__doc__)
    (set_title if sys.argv[2] == "--title" else set_description)(sys.argv[1], sys.argv[3].strip())
    print(f"{sys.argv[1]}: {sys.argv[2][2:]} set")
