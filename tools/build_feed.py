"""Build src/feed.xml from the posts: one item for each post, newest first."""
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

from sitelib import SRC, post_dates, post_slugs, read_post, write


def post_date(slug, post, dates):
    iso = dates.get(slug, {}).get("iso")
    if not iso:
        match = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', post["html"])
        iso = match.group(1) if match else "2026-01-01"
    return datetime.strptime(iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def build():
    dates = post_dates()
    posts = [(post_date(s, p, dates), s, p) for s, p in ((s, read_post(s)) for s in post_slugs())]
    posts.sort(key=lambda item: (item[0], item[1]), reverse=True)
    items = []
    for when, slug, post in posts:
        url = f"https://pastmysteries.com/posts/{slug}"
        items.append(
            "    <item>\n"
            f"      <title>{escape(post['title'])}</title>\n"
            f"      <link>{url}</link>\n"
            f"      <description>{escape(post['description'])}</description>\n"
            f"      <pubDate>{format_datetime(when)}</pubDate>\n"
            f"      <guid>{url}</guid>\n"
            "    </item>\n")
    newest = format_datetime(posts[0][0]) if posts else ""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
            "  <channel>\n"
            "    <title>Past Mystery</title>\n"
            "    <link>https://pastmysteries.com/</link>\n"
            "    <description>Evidence-based explainers on ancient mysteries, unusual historical events, "
            "and unexplained phenomena.</description>\n"
            "    <language>en-us</language>\n"
            f"    <lastBuildDate>{newest}</lastBuildDate>\n"
            '    <atom:link href="https://pastmysteries.com/feed.xml" rel="self" type="application/rss+xml" />\n'
            + "".join(items) + "  </channel>\n</rss>\n")


if __name__ == "__main__":
    write(SRC / "feed.xml", build())
    print(f"feed.xml: {len(post_slugs())} items")
