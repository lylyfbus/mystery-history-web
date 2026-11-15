"""Check the text rules for one or more posts. Prints each problem.

Usage: python3 tools/check_text.py <slug> [<slug> ...]
Rules: docs/writing-guide.md. Compares the length with the last committed text.
"""
import re
import subprocess
import sys

from sitelib import body_html, read_post, sentences, strip_tags, word_count

MAX_PARAGRAPH, MAX_SENTENCE, MAX_MEAN = 100, 30, 18
BANNED = ["breathtaking", "masterclass", "nearly severed", "ripped open"]


def old_words(slug):
    out = subprocess.run(["git", "show", f"master:src/posts/{slug}.html"], capture_output=True, text=True).stdout
    return sum(word_count(strip_tags(p)) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", body_html(out), re.S))


def check(slug):
    problems = []
    paragraphs = read_post(slug)["paragraphs"]
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
    if mean > MAX_MEAN:
        problems.append(f"average sentence is {mean:.1f} words (max {MAX_MEAN})")
    text = " ".join(paragraphs).lower()
    problems += [f"banned phrase: {b}" for b in BANNED if b in text]
    new, old = sum(word_count(p) for p in paragraphs), old_words(slug)
    if old and not 0.70 <= new / old <= 1.10:
        problems.append(f"length is {100 * new // old}% of the old text ({new} of {old} words); must be 70% to 110%")
    print(f"{'OK  ' if not problems else 'FAIL'} {slug}: {len(paragraphs)} paragraphs, {new} words "
          f"({100 * new // max(old, 1)}% of old), average sentence {mean:.1f} words")
    for p in problems:
        print(f"     - {p}")
    return not problems


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    results = [check(slug) for slug in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
