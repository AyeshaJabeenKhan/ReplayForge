"""
diff_engine.py

Compares two transcripts of the same prompts (a baseline and a replay
against a new model version), turn by turn, and flags any response
that changed enough to look like a regression.

The similarity check uses `difflib.SequenceMatcher`, part of the
Python standard library - the same tool `git diff` and many text-
comparison tools are built on. It returns a ratio from 0 (completely
different) to 1 (identical). A turn is flagged as a regression if that
ratio drops below a threshold you choose (0.7 by default - meaning
"less than 70% similar to before").

This is a simple, explainable signal on purpose: it does not try to
understand whether the *meaning* changed, only whether the *text*
changed a lot. That is an honest trade-off for a tool this size - see
the case study for the reasoning.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from .transcript import Transcript


@dataclass
class TurnDiff:
    prompt: str
    baseline_response: str
    new_response: str
    similarity: float
    is_regression: bool
    diff_lines: list[str]

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "baseline_response": self.baseline_response,
            "new_response": self.new_response,
            "similarity": round(self.similarity, 3),
            "is_regression": self.is_regression,
            "diff_lines": self.diff_lines,
        }


@dataclass
class RegressionReport:
    baseline_name: str
    baseline_version: str
    new_version: str
    similarity_threshold: float
    turn_diffs: list[TurnDiff] = field(default_factory=list)

    @property
    def regression_count(self) -> int:
        return sum(1 for d in self.turn_diffs if d.is_regression)

    @property
    def average_similarity(self) -> float:
        if not self.turn_diffs:
            return 1.0
        return sum(d.similarity for d in self.turn_diffs) / len(self.turn_diffs)

    def to_dict(self) -> dict:
        return {
            "baseline_name": self.baseline_name,
            "baseline_version": self.baseline_version,
            "new_version": self.new_version,
            "similarity_threshold": self.similarity_threshold,
            "total_turns": len(self.turn_diffs),
            "regression_count": self.regression_count,
            "average_similarity": round(self.average_similarity, 3),
            "turn_diffs": [d.to_dict() for d in self.turn_diffs],
        }


def diff_turn(prompt: str, baseline_response: str, new_response: str, similarity_threshold: float) -> TurnDiff:
    similarity = difflib.SequenceMatcher(None, baseline_response, new_response).ratio()
    is_regression = similarity < similarity_threshold

    diff_lines = list(
        difflib.unified_diff(
            baseline_response.splitlines(),
            new_response.splitlines(),
            fromfile="baseline",
            tofile="new",
            lineterm="",
        )
    )

    return TurnDiff(
        prompt=prompt,
        baseline_response=baseline_response,
        new_response=new_response,
        similarity=similarity,
        is_regression=is_regression,
        diff_lines=diff_lines,
    )


def diff_transcripts(baseline: Transcript, new: Transcript, similarity_threshold: float = 0.7) -> RegressionReport:
    """
    Compare two transcripts turn by turn, matching turns by their
    position in the list. Both transcripts are expected to hold
    responses to the *same prompts in the same order* (which is what
    `replayer.replay()` guarantees), so we check that assumption here
    rather than silently comparing mismatched turns.
    """
    if len(baseline.turns) != len(new.turns):
        raise ValueError(
            f"Transcripts have different numbers of turns "
            f"({len(baseline.turns)} vs {len(new.turns)}) - can't diff them turn by turn."
        )

    turn_diffs = []
    for baseline_turn, new_turn in zip(baseline.turns, new.turns):
        if baseline_turn.prompt != new_turn.prompt:
            raise ValueError(
                f"Prompt mismatch at the same position: {baseline_turn.prompt!r} vs {new_turn.prompt!r}. "
                f"Replays must use the exact same prompts, in the same order, as the baseline."
            )
        turn_diffs.append(
            diff_turn(baseline_turn.prompt, baseline_turn.response, new_turn.response, similarity_threshold)
        )

    return RegressionReport(
        baseline_name=baseline.name,
        baseline_version=baseline.model_version,
        new_version=new.model_version,
        similarity_threshold=similarity_threshold,
        turn_diffs=turn_diffs,
    )
