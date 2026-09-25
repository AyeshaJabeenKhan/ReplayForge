"""
demo_model.py

ReplayForge is meant to sit in front of *any* function that returns
text for a prompt - normally a real call to an LLM API, once for your
current model and again after an upgrade. To keep this project
runnable by anyone with zero setup (no API key required), this file
provides two small stand-in model versions:

    - demo_model_v1: a stable, "before the upgrade" model.
    - demo_model_v2: the "after the upgrade" model - answers the same
      way as v1 for most prompts, but has one deliberately degraded
      answer, so replaying against it actually catches a regression.

In a real deployment, you would replace these with your own functions
that call your LLM provider before and after a model upgrade. Nothing
else in ReplayForge (transcript, recorder, diff_engine, replayer) needs
to change for that swap.
"""

from __future__ import annotations

_ANSWERS_V1 = {
    "what is the capital of france?": "The capital of France is Paris.",
    "what is your refund policy?": "Our refund policy allows returns within 30 days of purchase.",
    "summarize: the quick brown fox jumps over the lazy dog.": "A fast fox jumps over a sleepy dog.",
}

# v2 matches v1 everywhere except the refund policy answer, which has
# regressed into a useless non-answer - this is the "silent model
# update broke something" scenario ReplayForge exists to catch.
_ANSWERS_V2 = {
    **_ANSWERS_V1,
    "what is your refund policy?": "Sorry, I can't help with that.",
}


def _lookup(prompt: str, answers: dict) -> str:
    return answers.get(prompt.strip().lower(), "I don't have an answer for that.")


def demo_model_v1(prompt: str) -> str:
    """The 'before' model - stable, known-good answers."""
    return _lookup(prompt, _ANSWERS_V1)


def demo_model_v2(prompt: str) -> str:
    """The 'after' model - identical to v1, except for one regressed answer."""
    return _lookup(prompt, _ANSWERS_V2)


DEMO_PROMPTS = [
    "What is the capital of France?",
    "What is your refund policy?",
    "Summarize: The quick brown fox jumps over the lazy dog.",
]
