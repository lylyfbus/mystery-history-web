"""Replace the hero image of a post, and set the same description (alt) on the post and on all cards.

Usage:
  python3 tools/set_hero.py <slug> <image-file> "<alt text>" ["<credit line>"]
  python3 tools/set_hero.py --sync-alts        (copy the alt of each post hero to all its cards)

The image is cut to 4:3 if it is taller than that, made 1600 px wide at most, and saved as WebP.
The credit line (for photos that need one) is shown below the hero image.
Pillow is necessary for the image step. If this Python has no Pillow, set PM_PYTHON to one that has it.
"""
import html
import os
import re
import subprocess
import sys

from sitelib import GROUPS, SRC, post_slugs, read_post, write

PILLOW_PYTHONS = [os.environ.get("PM_PYTHON"), sys.executable,
                  os.path.expanduser("~/miniforge3/envs/ds/bin/python")]
CONVERT = """
import sys
from PIL import Image, ImageOps
src, out = sys.argv[1], sys.argv[2]
im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
w, h = im.size
if h > w * 3 / 4:                      # taller than 4:3: keep the middle
    new_h = int(w * 3 / 4)
    top = (h - new_h) // 2
    im = im.crop((0, top, w, top + new_h))
if im.width > 1600:
    im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
im.save(out, "WEBP", quality=80, method=6)
print(im.size)
"""


def convert(image, out):
    for python in PILLOW_PYTHONS:
        if not python or not os.path.exists(python):
            continue
        if subprocess.run([python, "-c", "import PIL"], capture_output=True).returncode == 0:
            result = subprocess.run([python, "-c", CONVERT, str(image), str(out)], capture_output=True, text=True)
            if result.returncode != 0:
                raise SystemExit(result.stderr)
            return result.stdout.strip()
    raise SystemExit("No Python with Pillow found. Set PM_PYTHON=/path/to/python")


def set_alt(slug, alt):
    """Write alt on the post hero and on each card that shows this hero. Returns the number of files changed."""
    attr = html.escape(alt, quote=True)
    pattern = re.compile(r'(<img\b[^>]*?src="[^"]*/posts/' + re.escape(slug) + r'/hero\.webp"[^>]*?alt=")[^"]*(")', re.S)
    changed = 0
    paths = [SRC / "posts" / f"{slug}.html", SRC / "index.html", SRC / "archive.html"]
    paths += [SRC / "categories" / f"{g}.html" for g in GROUPS]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        new = pattern.sub(lambda m: m.group(1) + attr + m.group(2), text)
        if new != text:
            write(path, new)
            changed += 1
    return changed


def set_credit(slug, credit):
    path = SRC / "posts" / f"{slug}.html"
    text = re.sub(r'\n?[ \t]*<p class="image-credit">.*?</p>', "", path.read_text(encoding="utf-8"), flags=re.S)
    if credit:
        line = f'\n            <p class="image-credit">{html.escape(credit, quote=False)}</p>'
        text, n = re.subn(r'(<img\b[^>]*class="hero-image"[^>]*>)', lambda m: m.group(1) + line, text, count=1)
        if n != 1:
            raise SystemExit(f"{slug}: cannot find the hero image")
    write(path, text)


def sync_alts():
    """Use the best description we have for each hero: the post's, or a card's if the post only has the title."""
    for slug in post_slugs():
        post = read_post(slug)
        alt = post["hero_alt"]
        if len(alt) < 20 or alt == post["title"]:
            cards = []
            for path in [SRC / "index.html", SRC / "archive.html"] + [SRC / "categories" / f"{g}.html" for g in GROUPS]:
                cards += re.findall(r'/posts/' + re.escape(slug) + r'/hero\.webp" alt="([^"]*)"', path.read_text(encoding="utf-8"))
            better = [html.unescape(c) for c in cards if len(c) >= 20 and html.unescape(c) != post["title"]]
            if not better:
                print(f"{slug}: NO GOOD ALT TEXT; write one with set_hero.py")
                continue
            alt = max(better, key=len)
        set_alt(slug, alt)


if __name__ == "__main__":
    if sys.argv[1:] == ["--sync-alts"]:
        sync_alts()
    elif len(sys.argv) in (4, 5):
        slug, image, alt = sys.argv[1:4]
        if slug not in post_slugs():
            raise SystemExit(f"unknown post: {slug}")
        size = convert(image, SRC / "static" / "images" / "posts" / slug / "hero.webp")
        files = set_alt(slug, alt)
        set_credit(slug, sys.argv[4] if len(sys.argv) == 5 else "")
        print(f"{slug}: hero.webp {size}, alt set in {files} file(s)")
    else:
        raise SystemExit(__doc__)
