"""Turn a local file into text the agent can read."""
from pathlib import Path

import pandas as pd

import models

MAX_CHARS = 15_000

TEXT_SUFFIXES = {".py", ".txt", ".csv", ".json", ".jsonl", ".md", ".xml", ".html"}
EXCEL_SUFFIXES = {".xlsx", ".xls"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}


def _truncate(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return text
    return text[:MAX_CHARS] + f"\n[truncated: {len(text)} characters in total]"


def _read_excel(path: Path) -> str:
    sheets = pd.read_excel(path, sheet_name=None)
    return "\n\n".join(f"Sheet '{name}':\n{df.to_csv(index=False)}" for name, df in sheets.items())


def read_file(path: Path, instruction: str) -> str:
    """Return the content of `path` as text.

    `instruction` says what to look for; only images use it (it is the question for the
    vision model).
    """
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _truncate(path.read_text(errors="replace"))
    if suffix in EXCEL_SUFFIXES:
        return _truncate(_read_excel(path))
    if suffix in IMAGE_SUFFIXES:
        return models.describe_image(path, instruction)
    if suffix in AUDIO_SUFFIXES:
        return _truncate(models.transcribe_audio(path))
    return f"Unsupported file type '{suffix}'."
