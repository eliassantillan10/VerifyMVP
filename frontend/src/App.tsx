import { useState } from "react";

import {
  askCoach,
  generateChallenge,
  gradeTestCase,
  type Challenge,
  type CoachMode,
  type GradeReply,
} from "./api";
import "./App.css";

type State = "idle" | "generating" | "ready" | "coaching" | "grading" | "error";

export default function App() {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [coachEnabled, setCoachEnabled] = useState(false);
  const [gradingEnabled, setGradingEnabled] = useState(false);
  const [state, setState] = useState<State>("idle");
  const [message, setMessage] = useState("");
  const [coachReply, setCoachReply] = useState("");
  const [learnerText, setLearnerText] = useState("");
  const [testCaseDraft, setTestCaseDraft] = useState("");
  const [isTestCaseDraftSubmitted, setIsTestCaseDraftSubmitted] = useState(false);
  const [grade, setGrade] = useState<GradeReply | null>(null);
  const [isHintVisible, setIsHintVisible] = useState(false);

  async function getChallenge() {
    setChallenge(null); setCoachEnabled(false); setGradingEnabled(false); setCoachReply(""); setLearnerText(""); setTestCaseDraft(""); setIsTestCaseDraftSubmitted(false); setGrade(null); setIsHintVisible(false); setMessage(""); setState("generating");
    try {
      const next = await generateChallenge();
      setChallenge(next.challenge); setCoachEnabled(next.coachEnabled); setGradingEnabled(next.gradingEnabled); setState("ready");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create a challenge."); setState("error");
    }
  }

  async function requestCoach(mode: CoachMode) {
    if (!challenge) return;
    setState("coaching"); setMessage(""); setCoachReply("");
    try {
      const reply = await askCoach(challenge.id, mode, learnerText);
      setCoachReply(reply.message); setState("ready");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not reach the coach."); setState("ready");
    }
  }

  async function submitTestCaseDraft() {
    if (!testCaseDraft.trim()) return;
    if (!challenge || !gradingEnabled) {
      setIsTestCaseDraftSubmitted(true);
      return;
    }
    setState("grading"); setMessage(""); setGrade(null); setIsTestCaseDraftSubmitted(false);
    try {
      setGrade(await gradeTestCase(challenge.id, testCaseDraft)); setState("ready");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not reach the local grader."); setState("ready");
    }
  }

  return <main className="app-shell">
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">CS1 debugging practice</p>
        <h1>Case Breaker</h1>
        <p className="lede">Investigate a C++ problem, inspect its logic, and find flaws with test cases.</p>
      </div>
    </section>

    {message ? <section className="panel error-panel" role="alert">{message}</section> : null}
    <section className="panel game-panel" aria-label="Game">
      {challenge ? <>
        <div className="panel-header"><div><h2 id="challenge-title">CASE TO REVIEW</h2><p>Read the problem statement and inspect the implementation before opening another case.</p></div></div>
        <article className="task-card"><p className="task-label">Topic</p><p>{challenge.topic}</p><p className="task-label">Problem</p><p>{challenge.description}</p><p className="task-label">C++ code</p><pre><code>{challenge.code}</code></pre></article>
        <section className="practice-panel" aria-labelledby="practice-title">
          <div className="practice-panel-header"><h3 id="practice-title">Test your reasoning</h3></div>
          <p>{gradingEnabled ? "Submit an input for feedback from the required local LM Studio grader. The result is an assessment, not proof." : "Draft an input that you think would expose a flaw in the code's logic. This draft stays in your browser for now."}</p>
          <label htmlFor="test-case-draft">Your test case draft</label>
          <textarea id="test-case-draft" rows={2} value={testCaseDraft} onChange={(event) => { setTestCaseDraft(event.target.value); setIsTestCaseDraftSubmitted(false); setGrade(null); }} placeholder="Submit a test case that will expose the code's logic." />
          <div className="game-actions"><button type="button" disabled={!testCaseDraft.trim() || state === "grading"} onClick={submitTestCaseDraft}>{state === "grading" ? "Assessing..." : "Submit"}</button><button className="hint-button" type="button" aria-controls={isHintVisible ? "practice-hint" : undefined} aria-expanded={isHintVisible} onClick={() => setIsHintVisible((visible) => !visible)}>Hint</button></div>
          {isTestCaseDraftSubmitted ? <p role="status">Draft saved locally.</p> : null}
          {grade ? <p className="grade-reply" role="status" aria-live="polite"><strong>{grade.verdict === "EXPOSES_FLAW" ? "Likely exposes the flaw." : grade.verdict === "DOES_NOT_EXPOSE_FLAW" ? "Likely does not expose the flaw." : "The model's assessment is unclear."}</strong> {grade.message}</p> : null}
          {isHintVisible ? <p id="practice-hint" className="hint-template" aria-live="polite">Look for the smallest input that makes the code disagree with the problem statement.</p> : null}
        </section>
        {coachEnabled ? <section className="coach-panel" aria-labelledby="coach-title">
          <h3 id="coach-title">AI Coach</h3>
          <p>Ask for a nudge, an explanation, or feedback on your reasoning. The coach does not run the code.</p>
          <label htmlFor="coach-reasoning">Your reasoning (optional for hint or explanation)</label>
          <textarea id="coach-reasoning" maxLength={2000} value={learnerText} onChange={(event) => setLearnerText(event.target.value)} />
          <div className="game-actions"><button type="button" disabled={state === "coaching"} onClick={() => requestCoach("HINT")}>{state === "coaching" ? "Asking..." : "Ask AI Coach for Hint"}</button><button type="button" disabled={state === "coaching"} onClick={() => requestCoach("EXPLAIN")}>Explain</button><button type="button" disabled={state === "coaching" || !learnerText.trim()} onClick={() => requestCoach("REVIEW")}>Review reasoning</button></div>
          {coachReply ? <p className="coach-reply" aria-live="polite">{coachReply}</p> : null}
        </section> : null}
      </> : <div className="empty-game"><h2>READY TO INVESTIGATE?</h2><p>Open a reviewed C++ problem to begin your code review.</p></div>}
      <div className="game-actions"><button type="button" disabled={state === "generating"} onClick={getChallenge}>{state === "generating" ? "Opening..." : challenge ? "Open Another Case" : "Begin Investigation"}</button></div>
    </section>
  </main>;
}
