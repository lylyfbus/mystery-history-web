"""Put the story lists in the default order: added time, newest first.

Stories with the same date keep their order. Run this after a story is added.
It changes the 3 group pages and the 3 lists of archive.html, then the home rows and stories.json.
"""
import json
import re

import build_home
import build_stories
from sitelib import GROUPS, SRC, post_dates, write


def reorder(text, card_class, dates):
    """Sort each run of cards (lines next to each other) in the text."""
    card = rf'<a href="/posts/([a-z0-9-]+)" class="{card_class}">.*?</a>'
    run = re.compile(rf"(?:{card}\n)+", re.S)

    def fix(match):
        cards = [m.group(0) for m in re.finditer(card, match.group(0), re.S)]
        slug = lambda c: re.match(r'<a href="/posts/([a-z0-9-]+)"', c).group(1)  # noqa: E731
        cards.sort(key=lambda c: dates[slug(c)]["iso"], reverse=True)  # the sort is stable
        return "\n".join(cards) + "\n"

    return run.sub(fix, text)


def main():
    dates = post_dates()
    for path, card_class in [(SRC / "archive.html", "archive-card")] + \
            [(SRC / "categories" / f"{g}.html", "category-bar") for g in GROUPS]:
        write(path, reorder(path.read_text(encoding="utf-8"), card_class, dates))
    build_home.build()
    stories = build_stories.build()
    write(SRC / "static" / "data" / "stories.json", json.dumps(stories, ensure_ascii=False, indent=1) + "\n")
    print("lists: newest first")


if __name__ == "__main__":
    main()
