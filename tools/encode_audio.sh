#!/bin/sh
# Make a small MP3 for the site: mono, 64 kbit/s (about 8 MB for 18 minutes).
# Usage: tools/encode_audio.sh <input-audio-file> <post-slug>
set -e
[ $# -eq 2 ] || { echo "Usage: $0 <input-audio-file> <post-slug>"; exit 1; }
root="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$root/src/posts/$2.html" ] || { echo "No post with the name $2"; exit 1; }
out="$root/src/static/audio/$2.mp3"
tmp="$out.tmp.mp3"
ffmpeg -v error -y -i "$1" -ac 1 -ar 44100 -b:a 64k "$tmp"
mv "$tmp" "$out"
python3 "$root/tools/build_stories.py"
ls -lh "$out"
