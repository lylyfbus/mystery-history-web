"""Check the text rules for one or more posts. Prints each problem.

Usage: python3 tools/check_text.py <slug> [<slug> ...]
Rules: docs/writing-guide.md.
"""
import re
import sys

from sitelib import body_html, read_post, sentences, strip_tags, word_count

MAX_PARAGRAPH, MAX_SENTENCE = 100, 30
MEAN_RANGE, WORD_RANGE, TITLE_RANGE = (9, 15), (1100, 1600), (6, 8)
BANNED = ["breathtaking", "masterclass", "nearly severed", "ripped open"]


def check(slug):
    problems = []
    post = read_post(slug)
    body = body_html(post["html"])
    paragraphs = post["paragraphs"]
    titles = [strip_tags(t) for t in re.findall(r"<h2\b[^>]*>(.*?)</h2>", body, re.S)]
    if not TITLE_RANGE[0] <= len(titles) <= TITLE_RANGE[1]:
        problems.append(f"{len(titles)} section titles; {TITLE_RANGE[0]} to {TITLE_RANGE[1]} are necessary")
    if not re.match(r"\s*<h2\b", body):
        problems.append("the story must start with a section title")
    if re.search(r"</h2>\s*<h2\b", body):
        problems.append("a section title has no text below it")
    for title in titles:
        if word_count(title) > 8:
            problems.append(f"section title has more than 8 words: {title}")
    lengths = []
    for i, para in enumerate(paragraphs, 1):
        if word_count(para) > MAX_PARAGRAPH:
            problems.append(f"paragraph {i} has {word_count(para)} words (max {MAX_PARAGRAPH}): {para[:60]}...")
        for sentence in sentences(para):
            n = word_count(sentence)
            lengths.append(n)
            if n > MAX_SENTENCE:
                problems.append(f"sentence has {n} words (max {MAX_SENTENCE}): {sentence[:80]}...")
    mean = sum(lengths) / max(len(lengths), 1)
    if not MEAN_RANGE[0] <= mean <= MEAN_RANGE[1]:
        problems.append(f"average sentence is {mean:.1f} words; must be {MEAN_RANGE[0]} to {MEAN_RANGE[1]}")
    text = " ".join(paragraphs).lower()
    problems += [f"banned phrase: {b}" for b in BANNED if b in text]
    words = sum(word_count(p) for p in paragraphs)
    if not WORD_RANGE[0] <= words <= WORD_RANGE[1]:
        problems.append(f"{words} words; must be {WORD_RANGE[0]} to {WORD_RANGE[1]}")
    print(f"{'OK  ' if not problems else 'FAIL'} {slug}: {len(titles)} titles, {len(paragraphs)} paragraphs, "
          f"{words} words, average sentence {mean:.1f} words")
    for p in problems:
        print(f"     - {p}")
    return not problems


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    results = [check(slug) for slug in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
