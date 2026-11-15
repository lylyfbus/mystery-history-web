"""Shared helpers for the site tools. Read helpers come from tests/site_lib.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from site_lib import *  # noqa: F401,F403,E402
from site_lib import SRC, ROOT  # noqa: F401,E402


def write(path, text):
    Path(path).write_text(text, encoding="utf-8")
