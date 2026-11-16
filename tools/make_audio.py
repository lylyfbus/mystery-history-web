"""Make the recorded voice (MP3) for stories with the local Kokoro model.

Usage:  tools/make_audio.sh <slug> [<slug> ...]     or     tools/make_audio.sh --all [--force]

Run it through tools/make_audio.sh, which sets the Python folder and the model folder.
A story is skipped when its MP3 already matches the page text (see src/static/audio/manifest.json).
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from audio_text import speech_blocks, text_hash, word_count
from sitelib import SRC, post_slugs

MODEL = "mlx-community/Kokoro-82M-bf16"
VOICE = "am_michael"
SPEED = 1.0
PAUSE = {"title": 1.2, "h2": 0.9, "p": 0.55}   # seconds of silence after each kind of block
BEFORE_H2 = 0.6                                 # extra silence before a section title
AUDIO = SRC / "static" / "audio"
MANIFEST = AUDIO / "manifest.json"


def voice_file():
    from huggingface_hub import snapshot_download
    return str(Path(snapshot_download(MODEL, local_files_only=True)) / "voices" / f"{VOICE}.safetensors")


def make(model, voice, slug):
    rate = model.sample_rate
    parts = []
    for kind, text in speech_blocks(slug):
        if kind == "h2":
            parts.append(np.zeros(int(rate * BEFORE_H2), dtype=np.float32))
        for result in model.generate(text=text, voice=voice, speed=SPEED, lang_code="a"):
            parts.append(np.asarray(result.audio, dtype=np.float32).reshape(-1))
        parts.append(np.zeros(int(rate * PAUSE[kind]), dtype=np.float32))
    audio = np.concatenate(parts)
    out = AUDIO / f"{slug}.mp3"
    with tempfile.NamedTemporaryFile(suffix=".wav") as wav:
        sf.write(wav.name, audio, rate)
        tmp = out.with_suffix(".tmp.mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav.name, "-ac", "1", "-ar", "44100", "-b:a", "64k", str(tmp)], check=True)
        tmp.replace(out)
    return len(audio) / rate


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    slugs = post_slugs() if "--all" in sys.argv else args
    if not slugs:
        raise SystemExit(__doc__)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
    from mlx_audio.tts.utils import load_model
    model, voice = load_model(MODEL), voice_file()
    for i, slug in enumerate(sorted(slugs), 1):
        want = text_hash(slug)
        if not force and manifest.get(slug, {}).get("text") == want and (AUDIO / f"{slug}.mp3").is_file():
            print(f"[{i}/{len(slugs)}] {slug}: up to date")
            continue
        start = time.time()
        seconds = make(model, voice, slug)
        words = word_count(slug)
        manifest[slug] = {"text": want, "voice": f"kokoro {VOICE}", "seconds": round(seconds), "words": words}
        MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=1) + "\n", encoding="utf-8")
        print(f"[{i}/{len(slugs)}] {slug}: {seconds / 60:.1f} min, {words / seconds * 60:.0f} words a minute, made in {time.time() - start:.0f} s", flush=True)
