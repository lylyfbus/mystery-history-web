"""Replace the reference list and the editorial note of a post. The Amazon book line stays.

Usage: python3 tools/set_sources.py <slug> <file>

File format (plain UTF-8 text):
  One reference for each line:   URL | Publisher: Title | What it supports in the story
  One line for the note:         NOTE: text of the editorial note (1 or 2 sentences, about THIS story)
"""
import html
import re
import sys
from pathlib import Path

from sitelib import SRC, read_post, write
from set_body import to_html


def set_sources(slug, text):
    refs, note = [], None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("NOTE:"):
            note = line[5:].strip()
            continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) != 3 or not re.match(r"https://[^\s\"<>]+$", parts[0]) or not parts[1] or not parts[2]:
            raise SystemExit(f"{slug}: bad line (need: https URL | title | what it supports): {line[:90]}")
        refs.append(parts)
    if len(refs) < 4 or not note:
        raise SystemExit(f"{slug}: need 4 or more references and one NOTE: line")
    page = read_post(slug)["html"]
    start = page.index('<div class="post-sources">')
    end = page.index("</div>", start)
    amazon = [p for p in re.findall(r"<p\b[^>]*>.*?</p>", page[start:end], re.S) if "amazon.com" in p]
    out = ['<div class="post-sources">', "    <p>References &amp; Further Reading</p>", ""]
    for url, title, why in refs:
        out.append(f'        <p><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
                   f"{to_html(title)} &mdash; {to_html(why)}</a></p>")
    out.append("")
    out += [f"    {p}" for p in amazon]
    out.append(f'    <p class="source-note">Editorial note: {to_html(note)} See our <a href="/editorial-policy">Editorial Policy</a>.</p>')
    write(SRC / "posts" / f"{slug}.html", page[:start] + "\n".join(out) + "\n" + page[end:])
    print(f"{slug}: {len(refs)} references, {len(amazon)} book line(s)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    set_sources(sys.argv[1], Path(sys.argv[2]).read_text(encoding="utf-8"))
