"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function DiffLines({ lines }) {
  if (!lines || lines.length === 0) {
    return <div className="similarity-note">No text differences.</div>;
  }
  return (
    <div className="diff-lines">
      {lines.map((line, i) => {
        let cls = "context";
        if (line.startsWith("+") && !line.startsWith("+++")) cls = "added";
        else if (line.startsWith("-") && !line.startsWith("---")) cls = "removed";
        return (
          <div className={`diff-line ${cls}`} key={i}>
            {line}
          </div>
        );
      })}
    </div>
  );
}

export default function Home() {
  const [name, setName] = useState("baseline");
  const [transcripts, setTranscripts] = useState([]);
  const [replayVersion, setReplayVersion] = useState("v2");
  const [threshold, setThreshold] = useState(0.7);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [recording, setRecording] = useState(false);
  const [replaying, setReplaying] = useState(false);

  async function loadTranscripts() {
    try {
      const res = await fetch(`${API_URL}/transcripts`);
      const data = await res.json();
      setTranscripts(data);
    } catch (err) {
      // non-fatal, just means the list stays empty
    }
  }

  useEffect(() => {
    loadTranscripts();
  }, []);

  async function handleRecord(e) {
    e.preventDefault();
    setError("");
    setRecording(true);
    try {
      const res = await fetch(`${API_URL}/transcripts/record`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, model_version: "v1" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Recording failed.");
      await loadTranscripts();
    } catch (err) {
      setError(err.message === "Failed to fetch" ? "Could not reach the API at " + API_URL : err.message);
    } finally {
      setRecording(false);
    }
  }

  async function handleReplay(e) {
    e.preventDefault();
    setError("");
    setReport(null);
    setReplaying(true);
    try {
      const res = await fetch(`${API_URL}/replay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_name: name,
          model_version: replayVersion,
          similarity_threshold: Number(threshold),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Replay failed.");
      setReport(data);
    } catch (err) {
      setError(err.message === "Failed to fetch" ? "Could not reach the API at " + API_URL : err.message);
    } finally {
      setReplaying(false);
    }
  }

  return (
    <div className="page">
      <div className="header">
        <h1>ReplayForge</h1>
        <p>Record a baseline conversation, replay it against a new model version, and see exactly what changed.</p>
      </div>

      <form className="card" onSubmit={handleRecord}>
        <h2>1. Record a baseline</h2>
        <div className="field">
          <label>Transcript name</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="actions">
          <button className="primary" type="submit" disabled={recording}>
            {recording ? "Recording..." : "Record baseline (v1)"}
          </button>
        </div>
      </form>

      <div className="card">
        <h2>2. Saved transcripts</h2>
        {transcripts.length === 0 ? (
          <div className="empty-state">No transcripts yet. Record one above.</div>
        ) : (
          <div className="transcript-list">
            {transcripts.map((t) => (
              <span className="transcript-chip" key={t.name}>
                <b>{t.name}</b> &middot; {t.model_version} &middot; {t.turns} turns
              </span>
            ))}
          </div>
        )}
      </div>

      <form className="card" onSubmit={handleReplay}>
        <h2>3. Replay against a new model version</h2>
        <div className="settings-grid">
          <div className="field">
            <label>New model version</label>
            <select value={replayVersion} onChange={(e) => setReplayVersion(e.target.value)}>
              <option value="v2">v2 (has one injected regression)</option>
              <option value="v1">v1 (identical to baseline)</option>
            </select>
          </div>
          <div className="field">
            <label>Similarity threshold</label>
            <input type="number" step="0.05" min="0" max="1" value={threshold} onChange={(e) => setThreshold(e.target.value)} />
          </div>
        </div>
        <div className="actions">
          <button className="primary" type="submit" disabled={replaying}>
            {replaying ? "Replaying..." : "Run replay"}
          </button>
        </div>

        {error && <div className="error-box">{error}</div>}
      </form>

      {report && (
        <div className="card">
          <h2>Regression report</h2>
          <div className="summary-row">
            <div className="summary-item">
              <div className="value">{report.total_turns}</div>
              <div className="label">Turns</div>
            </div>
            <div className="summary-item">
              <div className="value">{report.regression_count}</div>
              <div className="label">Regressions</div>
            </div>
            <div className="summary-item">
              <div className="value">{(report.average_similarity * 100).toFixed(0)}%</div>
              <div className="label">Avg similarity</div>
            </div>
          </div>

          {report.turn_diffs.map((diff, i) => (
            <div className={`turn-diff ${diff.is_regression ? "regression" : ""}`} key={i}>
              <div className="turn-top">
                <p className="turn-prompt">{diff.prompt}</p>
                {diff.is_regression ? (
                  <span className="badge regression">regression</span>
                ) : (
                  <span className="badge ok">ok</span>
                )}
              </div>
              <div className="similarity-note">similarity: {(diff.similarity * 100).toFixed(0)}%</div>
              <DiffLines lines={diff.diff_lines} />
            </div>
          ))}
        </div>
      )}

      <div className="footer-note">
        ReplayForge: A project for catching LLM regressions before you ship a model upgrade.
      </div>
    </div>
  );
}
