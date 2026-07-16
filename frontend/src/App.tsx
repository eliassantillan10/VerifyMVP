import { useMemo, useState } from "react";

import {
  generateGame,
  type CandidateSolution,
  type GeneratedGame,
  type GameTask,
  type StudentSettings,
  type TopicOption,
  topicOptions,
} from "./api";
import "./App.css";
import { formatElapsedSeconds } from "./formatElapsedSeconds";

type SessionState =
  | { status: "idle" }
  | { status: "generating" }
  | { status: "ready"; game: GeneratedGame }
  | { status: "finished"; game: GeneratedGame; score: number; total: number }
  | { status: "error"; message: string };

function defaultSettings(): StudentSettings {
  return {
    coverTopics: [],
  };
}

function chooseCandidate(
  task: GameTask,
  candidateId: string,
): CandidateSolution | undefined {
  return task.candidate_solutions.find((candidate) => candidate.id === candidateId);
}

export default function App() {
  const [settings, setSettings] = useState<StudentSettings>(defaultSettings);
  const [session, setSession] = useState<SessionState>({ status: "idle" });
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedCandidate, setSelectedCandidate] = useState("");
  const [feedback, setFeedback] = useState<{
    candidateId: string;
    isCorrect: boolean;
    explanation: string;
    answeredInMs: number;
  } | null>(null);
  const [score, setScore] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const activeGame =
    session.status === "ready" || session.status === "finished"
      ? session.game
      : undefined;
  const hasRequiredSelections = settings.coverTopics.length > 0;

  const currentTask = useMemo(() => {
    if (session.status !== "ready") {
      return undefined;
    }
    return session.game.tasks[currentIndex];
  }, [currentIndex, session]);

  async function handleGenerateGame() {
    if (!hasRequiredSelections) {
      return;
    }

    setSession({ status: "generating" });
    setFeedback(null);
    setCurrentIndex(0);
    setScore(0);
    setSelectedCandidate("");
    setStartedAt(performance.now());

    try {
      const response = await generateGame(settings);
      setSession({ status: "ready", game: response.game });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Game generation failed";
      setSession({ status: "error", message });
    }
  }

  function toggleTopic(topic: TopicOption) {
    setSettings((current) => ({
      coverTopics: current.coverTopics.includes(topic)
        ? current.coverTopics.filter((selectedTopic) => selectedTopic !== topic)
        : [...current.coverTopics, topic],
    }));
  }

  function submitAnswer() {
    if (!currentTask || !startedAt) {
      return;
    }

    const elapsed = Math.max(0, Math.round(performance.now() - startedAt));
    const selected = chooseCandidate(currentTask, selectedCandidate);
    const isCorrect = selected?.id === currentTask.correct_solution_id;
    const earnedTimeBonus =
      activeGame && isCorrect && elapsed <= activeGame.scoring.fast_answer_threshold_ms;
    const points =
      (activeGame && isCorrect ? activeGame.scoring.correctness_points : 0) +
      (earnedTimeBonus ? activeGame.scoring.time_bonus_points : 0);

    setScore((current) => current + points);
    setFeedback({
      candidateId: selectedCandidate,
      isCorrect,
      explanation: currentTask.explanation,
      answeredInMs: elapsed,
    });
  }

  function handleNextTask() {
    if (session.status !== "ready") {
      return;
    }

    const nextIndex = currentIndex + 1;
    setSelectedCandidate("");
    setFeedback(null);
    setStartedAt(performance.now());

    if (nextIndex >= session.game.tasks.length) {
      setSession({
        status: "finished",
        game: session.game,
        score,
        total: session.game.tasks.length,
      });
      return;
    }

    setCurrentIndex(nextIndex);
  }

  const canSubmit = Boolean(currentTask && selectedCandidate);
  const answeredTasks = session.status === "finished" ? session.total : currentIndex;

  return (
    <main className="app-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">CS1 practice game</p>
          <h1>Create a practice game for what you know.</h1>
          <p className="lede">
            Pick the topics you have learned, then play through solution
            comparison tasks with immediate feedback.
          </p>
        </div>
        <div className="score-card" aria-live="polite">
          <p>Current score</p>
          <strong>{score}</strong>
          <span>
            {session.status === "finished"
              ? `Finished ${session.total} tasks`
              : session.status === "ready"
                ? `Task ${Math.min(currentIndex + 1, session.game.tasks.length)} of ${session.game.tasks.length}`
                : "Ready to generate"}
          </span>
        </div>
      </section>

      <section className="panel" aria-labelledby="creator-title">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Your topics</p>
            <h2 id="creator-title">Create your practice game</h2>
          </div>
          <button
            type="button"
            onClick={handleGenerateGame}
            disabled={session.status === "generating" || !hasRequiredSelections}
          >
            {session.status === "generating" ? "Generating..." : "Generate game"}
          </button>
        </div>

        <fieldset className="topic-checklist">
          <legend>Topics to cover</legend>
          <p className="field-help">Choose one or more topics to begin.</p>
          <div className="topic-options">
            {topicOptions.map((topic) => (
              <label className="topic-option" htmlFor={`topic-${topic.id}`} key={topic.id}>
                <input
                  checked={settings.coverTopics.includes(topic.id)}
                  id={`topic-${topic.id}`}
                  onChange={() => toggleTopic(topic.id)}
                  type="checkbox"
                />
                <span>{topic.label}</span>
              </label>
            ))}
          </div>
        </fieldset>
      </section>

      {session.status === "error" ? (
        <section className="panel error-panel" role="alert">
          {session.message}
        </section>
      ) : null}

      {session.status === "ready" || session.status === "finished" ? (
        <section className="panel game-panel" aria-labelledby="game-title">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Student game</p>
              <h2 id="game-title">
                {session.status === "finished"
                  ? `Final score: ${session.score}`
                  : session.game.title}
              </h2>
            </div>
            <div className="pill-row">
              <span className="pill">
                {session.status === "finished"
                  ? `Completed ${session.total}`
                  : `Task ${currentIndex + 1} of ${session.game.tasks.length}`}
              </span>
              <span className="pill">Individual play</span>
            </div>
          </div>

          {session.status === "ready" && currentTask ? (
            <>
              <article className="task-card">
                <p className="task-label">Specifications</p>
                <p>{currentTask.specifications}</p>
                <p className="task-label">Prompt</p>
                <h3>{currentTask.prompt}</h3>

                <div className="candidate-list" role="radiogroup" aria-label="Candidate solutions">
                  {currentTask.candidate_solutions.map((candidate) => (
                    <button
                      key={candidate.id}
                      type="button"
                      className={
                        selectedCandidate === candidate.id
                          ? "candidate selected"
                          : "candidate"
                      }
                      onClick={() => setSelectedCandidate(candidate.id)}
                    >
                      <span className="candidate-name">{candidate.label}</span>
                      <code>{candidate.code}</code>
                    </button>
                  ))}
                </div>
              </article>

              <div className="action-row">
                <button type="button" onClick={submitAnswer} disabled={!canSubmit}>
                  Submit answer
                </button>
              </div>
            </>
          ) : null}

          {feedback && currentTask ? (
            <article className="feedback-card" aria-live="polite">
              <div className={feedback.isCorrect ? "feedback ok" : "feedback bad"}>
                {feedback.isCorrect ? "Correct" : "Incorrect"}
              </div>
              <p>
                You answered in {formatElapsedSeconds(feedback.answeredInMs)} and selected{" "}
                {feedback.candidateId || "no option"}.
              </p>
              <p>{feedback.explanation}</p>
              <button type="button" onClick={handleNextTask}>
                {activeGame && currentIndex + 1 >= activeGame.tasks.length
                  ? "Finish game"
                  : "Next task"}
              </button>
            </article>
          ) : null}

          {session.status === "finished" ? (
            <article className="feedback-card" aria-live="polite">
              <p>Game complete.</p>
              <p>
                Final score: {session.score}. Completed {session.total} tasks with
                immediate feedback after each one.
              </p>
            </article>
          ) : null}
        </section>
      ) : null}

      <section className="panel summary-panel" aria-labelledby="rules-title">
        <div>
          <p className="eyebrow">Scoring</p>
          <h2 id="rules-title">How points work</h2>
        </div>
        <p>
          Correct answers award {activeGame ? activeGame.scoring.correctness_points : 100}
          points. Fast answers can add a smaller bonus if they are submitted
          within the configured threshold.
        </p>
        <p>
          Progress tracked: {answeredTasks} of{" "}
          {activeGame ? activeGame.tasks.length : 0}.
        </p>
      </section>
    </main>
  );
}
