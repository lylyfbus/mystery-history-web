"""Put back the links between stories that were in the old text of a post.

Usage: python3 tools/restore_links.py <slug> [<slug> ...]
For each link in the old story text (branch master), find the same words in the
new text and make them a link again. One link for each target. Safe to run again.
"""
import html
import re
import subprocess
import sys

from sitelib import SRC, body_html, post_slugs, read_post, write


def old_links(slug):
    old = subprocess.run(["git", "show", f"master:src/posts/{slug}.html"], capture_output=True, text=True).stdout
    return re.findall(r'<a href="(/posts/[a-z0-9-]+)"[^>]*>(.*?)</a>', body_html(old), re.S)


def restore(slug):
    page = read_post(slug)["html"]
    body = body_html(page)
    new_body, done, missed = body, [], []
    for href, anchor in old_links(slug):
        target = href.rsplit("/", 1)[1]
        if target not in post_slugs() or target == slug:
            continue
        if f'href="{href}"' in new_body:
            continue
        words = re.sub(r"<[^>]+>", "", anchor).strip()
        # try the old words, then shorter forms ("the Roswell incident" -> "Roswell")
        tries = [words] + [w for w in re.findall(r"[A-Z][\wÀ-ſ]+(?: [A-Z][\wÀ-ſ]+)*", html.unescape(words))]
        for text in tries:
            pattern = re.compile(r"(?<![\w>/\"-])" + re.escape(text) + r"(?![\w<\"-])")
            match = None
            for m in pattern.finditer(new_body):
                before = new_body[:m.start()]
                if before.count("<a ") == before.count("</a>") and before.rfind("<") <= before.rfind(">"):
                    match = m
                    break
            if match:
                new_body = new_body[:match.start()] + f'<a href="{href}">{text}</a>' + new_body[match.end():]
                done.append(f"{text} -> {href}")
                break
        else:
            missed.append(f"{words} -> {href}")
    if new_body != body:
        write(SRC / "posts" / f"{slug}.html", page.replace(body, new_body))
    for d in done:
        print(f"{slug}: linked {d}")
    for m in missed:
        print(f"{slug}: NOT FOUND {m}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for s in sys.argv[1:]:
        restore(s)
