import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from replayforge.diff_engine import diff_transcripts, diff_turn
from replayforge.transcript import Transcript, Turn


def test_identical_responses_have_similarity_one():
    diff = diff_turn("prompt", "same answer", "same answer", similarity_threshold=0.7)
    assert diff.similarity == 1.0
    assert diff.is_regression is False
    assert diff.diff_lines == []


def test_completely_different_responses_flagged_as_regression():
    diff = diff_turn("prompt", "The capital of France is Paris.", "Sorry, I can't help with that.", similarity_threshold=0.7)
    assert diff.similarity < 0.7
    assert diff.is_regression is True
    assert len(diff.diff_lines) > 0


def test_minor_wording_change_not_flagged_as_regression():
    diff = diff_turn(
        "prompt",
        "Our refund policy allows returns within 30 days.",
        "Our refund policy allows returns within 30 days of purchase.",
        similarity_threshold=0.7,
    )
    assert diff.is_regression is False


def test_diff_transcripts_matches_turns_by_position():
    baseline = Transcript(name="t", model_version="v1", turns=[Turn("q1", "a1"), Turn("q2", "a2")])
    new = Transcript(name="t", model_version="v2", turns=[Turn("q1", "a1"), Turn("q2", "different")])

    report = diff_transcripts(baseline, new, similarity_threshold=0.7)

    assert len(report.turn_diffs) == 2
    assert report.regression_count == 1


def test_diff_transcripts_raises_on_turn_count_mismatch():
    baseline = Transcript(name="t", model_version="v1", turns=[Turn("q1", "a1")])
    new = Transcript(name="t", model_version="v2", turns=[Turn("q1", "a1"), Turn("q2", "a2")])

    with pytest.raises(ValueError):
        diff_transcripts(baseline, new)


def test_diff_transcripts_raises_on_prompt_mismatch():
    baseline = Transcript(name="t", model_version="v1", turns=[Turn("q1", "a1")])
    new = Transcript(name="t", model_version="v2", turns=[Turn("different question", "a1")])

    with pytest.raises(ValueError):
        diff_transcripts(baseline, new)


def test_report_average_similarity_with_no_turns():
    report = diff_transcripts(
        Transcript(name="t", model_version="v1", turns=[]),
        Transcript(name="t", model_version="v2", turns=[]),
    )
    assert report.average_similarity == 1.0
    assert report.regression_count == 0
