"""Write the story text of a post to a plain text file, in the format that tools/set_body.py reads.

Usage: python3 tools/get_body.py <slug> <output-file>
"""
import html
import re
import sys
from pathlib import Path

from sitelib import body_html, read_post

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    body = body_html(read_post(sys.argv[1])["html"])
    paragraphs = []
    for tag, p in re.findall(r"<(p|h2)\b[^>]*>(.*?)</(?:p|h2)>", body, re.S):
        keep = re.sub(r"<(?!/?em>|a href=\"/posts/[a-z0-9-]+\">|/a>)[^>]+>", "", p)
        paragraphs.append(("## " if tag == "h2" else "") + " ".join(html.unescape(keep).split()))
    Path(sys.argv[2]).write_text("\n\n".join(paragraphs) + "\n", encoding="utf-8")
    print(f"{sys.argv[1]}: {len(paragraphs)} paragraphs -> {sys.argv[2]}")
