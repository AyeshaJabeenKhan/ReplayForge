"""
cli.py

A subcommand-based CLI for ReplayForge, built with argparse.

    python cli.py record --name baseline --model-version v1
    python cli.py list
    python cli.py show baseline
    python cli.py replay --baseline baseline --model-version v2

Each subcommand has its own arguments and its own help text
(`python cli.py record --help`), which is the normal way real CLIs
like `git` or `docker` are put together - one parser per subcommand,
all sharing one entry point.
"""

from __future__ import annotations

import argparse
import json

from replayforge import (
    configure_logging,
    demo_model_v1,
    demo_model_v2,
    list_transcripts,
    load_transcript,
    record_transcript,
    replay,
    save_transcript,
)
from replayforge.demo_model import DEMO_PROMPTS

_MODEL_FNS = {"v1": demo_model_v1, "v2": demo_model_v2}


def _resolve_model_fn(version: str):
    if version not in _MODEL_FNS:
        raise SystemExit(
            f"Unknown model version '{version}'. This demo only ships 'v1' and 'v2' - "
            f"see the README for how to plug in a real model."
        )
    return _MODEL_FNS[version]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replayforge",
        description="Record LLM conversation transcripts and replay them against a new model version to catch regressions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record", help="Record a new baseline transcript")
    record_parser.add_argument("--name", required=True, help="Name to save this transcript under")
    record_parser.add_argument("--model-version", default="v1", choices=list(_MODEL_FNS), help="Which demo model to record against (default: v1)")

    subparsers.add_parser("list", help="List all saved transcripts")

    show_parser = subparsers.add_parser("show", help="Print a saved transcript's prompts and responses")
    show_parser.add_argument("name", help="Name of the transcript to show")

    replay_parser = subparsers.add_parser("replay", help="Replay a baseline transcript against a new model version")
    replay_parser.add_argument("--baseline", required=True, help="Name of the saved baseline transcript to replay")
    replay_parser.add_argument("--model-version", default="v2", choices=list(_MODEL_FNS), help="Which demo model to replay against (default: v2)")
    replay_parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold below which a turn counts as a regression (default: 0.7)")
    replay_parser.add_argument("--save-as", default=None, help="Optionally save the new transcript under this name")
    replay_parser.add_argument("--json", action="store_true", help="Print the full JSON report instead of a readable summary")

    return parser


def cmd_record(args) -> int:
    model_fn = _resolve_model_fn(args.model_version)
    transcript = record_transcript(
        name=args.name,
        model_version=args.model_version,
        prompts=DEMO_PROMPTS,
        model_fn=model_fn,
    )
    path = save_transcript(transcript)
    print(f"Recorded {len(transcript.turns)} turns as '{args.name}' ({args.model_version}) -> {path}")
    return 0


def cmd_list(args) -> int:
    transcripts = list_transcripts()
    if not transcripts:
        print("No transcripts recorded yet. Try: python cli.py record --name baseline")
        return 0

    for t in transcripts:
        print(f"{t.name:<20} version={t.model_version:<6} turns={len(t.turns):<3} recorded_at={t.created_at}")
    return 0


def cmd_show(args) -> int:
    transcript = load_transcript(args.name)
    print(f"Transcript: {transcript.name} (version {transcript.model_version})\n")
    for i, turn in enumerate(transcript.turns, start=1):
        print(f"[{i}] Q: {turn.prompt}")
        print(f"    A: {turn.response}\n")
    return 0


def cmd_replay(args) -> int:
    baseline = load_transcript(args.baseline)
    model_fn = _resolve_model_fn(args.model_version)

    new_transcript, report = replay(
        baseline=baseline,
        new_model_version=args.model_version,
        model_fn=model_fn,
        similarity_threshold=args.threshold,
    )

    if args.save_as:
        new_transcript.name = args.save_as
        save_transcript(new_transcript)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    print(f"Replaying '{args.baseline}' ({report.baseline_version}) against {report.new_version}\n")
    for i, diff in enumerate(report.turn_diffs, start=1):
        flag = "REGRESSION" if diff.is_regression else "ok"
        print(f"[{i}] similarity={diff.similarity:.2f} -> {flag}")
        print(f"    Q: {diff.prompt}")
        print(f"    baseline: {diff.baseline_response}")
        print(f"    new:      {diff.new_response}\n")

    print(f"{report.regression_count} regression(s) out of {len(report.turn_diffs)} turns "
          f"(average similarity {report.average_similarity:.2f})")
    return 0


def main(argv=None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = {
        "record": cmd_record,
        "list": cmd_list,
        "show": cmd_show,
        "replay": cmd_replay,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
