import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from replayforge.transcript import Transcript, Turn


def test_turn_round_trips_through_dict():
    turn = Turn(prompt="hi", response="hello")
    rebuilt = Turn.from_dict(turn.to_dict())
    assert rebuilt == turn


def test_transcript_round_trips_through_dict():
    transcript = Transcript(name="t1", model_version="v1", turns=[Turn("a", "b"), Turn("c", "d")])
    rebuilt = Transcript.from_dict(transcript.to_dict())

    assert rebuilt.name == transcript.name
    assert rebuilt.model_version == transcript.model_version
    assert rebuilt.turns == transcript.turns


def test_transcript_save_and_load_round_trip(tmp_path):
    transcript = Transcript(name="t1", model_version="v1", turns=[Turn("a", "b")])
    path = tmp_path / "t1.json"

    transcript.save(path)
    loaded = Transcript.load(path)

    assert loaded.name == "t1"
    assert loaded.model_version == "v1"
    assert loaded.turns == [Turn("a", "b")]


def test_save_creates_parent_directories(tmp_path):
    transcript = Transcript(name="t1", model_version="v1")
    path = tmp_path / "nested" / "dir" / "t1.json"

    transcript.save(path)

    assert path.exists()
