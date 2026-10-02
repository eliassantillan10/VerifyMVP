const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type TopicOption = string;

export interface Challenge {
  id: string;
  topic: TopicOption;
  description: string;
  code: string;
}

interface ChallengeResponse {
  challenge: Challenge;
  coachEnabled: boolean;
  gradingEnabled: boolean;
}

export type CoachMode = "HINT" | "EXPLAIN" | "REVIEW";

export interface CoachReply {
  challengeId: string;
  mode: CoachMode;
  message: string;
}

export type GradeVerdict = "EXPOSES_FLAW" | "DOES_NOT_EXPOSE_FLAW" | "UNCLEAR";

export interface GradeReply {
  challengeId: string;
  verdict: GradeVerdict;
  message: string;
}

async function request<T>(path: string, body: object): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = (await response.json()) as T & { error?: string };
  if (!response.ok) throw new Error(payload.error ?? `Request failed with status ${response.status}`);
  return payload;
}

export function generateChallenge(): Promise<ChallengeResponse> {
  return request<ChallengeResponse>("/api/case-breaker/challenges/", {});
}

export async function askCoach(
  challengeId: string,
  mode: CoachMode,
  learnerText: string,
): Promise<CoachReply> {
  const response = await request<{ coach: CoachReply }>("/api/case-breaker/coach/", {
    challengeId,
    mode,
    learnerText,
  });
  return response.coach;
}

export async function gradeTestCase(
  challengeId: string,
  testCase: string,
): Promise<GradeReply> {
  const response = await request<{ grade: GradeReply }>("/api/case-breaker/grade/", {
    challengeId,
    testCase,
  });
  return response.grade;
}
