"""
recorder.py

Turns a list of prompts and a "model function" into a Transcript, by
simply calling the model once per prompt and keeping the result. This
is used twice in ReplayForge: once to record the original baseline,
and again (with a different model function/version) to record what a
new model version says to the exact same prompts, before diffing the
two.
"""

from __future__ import annotations

from typing import Callable

from .transcript import Transcript, Turn


def record_transcript(
    name: str,
    model_version: str,
    prompts: list[str],
    model_fn: Callable[[str], str],
) -> Transcript:
    """Call `model_fn` once per prompt and collect the results into a Transcript."""
    turns = [Turn(prompt=prompt, response=model_fn(prompt)) for prompt in prompts]
    return Transcript(name=name, model_version=model_version, turns=turns)
