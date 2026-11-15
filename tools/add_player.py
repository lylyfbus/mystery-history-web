"""Add the audio player files to all pages, and the Listen buttons to all posts. Safe to run again."""
import re
from sitelib import SRC, all_pages, write

CSS = '    <link rel="stylesheet" href="/static/css/player.css">\n'
JS = ('    <script defer src="/static/js/player-core.js"></script>\n'
      '    <script defer src="/static/js/player-ui.js"></script>\n')


def row(slug):
    return (f'            <div class="listen-row" data-slug="{slug}">'
            '<button class="listen-btn" type="button">&#9654; Listen</button>'
            '<button class="listen-add" type="button">+ Add to playlist</button></div>\n')


def fix(page, text):
    if "/static/css/player.css" not in text:
        text = text.replace("</head>", CSS + "</head>", 1)
    if "/static/js/player-ui.js" not in text:
        text = text.replace("</body>", JS + "</body>", 1)
    if page.parent.name == "posts" and 'class="listen-row"' not in text:
        text, n = re.subn(r'(<img\b[^>]*class="hero-image"[^>]*>\n?)', lambda m: m.group(1).rstrip("\n") + "\n" + row(page.stem),
                          text, count=1)
        if n != 1:
            raise SystemExit(f"{page}: cannot find the hero image")
    return text


if __name__ == "__main__":
    changed = 0
    for page in all_pages():
        old = page.read_text(encoding="utf-8")
        new = fix(page, old)
        if new != old:
            write(page, new)
            changed += 1
    print(f"player: {changed} page(s) changed")
