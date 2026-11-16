"""The text that the recorded voice reads for a story, and a hash of it.

The site test uses text_hash() to find an MP3 that no longer matches its page.
tools/make_audio.py uses speech_blocks() to make the MP3.
"""
import hashlib
import html
import json
import re
from pathlib import Path

from sitelib import SRC, body_html, read_post

LEXICON = json.loads((Path(__file__).parent / "audio_lexicon.json").read_text(encoding="utf-8"))
ONES = "zero one two three four five six seven eight nine ten eleven twelve".split()
TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty"}
TEENS = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
UNITS = {"km": "kilometers", "mm": "millimeters", "cm": "centimeters", "kg": "kilograms", "mph": "miles per hour",
         "Hz": "hertz", "kHz": "kilohertz", "MHz": "megahertz", "°C": "degrees Celsius", "°F": "degrees Fahrenheit"}


def blocks(slug):
    """[(kind, text)] with kind 'title', 'h2' or 'p'. Plain text, no markup."""
    stories = json.loads((SRC / "static" / "data" / "stories.json").read_text(encoding="utf-8"))
    title = next(s["title"] for s in stories if s["slug"] == slug)
    out = [("title", title)]
    body = body_html(read_post(slug)["html"])
    for tag, inner in re.findall(r"<(p|h2)\b[^>]*>(.*?)</(?:p|h2)>", body, re.S):
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", "", inner)).split())
        if text:
            out.append((tag, text))
    return out


def text_hash(slug):
    return hashlib.sha256(json.dumps(blocks(slug), ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def word_count(slug):
    return sum(len(t.split()) for _, t in blocks(slug))


def _minutes(m):
    m = int(m)
    if m < 10:
        return "oh " + ONES[m]
    if m < 20:
        return TEENS[m - 10]
    return TENS[m // 10] + ("" if m % 10 == 0 else " " + ONES[m % 10])


def _clock(match):
    hour, minute = int(match.group(1)), match.group(2)
    if hour > 12:
        return match.group(0)
    return ONES[hour] + (" o'clock" if minute == "00" else " " + _minutes(minute))


def for_speech(text, lexicon=True):
    """Change text so that the voice reads times, ranges, units and hard names correctly."""
    text = re.sub(r"\b(\d{1,2}):([0-5]\d)\b", _clock, text)
    text = re.sub(r"o'clock (AM|PM|a\.m\.|p\.m\.)", r"\1", text)
    text = re.sub(r"(?<=\d)\s?[–-]\s?(?=\d)", " to ", text)
    text = re.sub(r"(?<=\d)\s?(km|mm|cm|kg|mph|kHz|MHz|Hz|°C|°F)(?![A-Za-z])", lambda m: " " + UNITS[m.group(1)], text)
    text = re.sub(r"\bSt\. (?=[A-Z])", "Saint ", text)
    text = re.sub(r"\bJr\.", "Junior", text)
    text = text.replace(" & ", " and ").replace("6EQUJ5", "six, E, Q, U, J, five")
    text = text.replace("—", ", ").replace("…", ".")
    if lexicon:
        for word, sounds in LEXICON.items():
            text = re.sub(r"(?<![\w\[])" + re.escape(word) + r"(?![\w\]])", f"[{word}](/{sounds}/)", text)
    return text


def speech_blocks(slug):
    out = []
    for kind, text in blocks(slug):
        if kind != "p" and text[-1] not in ".?!":
            text += "."
        out.append((kind, for_speech(text)))
    return out
