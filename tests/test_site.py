"""Tests for the static site. Each test stops a problem that we had before.

Run: ./run_tests.sh   (or: python3 -m unittest discover -s tests -v)
"""
import html
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_lib import (FOOTER, GROUPS, MENU, ROOT, SRC, all_pages, article_html, body_html,  # noqa: E402
                      footer_links, listed_slugs, menu_links, post_slugs, read_post, resolve,
                      sentences, word_count)

MAX_PARAGRAPH_WORDS = 100
MAX_SENTENCE_WORDS = 30
MAX_MEAN_SENTENCE_WORDS = 18
BANNED_PHRASES = ["breathtaking", "masterclass", "nearly severed", "ripped open"]

# Until all posts are rewritten, the text rules apply only to the posts in this file.
_REWRITTEN = ROOT / "tests" / "rewritten.txt"


def text_rule_slugs():
    if _REWRITTEN.exists():
        return [s.strip() for s in _REWRITTEN.read_text().split() if s.strip()]
    return post_slugs()


def plain(text):
    """Same text with straight quotes, for comparison of titles."""
    return (text or "").replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')


def rel(path):
    return str(path.relative_to(SRC))


class SiteTests(unittest.TestCase):
    maxDiff = None

    def check(self, problems):
        if problems:
            more = f"\n... and {len(problems) - 25} more" if len(problems) > 25 else ""
            self.fail(f"{len(problems)} problem(s):\n" + "\n".join(map(str, problems[:25])) + more)

    # --- links ---------------------------------------------------------
    def test_internal_links_and_images_resolve(self):
        bad = []
        for page in all_pages():
            for ref in re.findall(r'(?:href|src)="([^"]*)"', page.read_text(encoding="utf-8")):
                target = resolve(page, ref)
                if target is not None and not target.is_file():
                    bad.append(f"{rel(page)}: {ref}")
        self.check(bad)

    # --- same frame on all pages --------------------------------------
    def test_menu_is_same_on_all_pages(self):
        bad = [f"{rel(p)}: {menu_links(p.read_text(encoding='utf-8'))}"
               for p in all_pages() if menu_links(p.read_text(encoding="utf-8")) != MENU]
        self.check(bad)

    def test_footer_links_same_on_all_pages(self):
        bad = [f"{rel(p)}: {footer_links(p.read_text(encoding='utf-8'))}"
               for p in all_pages() if footer_links(p.read_text(encoding="utf-8")) != FOOTER]
        self.check(bad)

    # --- posts ---------------------------------------------------------
    def test_post_head_uses_own_slug(self):
        bad = []
        for slug in post_slugs():
            post = read_post(slug)
            page = post["html"]
            url = f"https://pastmysteries.com/posts/{slug}"
            image = f"https://pastmysteries.com/static/images/posts/{slug}/hero.webp"
            wanted = {
                "canonical": f'<link rel="canonical" href="{url}">',
                "og:url": f'<meta property="og:url" content="{url}">',
                "og:image": f'<meta property="og:image" content="{image}">',
                "twitter:image": f'<meta name="twitter:image" content="{image}">',
                "schema @id": f'"@id": "{url}"',
                "schema image": f'"image": "{image}"',
            }
            for name, text in wanted.items():
                if text not in page:
                    bad.append(f"{slug}: {name} does not use the post's own slug")
            titles = {
                "og:title": re.search(r'<meta property="og:title" content="([^"]*)"', page),
                "twitter:title": re.search(r'<meta name="twitter:title" content="([^"]*)"', page),
                "schema headline": re.search(r'"headline":\s*"((?:[^"\\]|\\.)*)"', page),
            }
            for name, match in titles.items():
                got = html.unescape(match.group(1)).replace('\\"', '"') if match else None
                if plain(got) != plain(post["title"]):
                    bad.append(f"{slug}: {name} is {got!r}, h1 is {post['title']!r}")
            if post["hero_src"] != f"../static/images/posts/{slug}/hero.webp":
                bad.append(f"{slug}: hero image is {post['hero_src']}")
        self.check(bad)

    def test_no_tag_inside_attribute(self):
        # Problem we had: an auto-link tool put <a href> inside an alt="" text.
        bad = []
        for page in all_pages():
            for value in re.findall(r'(?:alt|content|title|aria-label)="([^"]*)"', page.read_text(encoding="utf-8")):
                if "<" in value or ">" in value:
                    bad.append(f"{rel(page)}: tag inside attribute: {value[:80]}")
            if re.search(r'alt="[^"]*<a href=', page.read_text(encoding="utf-8")):
                bad.append(f"{rel(page)}: <a> inside alt text")
        self.check(bad)

    def test_post_format(self):
        bad = []
        for slug in post_slugs():
            page = read_post(slug)["html"]
            body = body_html(page)
            if not body:
                bad.append(f"{slug}: cannot find the story body")
                continue
            for tag in ("h2", "h3", "h4", "ul", "ol", "img", "audio", "div"):
                if re.search(rf"<{tag}\b", body):
                    bad.append(f"{slug}: <{tag}> in the story body")
            if len(re.findall(r"<img\b", article_html(page))) != 1:
                bad.append(f"{slug}: the article must have exactly 1 image (the hero)")
            for needed in ('class="hero-image"', 'class="post-sources"', 'class="share-buttons"',
                           'class="breadcrumb"', 'class="post-category"'):
                if needed not in page:
                    bad.append(f"{slug}: missing {needed}")
            if page.count("<article") != 1 or page.count("<h1") != 1:
                bad.append(f"{slug}: must have 1 <article> and 1 <h1>")
        self.check(bad)

    def test_group_is_consistent_in_post(self):
        bad = []
        by_name = {name: slug for slug, name in GROUPS.items()}
        for slug in post_slugs():
            post = read_post(slug)
            group = post["group"]
            if group not in by_name:
                bad.append(f"{slug}: unknown group {group!r}")
                continue
            if post["breadcrumb_group"] != group or post["schema_group"] != group:
                bad.append(f"{slug}: badge {group!r}, breadcrumb {post['breadcrumb_group']!r}, "
                           f"schema {post['schema_group']!r}")
            href = f"/categories/{by_name[group]}"
            if post["breadcrumb_href"] != href or post["schema_group_item"] != f"https://pastmysteries.com{href}":
                bad.append(f"{slug}: breadcrumb links {post['breadcrumb_href']} / {post['schema_group_item']}")
        self.check(bad)

    # --- listings --------------------------------------------------------
    def test_each_post_listed_once_per_listing(self):
        bad = []
        slugs = post_slugs()
        group_of = {s: read_post(s)["group"] for s in slugs}
        on_group_page = {g: listed_slugs(f"categories/{g}.html") for g in GROUPS}
        for slug in slugs:
            homes = [g for g, listed in on_group_page.items() for s in listed if s == slug]
            want = [g for g, name in GROUPS.items() if name == group_of[slug]]
            if homes != want:
                bad.append(f"{slug}: is on group pages {homes}, must be on {want}")
        loc = r"pastmysteries\.com/posts/([a-z0-9-]+)</(?:loc|link)>"
        for path, pattern in (("archive.html", r'href="/posts/([a-z0-9-]+)" class="archive-card"'),
                              ("sitemap.xml", loc), ("feed.xml", loc)):
            counts = Counter(listed_slugs(path, pattern))
            for slug in slugs:
                if counts[slug] != 1:
                    bad.append(f"{path}: {slug} is listed {counts[slug]} times")
            for extra in sorted(set(counts) - set(slugs)):
                bad.append(f"{path}: lists {extra}, which is not a post")
        home = Counter(listed_slugs("index.html"))
        bad += [f"index.html: {s} is listed {n} times" for s, n in home.items() if n > 1 or s not in slugs]
        self.check(bad)

    def test_home_counts_and_sections(self):
        bad = []
        page = (SRC / "index.html").read_text(encoding="utf-8")
        counts = Counter(read_post(s)["group"] for s in post_slugs())
        sections = page.split('<section class="carousel-section">')[1:]
        for gslug, name in GROUPS.items():
            match = re.search(rf'href="/categories/{gslug}"[^>]*>View All \((\d+)\)', page)
            if not match or int(match.group(1)) != counts[name]:
                bad.append(f"index.html: {name} shows {match.group(1) if match else None}, has {counts[name]} posts")
            for section in sections:
                if f"/categories/{gslug}" in section:
                    for slug in re.findall(r'href="/posts/([a-z0-9-]+)"', section):
                        if read_post(slug)["group"] != name:
                            bad.append(f"index.html: {slug} is in the {name} row")
        self.check(bad)

    # --- text rules (audience: age 10+) ---------------------------------
    def test_paragraph_length(self):
        bad = []
        for slug in text_rule_slugs():
            for i, para in enumerate(read_post(slug)["paragraphs"], 1):
                n = word_count(para)
                if n > MAX_PARAGRAPH_WORDS:
                    bad.append(f"{slug}: paragraph {i} has {n} words (max {MAX_PARAGRAPH_WORDS})")
        self.check(bad)

    def test_sentence_length(self):
        bad = []
        for slug in text_rule_slugs():
            lengths = []
            for para in read_post(slug)["paragraphs"]:
                for sentence in sentences(para):
                    n = word_count(sentence)
                    lengths.append(n)
                    if n > MAX_SENTENCE_WORDS:
                        bad.append(f"{slug}: {n} words: {sentence[:90]}...")
            if lengths and sum(lengths) / len(lengths) > MAX_MEAN_SENTENCE_WORDS:
                bad.append(f"{slug}: average sentence is {sum(lengths) / len(lengths):.1f} words "
                           f"(max {MAX_MEAN_SENTENCE_WORDS})")
        self.check(bad)

    def test_no_banned_phrases(self):
        bad = []
        for slug in text_rule_slugs():
            text = " ".join(read_post(slug)["paragraphs"]).lower()
            bad += [f"{slug}: contains {phrase!r}" for phrase in BANNED_PHRASES if phrase in text]
        self.check(bad)

    def test_post_is_not_empty(self):
        bad = []
        for slug in post_slugs():
            words = sum(word_count(p) for p in read_post(slug)["paragraphs"])
            if words < 900:
                bad.append(f"{slug}: only {words} words in the story")
        self.check(bad)


class SentenceSplitTests(unittest.TestCase):
    def test_split(self):
        self.assertEqual(sentences("Dr. Smith went home. He slept."), ["Dr. Smith went home.", "He slept."])
        self.assertEqual(sentences('He said "Stop!" Then he ran.'), ['He said "Stop!"', "Then he ran."])
        self.assertEqual(sentences("It cost $2.5 million. J. Edgar Hoover knew."),
                         ["It cost $2.5 million.", "J. Edgar Hoover knew."])
        self.assertEqual(sentences("The U.S. Navy looked. Nothing."), ["The U.S. Navy looked.", "Nothing."])


if __name__ == "__main__":
    unittest.main()
