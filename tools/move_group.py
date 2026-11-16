"""Move a post to a different group. Updates all places that show the group.

Usage: python3 tools/move_group.py <post-slug> <group-slug>
Example: python3 tools/move_group.py oak-island-money-pit-nova-scotia interesting-history
"""
import re
import sys
from collections import Counter

import build_home
from sitelib import GROUPS, SRC, post_slugs, read_post, write


def take(text, pattern):
    """Remove the first match from text. Return (text, match text or None)."""
    match = re.search(pattern, text, re.S)
    if not match:
        return text, None
    return text[:match.start()] + text[match.end():], match.group(0)


def add_after_last(text, card_class, card, start=0, end=None):
    """Put the card after the last card of this class between start and end."""
    end = len(text) if end is None else end
    last = text.rfind(f'class="{card_class}"', start, end)
    if last < 0:
        raise SystemExit(f"cannot find a {card_class} to put the card after")
    close = text.index("</a>", last) + len("</a>")
    return text[:close] + "\n" + card.strip("\n") + text[close:]


def section_bounds(text, marker, group):
    start = text.index(marker.format(group=group))
    nxt = min((i for i in (text.find(marker.format(group=g), start + 1) for g in GROUPS) if i > 0),
              default=len(text))
    return start, nxt


def move(slug, group):
    if slug not in post_slugs():
        raise SystemExit(f"unknown post: {slug}")
    if group not in GROUPS:
        raise SystemExit(f"unknown group: {group} (use one of {', '.join(GROUPS)})")
    name = GROUPS[group]
    post = read_post(slug)
    if post["group"] == name:
        print(f"{slug}: already in {name}")
    # 1. the post: badge, breadcrumb, breadcrumb schema
    page = post["html"]
    page = re.sub(r'(<span class="post-category">)[^<]*', rf"\g<1>{name}", page, count=1)
    page = re.sub(r'(<nav class="breadcrumb"[^>]*>.*?<a href=")/categories/[a-z-]+("[^>]*>)[^<]*',
                  rf"\g<1>/categories/{group}\g<2>{name}", page, count=1, flags=re.S)
    page = re.sub(r'("position":\s*2,\s*"name":\s*")[^"]*(",\s*"item":\s*")[^"]*',
                  rf"\g<1>{name}\g<2>https://pastmysteries.com/categories/{group}", page, count=1)
    write(SRC / "posts" / f"{slug}.html", page)

    # 2. the group pages
    card = None
    for g in GROUPS:
        path = SRC / "categories" / f"{g}.html"
        text, found = take(path.read_text(encoding="utf-8"),
                           rf'<a href="/posts/{slug}" class="category-bar">.*?</a>\n?')
        if found:
            card = card or found
            write(path, text)
    if card is None:
        raise SystemExit(f"{slug}: no card on a group page; add one by hand")
    path = SRC / "categories" / f"{group}.html"
    write(path, add_after_last(path.read_text(encoding="utf-8"), "category-bar", card))

    # 3. the archive (1 grid for each group)
    path = SRC / "archive.html"
    text, card = take(path.read_text(encoding="utf-8"), rf'<a href="/posts/{slug}" class="archive-card">.*?</a>\n?')
    if card:
        start, end = section_bounds(text, '<h3 class="archive-cat-title"><a href="/categories/{group}">', group)
        write(path, add_after_last(text, "archive-card", card, start, end))

    # 4. the home page: the row (only if the post is there) and the 3 counts
    path = SRC / "index.html"
    text, card = take(path.read_text(encoding="utf-8"), rf'<a href="/posts/{slug}" class="carousel-card">.*?</a>\n?')
    if card:
        start, end = section_bounds(text, 'href="/categories/{group}" class="carousel-view-all"', group)
        text = add_after_last(text, "carousel-card", card, start, end)
    counts = Counter(read_post(s)["group"] for s in post_slugs())
    for g, gname in GROUPS.items():
        text = re.sub(rf'(href="/categories/{g}" class="carousel-view-all">View All \()\d+', rf"\g<1>{counts[gname]}", text)
    write(path, text)
    build_home.build()  # each row = first 10 stories of its group page
    print(f"{slug}: now in {name}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    move(sys.argv[1], sys.argv[2])
