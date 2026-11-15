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

# Posts that were in the wrong group before. The date of the real thing decides the group.
EXPECTED_GROUP = {
    "oak-island-money-pit-nova-scotia": "Interesting History",  # digging started in 1795
    "el-dorado-lost-city": "Interesting History",               # legend of the 1500s
    "crystal-skulls": "Interesting History",                    # made in the 1800s
    "shroud-of-turin": "Interesting History",                   # first record in 1354
    "voynich-manuscript-mystery": "Interesting History",        # a book from the 1400s
    "winchester-mystery-house": "Interesting History",          # a house and its owner
    "dancing-plague-1518": "Interesting History",               # a recorded event of 1518
    "flannan-isle-lighthouse": "Interesting History",           # a disappearance, as Mary Celeste
    "philadelphia-experiment": "Unknown Phenomena",             # a claimed event without records
    "skinwalker-ranch": "Unknown Phenomena",
}

# Heroes that were replaced because the old AI image did not agree with the story.
REPLACED_HEROES = ["sacsayhuaman", "rosetta-stone", "gobekli-tepe", "pentagon-uap-reports", "molasses-flood",
                   "copper-scroll-treasure", "saqqara-bird", "shroud-of-turin"]


def text_rule_slugs():
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

    def test_archive_sections(self):
        # The archive has 1 grid for each group. A card must be in the grid of its group.
        bad = []
        page = (SRC / "archive.html").read_text(encoding="utf-8")
        parts = re.split(r'<h3 class="archive-cat-title"><a href="/categories/([a-z-]+)">', page)
        seen = parts[1::2]
        if sorted(seen) != sorted(GROUPS):
            bad.append(f"archive.html: sections are {seen}")
        for gslug, section in zip(parts[1::2], parts[2::2]):
            for slug in re.findall(r'href="/posts/([a-z0-9-]+)" class="archive-card"', section):
                if read_post(slug)["group"] != GROUPS.get(gslug):
                    bad.append(f"archive.html: {slug} is in the {gslug} section")
        self.check(bad)

    def test_group_assignment(self):
        # Group rules: docs/superpowers/specs/2026-11-15-...-design.md section 6.
        bad = [f"{slug}: is {read_post(slug)['group']!r}, must be {want!r}"
               for slug, want in EXPECTED_GROUP.items() if read_post(slug)["group"] != want]
        self.check(bad)

    # --- images -----------------------------------------------------------
    def test_hero_alt_same_on_all_cards(self):
        # A card on the home, archive, or group page shows the hero of a post.
        # Its description (alt) must be the same as on the post. Tool: tools/set_hero.py
        bad = []
        alts = {slug: read_post(slug)["hero_alt"] for slug in post_slugs()}
        for slug, alt in alts.items():
            if len(alt) < 20 or alt == read_post(slug)["title"]:
                bad.append(f"{slug}: the hero alt text must describe the picture: {alt!r}")
        for path in ["index.html", "archive.html"] + [f"categories/{g}.html" for g in GROUPS]:
            text = (SRC / path).read_text(encoding="utf-8")
            for slug, alt in re.findall(r'<img src="[^"]*/posts/([a-z0-9-]+)/hero\.webp" alt="([^"]*)"', text):
                if slug in alts and html.unescape(alt) != alts[slug]:
                    bad.append(f"{path}: alt for {slug} is not the same as on the post")
        self.check(bad)

    def test_image_credits(self):
        # Each replaced hero has a row in docs/image-credits.md. Photos with a CC BY licence show a credit.
        licences = {"Public domain", "CC0", "CC BY 4.0", "CC BY-SA 3.0", "CC BY-SA 4.0", "Generated"}
        rows = [[c.strip() for c in line.strip().strip("|").split("|")]
                for line in (ROOT / "docs" / "image-credits.md").read_text(encoding="utf-8").splitlines()
                if line.startswith("| ") and not line.startswith("| Post") and not line.startswith("| ---")]
        bad = []
        for row in rows:
            if len(row) != 5:
                bad.append(f"bad row: {row}")
                continue
            slug, _file, author, licence, source = row
            if slug not in post_slugs():
                bad.append(f"{slug}: not a post")
                continue
            if licence not in licences:
                bad.append(f"{slug}: unknown licence {licence!r}")
            if licence != "Generated" and not source.startswith("https://commons.wikimedia.org/wiki/File:"):
                bad.append(f"{slug}: source must be a Wikimedia Commons file page")
            page = read_post(slug)["html"]
            credit = re.search(r'<p class="image-credit">(.*?)</p>', page, re.S)
            if licence.startswith("CC BY"):
                if not credit or author not in html.unescape(credit.group(1)) or licence not in credit.group(1):
                    bad.append(f"{slug}: the post must show a credit with {author!r} and {licence!r}")
        for slug in REPLACED_HEROES:
            if slug not in [r[0] for r in rows]:
                bad.append(f"{slug}: no row in docs/image-credits.md")
        self.check(bad)

    # --- audio player ----------------------------------------------------
    def test_stories_json_matches_posts(self):
        # The player reads stories.json. Run tools/build_stories.py after a post changes.
        import json
        path = SRC / "static" / "data" / "stories.json"
        self.assertTrue(path.is_file(), "run: python3 tools/build_stories.py")
        stories = json.loads(path.read_text(encoding="utf-8"))
        bad = []
        if sorted(s["slug"] for s in stories) != post_slugs():
            bad.append("stories.json does not have exactly the posts")
        if [s["slug"] for s in stories] != listed_slugs("archive.html", r'href="/posts/([a-z0-9-]+)" class="archive-card"'):
            bad.append("stories.json is not in the archive order")
        by_name = {name: slug for slug, name in GROUPS.items()}
        for story in stories:
            if story["slug"] not in post_slugs():
                continue
            post = read_post(story["slug"])
            if story["title"] != post["title"] or story["group"] != by_name.get(post["group"]):
                bad.append(f"{story['slug']}: title or group is out of date")
            if story["image"] != f"/static/images/posts/{story['slug']}/hero.webp":
                bad.append(f"{story['slug']}: image is {story['image']}")
            mp3 = SRC / "static" / "audio" / f"{story['slug']}.mp3"
            want = f"/static/audio/{story['slug']}.mp3" if mp3.is_file() else None
            if story["audio"] != want:
                bad.append(f"{story['slug']}: audio is {story['audio']}, must be {want}")
        self.check(bad)

    def test_player_assets_on_all_pages(self):
        bad = []
        for page in all_pages():
            text = page.read_text(encoding="utf-8")
            for asset in ("/static/css/player.css", "/static/js/player-core.js", "/static/js/player-ui.js"):
                if text.count(f'"{asset}"') != 1:
                    bad.append(f"{rel(page)}: {asset} is there {text.count(asset)} times")
            if text.find("player-core.js") > text.find("player-ui.js"):
                bad.append(f"{rel(page)}: player-core.js must load before player-ui.js")
            rows = re.findall(r'<div class="listen-row" data-slug="([^"]*)">', text)
            want = [page.stem] if page.parent.name == "posts" else []
            if rows != want:
                bad.append(f"{rel(page)}: listen rows {rows}, must be {want}")
        self.check(bad)

    def test_listen_page(self):
        page = SRC / "listen.html"
        self.assertTrue(page.is_file(), "src/listen.html is missing")
        text = page.read_text(encoding="utf-8")
        for needed in ('id="pm-lists"', 'id="pm-stories"', '<link rel="canonical" href="https://pastmysteries.com/listen">',
                       "<noscript>"):
            self.assertIn(needed, text)
        sitemap = (SRC / "sitemap.xml").read_text(encoding="utf-8")
        for path in ("listen", "archive"):  # the archive was missing from the sitemap before
            self.assertIn(f"<loc>https://pastmysteries.com/{path}</loc>", sitemap)

    def test_audio_files_small(self):
        # Problem we had: a 35 MB MP3 (256 kbit/s) for one story. Use tools/encode_audio.sh.
        import shutil
        import subprocess
        if not shutil.which("ffprobe"):
            self.skipTest("ffprobe is not installed")
        bad = []
        for mp3 in sorted((SRC / "static" / "audio").glob("*.mp3")):
            out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                                  "stream=channels,bit_rate", "-of", "csv=p=0", str(mp3)],
                                 capture_output=True, text=True).stdout.strip().split(",")
            channels, bit_rate = int(out[0]), int(out[1])
            if channels != 1 or bit_rate > 72000:
                bad.append(f"{mp3.name}: {channels} channel(s), {bit_rate // 1000} kbit/s (must be mono, max 72)")
            if mp3.stem not in post_slugs():
                bad.append(f"{mp3.name}: no post has this name")
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

    def test_links_between_stories_are_kept(self):
        # Problem we had: a rewrite removed all links from one story to another.
        # After a rewrite, run: python3 tools/restore_links.py <slug>
        total = sum(len(re.findall(r'<a href="/posts/', body_html(read_post(s)["html"]))) for s in post_slugs())
        self.assertGreaterEqual(total, 30, f"only {total} links between stories; a rewrite removed them")

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
