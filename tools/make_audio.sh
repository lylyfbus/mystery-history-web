#!/bin/sh
# Make story MP3s with the local Kokoro voice. See tools/make_audio.py.
# Needs: ../audio/kokoro-venv (misaki, spacy, espeakng-loader) and the Kokoro model in the local model folder.
set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
venv="${KOKORO_VENV:-$(cd "$root/../audio/kokoro-venv" && pwd)}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-$HOME/.helix/services/local-model-service/models}"
export HF_HUB_OFFLINE=1
cd "$root/tools"
"$venv/bin/python" make_audio.py "$@" 2>&1 | grep -v "^WARNING\|Creating new KokoroPipeline"
python3 build_stories.py
