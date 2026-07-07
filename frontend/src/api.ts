const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export interface HealthResponse {
  status: "ok";
  service: string;
  database: "postgresql";
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const payload = value as Record<string, unknown>;
  return (
    payload.status === "ok" &&
    typeof payload.service === "string" &&
    payload.database === "postgresql"
  );
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/health/`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  const payload: unknown = await response.json();
  if (!isHealthResponse(payload)) {
    throw new Error("Health check returned an unexpected response");
  }

  return payload;
}
