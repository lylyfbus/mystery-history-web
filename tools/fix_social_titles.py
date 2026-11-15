"""Make og:title, twitter:title and the schema headline equal to the h1 of each post."""
import html
import json
import re
from sitelib import SRC, post_slugs, read_post, write

changed = 0
for slug in post_slugs():
    post = read_post(slug)
    page = post["html"]
    attr = html.escape(post["title"], quote=True)
    new = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + attr, page, count=1)
    new = re.sub(r'(<meta name="twitter:title" content=")[^"]*', lambda m: m.group(1) + attr, new, count=1)
    new = re.sub(r'("headline":\s*)"(?:[^"\\]|\\.)*"',
                 lambda m: m.group(1) + json.dumps(post["title"], ensure_ascii=False), new, count=1)
    if new != page:
        write(SRC / "posts" / f"{slug}.html", new)
        changed += 1
print(f"social titles: {changed} post(s) changed")
