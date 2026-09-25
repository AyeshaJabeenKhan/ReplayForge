"""
api.py

A small FastAPI app that lets the Next.js dashboard record a baseline,
list saved transcripts, and run a replay to get a regression report.

Run it with:
    uvicorn api:app --reload --port 8000

Note on the demo models: to keep this project runnable with zero setup
(no API key required), this API uses `demo_model_v1` and
`demo_model_v2` from replayforge/demo_model.py as stand-ins for a real
"before" and "after" LLM. Swap in your own functions that call a real
model for real use - see the README.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

configure_logging()

app = FastAPI(title="ReplayForge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_MODEL_FNS = {"v1": demo_model_v1, "v2": demo_model_v2}


class RecordRequest(BaseModel):
    name: str = Field(..., min_length=1)
    model_version: str = Field("v1")


class ReplayRequest(BaseModel):
    baseline_name: str = Field(..., min_length=1)
    model_version: str = Field("v2")
    similarity_threshold: float = Field(0.7, ge=0, le=1)
    save_as: str | None = None


def _resolve_model_fn(version: str):
    if version not in _MODEL_FNS:
        raise HTTPException(status_code=400, detail=f"Unknown model version '{version}'. Available: {list(_MODEL_FNS)}")
    return _MODEL_FNS[version]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/prompts")
def default_prompts() -> list:
    return DEMO_PROMPTS


@app.get("/transcripts")
def list_all_transcripts() -> list:
    return [
        {"name": t.name, "model_version": t.model_version, "turns": len(t.turns), "created_at": t.created_at}
        for t in list_transcripts()
    ]


@app.get("/transcripts/{name}")
def get_transcript(name: str) -> dict:
    try:
        transcript = load_transcript(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return transcript.to_dict()


@app.post("/transcripts/record")
def record(request: RecordRequest) -> dict:
    model_fn = _resolve_model_fn(request.model_version)
    transcript = record_transcript(
        name=request.name,
        model_version=request.model_version,
        prompts=DEMO_PROMPTS,
        model_fn=model_fn,
    )
    save_transcript(transcript)
    return transcript.to_dict()


@app.post("/replay")
def run_replay(request: ReplayRequest) -> dict:
    try:
        baseline = load_transcript(request.baseline_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    model_fn = _resolve_model_fn(request.model_version)

    new_transcript, report = replay(
        baseline=baseline,
        new_model_version=request.model_version,
        model_fn=model_fn,
        similarity_threshold=request.similarity_threshold,
    )

    if request.save_as:
        new_transcript.name = request.save_as
        save_transcript(new_transcript)

    return report.to_dict()
