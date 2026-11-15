"""Build src/static/data/stories.json: the list of stories that the audio player reads.

Run this after a post is added, renamed, moved to a different group, or gets an MP3.
"""
import json
import shutil
import subprocess

from sitelib import GROUPS, SRC, listed_slugs, post_slugs, read_post, write


def duration(path):
    if not shutil.which("ffprobe"):
        return None
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    try:
        return round(float(out))
    except ValueError:
        return None


def build():
    by_name = {name: slug for slug, name in GROUPS.items()}
    order = listed_slugs("archive.html", r'href="/posts/([a-z0-9-]+)" class="archive-card"')
    order += [s for s in post_slugs() if s not in order]
    stories = []
    for slug in order:
        post = read_post(slug)
        mp3 = SRC / "static" / "audio" / f"{slug}.mp3"
        stories.append({
            "slug": slug,
            "title": post["title"],
            "group": by_name[post["group"]],
            "image": f"/static/images/posts/{slug}/hero.webp",
            "audio": f"/static/audio/{slug}.mp3" if mp3.is_file() else None,
            "duration": duration(mp3) if mp3.is_file() else None,
        })
    return stories


if __name__ == "__main__":
    stories = build()
    path = SRC / "static" / "data" / "stories.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, json.dumps(stories, ensure_ascii=False, indent=1) + "\n")
    print(f"stories.json: {len(stories)} stories, {sum(1 for s in stories if s['audio'])} with MP3")
