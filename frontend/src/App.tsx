import { FormEvent, useState } from "react";

import { generateChallenge, gradeChallenge, type Challenge, type GradeResult } from "./api";
import { readProgress, recordOutcome } from "./progress";
import "./App.css";

type State = "idle" | "generating" | "ready" | "grading" | "error";

function scoreForProgress(progress = readProgress()) {
  return Object.values(progress).reduce((score, topic) => score + topic.passes, 0);
}

export default function App() {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<GradeResult | null>(null);
  const [isHintVisible, setIsHintVisible] = useState(false);
  const [score, setScore] = useState(scoreForProgress);
  const [state, setState] = useState<State>("idle");
  const [message, setMessage] = useState("");

  async function getChallenge() {
    setState("generating"); setMessage(""); setResult(null); setValues({}); setIsHintVisible(false);
    try {
      const next = await generateChallenge(readProgress());
      setChallenge(next); setState("ready");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create a challenge."); setState("error");
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!challenge) return;
    const testCase = Object.fromEntries(challenge.input_schema.map((field) => [field.name, Number(values[field.name])]));
    if (Object.values(testCase).some((value) => !Number.isInteger(value))) {
      setMessage("Enter an integer for every field."); return;
    }
    setState("grading"); setMessage("");
    try {
      const graded = await gradeChallenge(challenge.challenge_token, testCase);
      setResult(graded); setState("ready"); setScore(scoreForProgress(recordOutcome(challenge.topic, graded.is_breaking)));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not grade that test case."); setState("ready");
    }
  }

  return <main className="app-shell">
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">CS1 debugging practice</p>
        <h1>Case Breaker</h1>
        <p className="lede">Investigate the specification. Inspect the code. Uncover inputs that break the logic.</p>
      </div>
      <div className="score-card" aria-live="polite"><p>Cases broken</p><strong>{score}</strong></div>
    </section>

    {message ? <section className="panel error-panel" role="alert">{message}</section> : null}
    <section className="panel game-panel" aria-label="Game">
      {challenge ? <>
        <div className="panel-header"><div><h2 id="challenge-title">BREAK THIS CASE</h2><p>Find the test case that exposes the logical error in the following code.</p></div></div>
        <article className="task-card"><p className="task-label">Specification</p><p>{challenge.specification}</p><p className="task-label">Faulty C++ code</p><pre><code>{challenge.code}</code></pre></article>
        {!result?.is_breaking ? <form className="test-case-form" onSubmit={submit} aria-label="Counterexample test case"><h3>Your test case</h3><p className="field-help">Enter inputs only. Case Breaker runs them against the specification and the code, then compares the outputs.</p><div className="input-grid">{challenge.input_schema.map((field) => <label key={field.name} htmlFor={`input-${field.name}`}>{field.label}<span>{field.description}</span><input aria-label={field.label} id={`input-${field.name}`} inputMode="numeric" value={values[field.name] ?? ""} onChange={(event) => setValues((current) => ({ ...current, [field.name]: event.target.value }))} /></label>)}</div><button type="submit" disabled={state === "grading" || state === "generating"}>{state === "grading" ? "Checking..." : "Test this Case"}</button></form> : null}
        {result ? <article className={`feedback-card ${result.is_breaking ? "success-card" : ""}`} aria-live="polite"><div className={result.is_breaking ? "feedback ok" : "feedback bad"}>{result.is_breaking ? "Case Broken" : "Case Still Holds"}</div>{result.feedback ? <p>{result.feedback}</p> : null}{isHintVisible && result.hint ? <><p className="task-label">Clue</p><p>{result.hint}</p></> : null}{result.is_breaking ? <><p>Expected: <strong>{String(result.expected_output)}</strong> · Actual: <strong>{String(result.actual_output)}</strong></p><p>{result.explanation}</p></> : null}</article> : null}
      </> : <div className="empty-game"><h2>READY TO BREAK THE CASE?</h2><p>Start a game to receive a specification, code, and test inputs.</p></div>}
      <div className="game-actions"><button type="button" disabled={state === "generating"} onClick={getChallenge}>{state === "generating" ? "Creating..." : challenge ? "Open Another Case" : "Begin Investigation"}</button><button type="button" disabled={!result?.hint} onClick={() => setIsHintVisible(true)}>Clue</button></div>
    </section>
  </main>;
}
