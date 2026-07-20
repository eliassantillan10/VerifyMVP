import { FormEvent, useState } from "react";

import { generateChallenge, gradeChallenge, type Challenge, type GradeResult } from "./api";
import { readProgress, recordOutcome } from "./progress";
import "./App.css";

type State = "idle" | "generating" | "ready" | "grading" | "error";

export default function App() {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<GradeResult | null>(null);
  const [state, setState] = useState<State>("idle");
  const [message, setMessage] = useState("");

  async function getChallenge() {
    setState("generating"); setMessage(""); setResult(null); setValues({});
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
      setResult(graded); setState("ready"); recordOutcome(challenge.topic, graded.is_breaking);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not grade that test case."); setState("ready");
    }
  }

  return <main className="app-shell">
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">CS1 debugging practice</p>
        <h1>Case Breaker</h1>
        <p className="lede">Read the contract. Study the code. Find one concrete input that makes the logic break.</p>
      </div>
      <div className="score-card" aria-live="polite"><p>Challenge status</p><strong>{result?.is_breaking ? "Broken" : challenge ? "Active" : "Ready"}</strong><span>{challenge ? challenge.topic_label : "Challenges adapt as you play"}</span><button type="button" disabled={state === "generating"} onClick={getChallenge}>{state === "generating" ? "Creating..." : "New challenge"}</button></div>
    </section>

    {message ? <section className="panel error-panel" role="alert">{message}</section> : null}
    {challenge ? <section className="panel game-panel" aria-labelledby="challenge-title">
      <div className="panel-header"><div><p className="eyebrow">{challenge.topic_label}</p><h2 id="challenge-title">Find the breaking case</h2></div><span className="pill">One problem at a time</span></div>
      <article className="task-card"><p className="task-label">Specification</p><p>{challenge.specification}</p><p className="task-label">Faulty C++ code</p><pre><code>{challenge.code}</code></pre><p className="prompt">{challenge.prompt}</p></article>
      {!result?.is_breaking ? <form className="test-case-form" onSubmit={submit} aria-label="Counterexample test case"><h3>Your test case</h3><p className="field-help">Enter inputs only. Case Breaker compares the intended result with the code’s result.</p><div className="input-grid">{challenge.input_schema.map((field) => <label key={field.name} htmlFor={`input-${field.name}`}>{field.label}<span>{field.description}</span><input aria-label={field.label} id={`input-${field.name}`} inputMode="numeric" value={values[field.name] ?? ""} onChange={(event) => setValues((current) => ({ ...current, [field.name]: event.target.value }))} /></label>)}</div><button type="submit" disabled={state === "grading"}>{state === "grading" ? "Checking..." : "Test this case"}</button></form> : null}
      {result ? <article className={`feedback-card ${result.is_breaking ? "success-card" : ""}`} aria-live="polite"><div className={result.is_breaking ? "feedback ok" : "feedback bad"}>{result.is_breaking ? "You broke it" : "Not a breaking case"}</div>{result.feedback ? <p>{result.feedback}</p> : null}{result.hint ? <><p className="task-label">Hint unlocked</p><p>{result.hint}</p></> : null}{result.is_breaking ? <><p>Expected: <strong>{String(result.expected_output)}</strong> · Actual: <strong>{String(result.actual_output)}</strong></p><p>{result.explanation}</p><button type="button" onClick={getChallenge}>Next question</button></> : <button type="button" onClick={() => setResult(null)}>Try another case</button>}</article> : null}
    </section> : null}
  </main>;
}
