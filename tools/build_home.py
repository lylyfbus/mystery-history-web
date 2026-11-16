"""Rebuild the 3 story rows on the home page.

Each row shows the first 10 stories of its group page (src/categories/<group>.html), in the same order.
Run this after the order on a group page changes, or after a story is added or moved.
"""
import re

from sitelib import GROUPS, SRC, listed_slugs, write

ROW_SIZE = 10


def build():
    page = (SRC / "index.html").read_text(encoding="utf-8")
    archive = (SRC / "archive.html").read_text(encoding="utf-8")
    for group in GROUPS:
        top = listed_slugs(f"categories/{group}.html", r'href="/posts/([a-z0-9-]+)" class="category-bar"')[:ROW_SIZE]
        cards = []
        for slug in top:
            card = re.search(rf'<a href="/posts/{slug}" class="archive-card">.*?</a>', archive, re.S)
            if not card:
                raise SystemExit(f"{slug}: no card in archive.html")
            cards.append(card.group(0).replace('class="archive-card"', 'class="carousel-card"', 1))
        row = re.compile(rf'(href="/categories/{group}" class="carousel-view-all".*?<div class="carousel-track">\n)(.*?)([ \t]*</div>\s*<button class="carousel-btn carousel-btn-right")', re.S)
        if not row.search(page):
            raise SystemExit(f"index.html: no row for {group}")
        page = row.sub(lambda m: m.group(1) + "\n".join(cards) + "\n" + m.group(3), page, count=1)
    write(SRC / "index.html", page)
    print(f"index.html: {len(GROUPS)} rows, {ROW_SIZE} stories each")


if __name__ == "__main__":
    build()
