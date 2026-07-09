import { useMemo, useState } from "react";

import {
  generateGame,
  type CandidateSolution,
  type GeneratedGame,
  type GameTask,
  type ProblemType,
  type TeacherSettings,
  type TopicOption,
} from "./api";
import "./App.css";

type SessionState =
  | { status: "idle" }
  | { status: "generating" }
  | { status: "ready"; game: GeneratedGame }
  | { status: "finished"; game: GeneratedGame; score: number; total: number }
  | { status: "error"; message: string };

const topicOptions: TopicOption[] = [
  "variables",
  "conditionals",
  "loops",
  "functions",
  "arrays",
  "strings",
];

const problemTypeOptions: ProblemType[] = [
  "solution comparison",
  "specification checking",
  "debugging",
];

function defaultSettings(): TeacherSettings {
  return {
    coverTopics: ["loops", "functions"],
    emphasizeTopics: ["conditionals"],
    problemTypes: ["solution comparison"],
  };
}

function chooseCandidate(
  task: GameTask,
  candidateId: string,
): CandidateSolution | undefined {
  return task.candidate_solutions.find((candidate) => candidate.id === candidateId);
}

export default function App() {
  const [settings, setSettings] = useState<TeacherSettings>(defaultSettings);
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

  const currentTask = useMemo(() => {
    if (session.status !== "ready") {
      return undefined;
    }
    return session.game.tasks[currentIndex];
  }, [currentIndex, session]);

  async function handleGenerateGame() {
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
          <p className="eyebrow">CS1 teacher authoring flow</p>
          <h1>Generate a practice game from your course goals.</h1>
          <p className="lede">
            Choose the topics to cover, the topics to emphasize, and the kind of
            solution-checking tasks you want. Students then play through one
            task at a time and get immediate feedback.
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

      <section className="panel" aria-labelledby="teacher-title">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Teacher settings</p>
            <h2 id="teacher-title">Author the game</h2>
          </div>
          <button
            type="button"
            onClick={handleGenerateGame}
            disabled={session.status === "generating"}
          >
            {session.status === "generating" ? "Generating..." : "Generate game"}
          </button>
        </div>

        <div className="settings-grid">
          <label>
            Topics to cover
            <select
              multiple
              value={settings.coverTopics}
              onChange={(event) =>
                setSettings((current) => ({
                  ...current,
                  coverTopics: Array.from(event.target.selectedOptions).map(
                    (option) => option.value as TopicOption,
                  ),
                }))
              }
            >
              {topicOptions.map((topic) => (
                <option value={topic} key={topic}>
                  {topic}
                </option>
              ))}
            </select>
          </label>

          <label>
            Topics to emphasize
            <select
              multiple
              value={settings.emphasizeTopics}
              onChange={(event) =>
                setSettings((current) => ({
                  ...current,
                  emphasizeTopics: Array.from(event.target.selectedOptions).map(
                    (option) => option.value as TopicOption,
                  ),
                }))
              }
            >
              {topicOptions.map((topic) => (
                <option value={topic} key={topic}>
                  {topic}
                </option>
              ))}
            </select>
          </label>

          <label>
            Problem types
            <select
              multiple
              value={settings.problemTypes}
              onChange={(event) =>
                setSettings((current) => ({
                  ...current,
                  problemTypes: Array.from(event.target.selectedOptions).map(
                    (option) => option.value as ProblemType,
                  ),
                }))
              }
            >
              {problemTypeOptions.map((problemType) => (
                <option value={problemType} key={problemType}>
                  {problemType}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="selection-summary">
          <div>
            <span>Covering</span>
            <strong>{settings.coverTopics.join(", ")}</strong>
          </div>
          <div>
            <span>Emphasizing</span>
            <strong>{settings.emphasizeTopics.join(", ")}</strong>
          </div>
          <div>
            <span>Problem style</span>
            <strong>{settings.problemTypes.join(", ")}</strong>
          </div>
        </div>
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
                You answered in {feedback.answeredInMs}ms and selected{" "}
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
