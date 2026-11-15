"""Replace the story text of a post. Nothing else in the post changes.

Usage: python3 tools/set_body.py <post-slug> <text-file>

The text file is plain UTF-8. One paragraph for each block; a blank line between
blocks. <em>...</em> and <a href="/posts/slug">...</a> are permitted. All other characters are written as text.
"""
import re
import sys
from html.entities import codepoint2name
from pathlib import Path

from sitelib import SRC, body_html, read_post, word_count, write


def to_html(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"&lt;(/?)em&gt;", r"<\1em>", text)
    text = re.sub(r'&lt;a href="(/posts/[a-z0-9-]+)"&gt;(.*?)&lt;/a&gt;', r'<a href="\1">\2</a>', text)
    return "".join(ch if ord(ch) < 128 else f"&{codepoint2name[ord(ch)]};" if ord(ch) in codepoint2name
                   else f"&#{ord(ch)};" for ch in text)


def set_body(slug, text):
    paragraphs = [" ".join(block.split()) for block in re.split(r"\n\s*\n", text.strip()) if block.strip()]
    if len(paragraphs) < 8:
        raise SystemExit(f"{slug}: only {len(paragraphs)} paragraphs; the file looks wrong")
    post = read_post(slug)
    old_body = body_html(post["html"])
    if not old_body:
        raise SystemExit(f"{slug}: cannot find the story body")
    new_body = "\n\n" + "\n\n".join(f"        <p>{to_html(p)}</p>" for p in paragraphs) + "\n\n                "
    if post["html"].count(old_body) != 1:
        raise SystemExit(f"{slug}: story body is not unique in the file")
    write(SRC / "posts" / f"{slug}.html", post["html"].replace(old_body, new_body))
    old_words = sum(word_count(p) for p in post["paragraphs"])
    new_words = sum(word_count(p) for p in paragraphs)
    print(f"{slug}: {len(post['paragraphs'])} -> {len(paragraphs)} paragraphs, "
          f"{old_words} -> {new_words} words ({100 * new_words // max(old_words, 1)}%)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    set_body(sys.argv[1], Path(sys.argv[2]).read_text(encoding="utf-8"))
