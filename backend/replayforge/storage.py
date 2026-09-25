"""
storage.py

Transcripts are saved as plain JSON files in a folder on disk - no
database needed for a tool this size. This file has the small amount
of logic for finding and listing those files, so the API and CLI don't
each reinvent it.
"""

from __future__ import annotations

from pathlib import Path

from .transcript import Transcript

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "transcripts"


def transcript_path(name: str, data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return data_dir / f"{safe_name}.json"


def save_transcript(transcript: Transcript, data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    path = transcript_path(transcript.name, data_dir)
    transcript.save(path)
    return path


def load_transcript(name: str, data_dir: Path = DEFAULT_DATA_DIR) -> Transcript:
    path = transcript_path(name, data_dir)
    if not path.exists():
        raise FileNotFoundError(f"No saved transcript named '{name}' (looked for {path})")
    return Transcript.load(path)


def list_transcripts(data_dir: Path = DEFAULT_DATA_DIR) -> list[Transcript]:
    if not data_dir.exists():
        return []
    return [Transcript.load(p) for p in sorted(data_dir.glob("*.json"))]
