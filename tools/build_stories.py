"""Build src/static/data/stories.json: the list of stories that the audio player reads.

Run this after a post is added, renamed, moved to a different group, or gets an MP3.
"""
import json
import shutil
import subprocess

from sitelib import GROUPS, ROOT, SRC, listed_slugs, post_dates, post_slugs, read_post, write


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
    dates = post_dates()
    years = json.loads((ROOT / "tools" / "story_years.json").read_text(encoding="utf-8"))
    views = json.loads((ROOT / "tools" / "views.json").read_text(encoding="utf-8"))
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
            "added": dates[slug]["iso"],           # sort: added time
            "year": years[slug]["year"],           # sort: story time (a year before the year 1 is negative)
            "when": years[slug]["label"],          # the text that a card shows for the story time
            "views": views.get(slug),              # sort: number of views (None = no number yet)
        })
    return stories


if __name__ == "__main__":
    stories = build()
    path = SRC / "static" / "data" / "stories.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, json.dumps(stories, ensure_ascii=False, indent=1) + "\n")
    print(f"stories.json: {len(stories)} stories, {sum(1 for s in stories if s['audio'])} with MP3")
