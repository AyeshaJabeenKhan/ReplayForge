"""
replayer.py

Ties recorder.py and diff_engine.py together: take a baseline
transcript, run the exact same prompts through a new model version,
and produce a regression report comparing the two.

This is the main thing ReplayForge is "for" - everything else in the
package exists to support this one operation.
"""

from __future__ import annotations

from typing import Callable

from .diff_engine import RegressionReport, diff_transcripts
from .recorder import record_transcript
from .transcript import Transcript


def replay(
    baseline: Transcript,
    new_model_version: str,
    model_fn: Callable[[str], str],
    similarity_threshold: float = 0.7,
) -> tuple[Transcript, RegressionReport]:
    """
    Replay every prompt from `baseline` against `model_fn`, and diff
    the results against the baseline's original responses.

    Returns (new_transcript, report) - the new transcript is returned
    too so the caller can save it, if they want a record of this
    replay for next time.
    """
    prompts = [turn.prompt for turn in baseline.turns]
    new_transcript = record_transcript(
        name=baseline.name,
        model_version=new_model_version,
        prompts=prompts,
        model_fn=model_fn,
    )

    report = diff_transcripts(baseline, new_transcript, similarity_threshold=similarity_threshold)

    return new_transcript, report
