import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from replayforge.recorder import record_transcript
from replayforge.replayer import replay
from replayforge.transcript import Transcript


def fixed_model(prompt: str) -> str:
    return f"answer to: {prompt}"


def test_record_transcript_calls_model_once_per_prompt():
    prompts = ["a", "b", "c"]
    transcript = record_transcript(name="t", model_version="v1", prompts=prompts, model_fn=fixed_model)

    assert len(transcript.turns) == 3
    assert transcript.turns[0].response == "answer to: a"
    assert transcript.turns[2].response == "answer to: c"


def test_replay_reuses_same_prompts_as_baseline():
    baseline = record_transcript(name="t", model_version="v1", prompts=["a", "b"], model_fn=fixed_model)

    def different_model(prompt):
        return "changed: " + fixed_model(prompt)

    new_transcript, report = replay(baseline, new_model_version="v2", model_fn=different_model)

    assert [t.prompt for t in new_transcript.turns] == ["a", "b"]
    assert new_transcript.model_version == "v2"
    assert report.new_version == "v2"
    assert len(report.turn_diffs) == 2


def test_replay_with_identical_model_shows_no_regressions():
    baseline = record_transcript(name="t", model_version="v1", prompts=["a", "b"], model_fn=fixed_model)

    new_transcript, report = replay(baseline, new_model_version="v1-again", model_fn=fixed_model)

    assert report.regression_count == 0
    assert report.average_similarity == 1.0
