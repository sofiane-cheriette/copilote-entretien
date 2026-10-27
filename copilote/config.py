import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


BASE_DIR = _base_dir()
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USER_NAME = os.getenv("USER_NAME", "le candidat")
GEMINI_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_MODELS",
        "gemini-3.6-flash,gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite",
    ).split(",")
    if m.strip()
]
RMS_THRESHOLD = int(os.getenv("RMS_THRESHOLD", "350"))
SILENCE_SEC = float(os.getenv("SILENCE_SEC", "1.0"))
MIN_SPEECH_SEC = float(os.getenv("MIN_SPEECH_SEC", "0.7"))
MAX_SEGMENT_SEC = float(os.getenv("MAX_SEGMENT_SEC", "25"))
FONT_SIZE = int(os.getenv("FONT_SIZE", "22"))
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "6"))

CV_PATH = BASE_DIR / "cv.txt"
CONTEXTE_PATH = BASE_DIR / "contexte.txt"
SESSIONS_DIR = BASE_DIR / "sessions"
