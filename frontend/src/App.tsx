import { useEffect, useState } from "react";

import { getHealth, type HealthResponse } from "./api";
import "./App.css";

type ApiState =
  | { status: "loading" }
  | { status: "online"; data: HealthResponse }
  | { status: "offline"; message: string };

const stackItems = [
  { label: "Backend", value: "Django" },
  { label: "Frontend", value: "React" },
  { label: "Database", value: "PostgreSQL" },
  { label: "Runtime", value: "Docker Compose" },
];

export default function App() {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });

  async function refreshHealth() {
    setApiState({ status: "loading" });
    try {
      const data = await getHealth();
      setApiState({ status: "online", data });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Backend status unavailable";
      setApiState({ status: "offline", message });
    }
  }

  useEffect(() => {
    let isActive = true;

    async function loadHealth() {
      try {
        const data = await getHealth();
        if (isActive) {
          setApiState({ status: "online", data });
        }
      } catch (error) {
        if (isActive) {
          const message =
            error instanceof Error ? error.message : "Backend status unavailable";
          setApiState({ status: "offline", message });
        }
      }
    }

    void loadHealth();

    return () => {
      isActive = false;
    };
  }, []);

  return (
    <main className="app-shell">
      <section className="overview" aria-labelledby="page-title">
        <div>
          <p className="eyebrow">MVP verification workspace</p>
          <h1 id="page-title">VerifyMVP</h1>
        </div>
        <div className="status-panel" aria-live="polite">
          <div>
            <p className="panel-label">Backend API</p>
            <p className={`status-text status-${apiState.status}`}>
              {apiState.status === "loading" && "checking"}
              {apiState.status === "online" && "online"}
              {apiState.status === "offline" && "offline"}
            </p>
          </div>
          <button type="button" onClick={refreshHealth}>
            Refresh
          </button>
        </div>
      </section>

      <section className="grid" aria-label="Application stack">
        {stackItems.map((item) => (
          <article className="stack-card" key={item.label}>
            <p>{item.label}</p>
            <strong>{item.value}</strong>
          </article>
        ))}
      </section>

      <section className="contract-panel" aria-labelledby="contract-title">
        <div>
          <h2 id="contract-title">API contract</h2>
          <p>/api/health/</p>
        </div>
        <pre>
          {apiState.status === "online"
            ? JSON.stringify(apiState.data, null, 2)
            : apiState.status === "offline"
              ? apiState.message
              : "Waiting for backend response"}
        </pre>
      </section>
    </main>
  );
}
