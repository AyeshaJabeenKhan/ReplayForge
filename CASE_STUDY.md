# Case Study: Building ReplayForge

## The problem

If your product depends on an LLM, you don't fully control the model underneath it. Providers update models, and sometimes a prompt that used to get a great answer starts getting a worse one, with no warning. The usual way teams find out is a user complaint, days or weeks after the change happened.

The fix sounds simple: before you switch to a new model, run your real prompts through it and compare the answers to what you had before. ReplayForge is a small, honest version of that idea.

## Step 1: What does a "conversation" actually need to be?

Before writing any logic, I had to decide what to actually save. I kept it as simple as it could be: a `Transcript` is just a name, a model version, and a list of `Turn`s (a prompt and its response). No conversation branching, no system prompts, no metadata beyond what's needed to compare two transcripts later.

This is a "serialization" problem in the plainest sense: turn a Python object into JSON, and turn it back later, with nothing lost in between. I wrote small `to_dict` / `from_dict` methods by hand instead of reaching for a serialization library, since the shape is simple enough that the extra dependency wouldn't pay for itself. `Transcript.save()` and `Transcript.load()` wrap this with basic file I/O, so a transcript is a plain JSON file you could open and read yourself, which matters for a tool meant to be trusted with catching real regressions.

## Step 2: Comparing two answers fairly

The core question ReplayForge answers is: "did this answer change enough to worry about?" I used `difflib.SequenceMatcher`, which is part of Python's standard library, to get a similarity ratio between 0 (nothing alike) and 1 (identical).

I picked a similarity-based approach over something like "did the length change" (which I used in an earlier project) because for this specific problem - comparing two answers to the *same* question - text similarity is a much more direct signal. Two answers can be the same length and still say completely different things; `difflib` catches that by actually looking at the shared substrings, not just a count.

I paired this with `difflib.unified_diff`, the same style of diff you see in `git diff`, so a flagged regression doesn't just say "this got worse" - it shows exactly which lines were added and removed. That distinction (a similarity *score* to decide whether something changed, and a *diff* to show what changed) mirrors how real code review tools work, and it was a deliberate choice to keep both, rather than just picking one.

## Step 3: Matching turns correctly

Diffing two transcripts only makes sense if you're comparing the response to the *same* prompt in both. I enforce this directly: `diff_transcripts()` checks that both transcripts have the same number of turns, and that the prompt at each position matches exactly, before it compares anything. If either check fails, it raises a clear error instead of quietly comparing the wrong things.

This might seem like a small detail, but it is exactly the kind of assumption that causes confusing bugs later if left unchecked - a report that says "regression detected" when actually two unrelated questions got compared to each other would be worse than no report at all.

## Step 4: Building the CLI properly

The brief for this project specifically called out CLI design, so I put real thought into it instead of writing a single script with a pile of `if` statements. `argparse` supports subcommands (`record`, `list`, `show`, `replay`), each with its own arguments and its own `--help` text - the same pattern tools like `git` and `docker` use. This means `python cli.py replay --help` shows exactly the options relevant to replaying, not a confusing list of every option the whole tool supports.

I also made sure the CLI and the API share the same underlying functions (`record_transcript`, `replay`, `diff_transcripts`) rather than each having their own copy of the logic. The CLI and the dashboard are just two different front doors into the same core package.

## Step 5: Making it demoable without an API key

Same challenge I've run into on similar projects: showing "catches a regression" convincingly usually means waiting for a real model provider to actually break something, which isn't practical for a demo.

`demo_model_v1` and `demo_model_v2` are small, honest stand-ins: `v2` matches `v1` answer-for-answer, except for one prompt where it gives a noticeably worse response. This means running the demo actually produces one real, caught regression out of several turns - not a hypothetical description of what the tool *would* do.

## Trade-offs I made on purpose

- **Text similarity, not meaning.** ReplayForge doesn't know if an answer is factually correct, only whether it looks similar to before. A model could get *more* correct and still get flagged, if the wording changed a lot. I see this as an honest, explainable limitation rather than a flaw to hide - see "what I would improve" below.
- **JSON files on disk, not a database.** For a personal tool or a small team's use, a folder of JSON files is easy to inspect, version, and back up. A real production monitoring system for dozens of models would want a database, but that's solving a different, bigger problem.
- **No support for multi-turn conversations that branch.** Each transcript is a flat list of independent prompts and responses, not a back-and-forth dialogue tree. This matches the most common real use case (a set of test questions you want to keep re-checking) without adding the complexity of tracking conversation state.

## What I would improve with more time

- Add an optional "judge" step: send both the old and new answer to an LLM and ask it whether the new one is better, worse, or equivalent - a second signal alongside the text similarity score.
- Support recording real multi-turn conversations (where turn 2 depends on the answer to turn 1), not just a flat list of independent prompts.
- Let the dashboard show a history of replays over time for the same baseline, so you can see if a model is drifting gradually rather than just checking once.

