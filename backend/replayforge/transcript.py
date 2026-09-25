"""
transcript.py

A Transcript is a saved record of a conversation: one model version,
a list of prompts, and the response each prompt got. This is the
thing ReplayForge records once (the "baseline"), and later replays
against a new model version to check for regressions.

This file handles turning a Transcript into plain JSON and back
(serialization), so transcripts can be saved to disk and loaded again
later - the same shape every time, whether it just came from a live
model call or was loaded from a file recorded last week.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Turn:
    prompt: str
    response: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Turn":
        return cls(prompt=data["prompt"], response=data["response"])


@dataclass
class Transcript:
    name: str
    model_version: str
    turns: list[Turn] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "model_version": self.model_version,
            "created_at": self.created_at,
            "turns": [t.to_dict() for t in self.turns],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transcript":
        return cls(
            name=data["name"],
            model_version=data["model_version"],
            created_at=data.get("created_at", ""),
            turns=[Turn.from_dict(t) for t in data.get("turns", [])],
        )

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "Transcript":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)
