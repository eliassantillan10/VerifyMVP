const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type TopicOption = string;

export interface ChallengeInput { name: string; label: string; description: string }
export interface Challenge {
  challenge_token: string;
  topic: TopicOption;
  topic_label: string;
  specification: string;
  prompt: string;
  code: string;
  input_schema: ChallengeInput[];
}
export interface GradeResult {
  is_breaking: boolean;
  hint?: string;
  feedback?: string;
  expected_output?: boolean;
  actual_output?: boolean;
  explanation?: string;
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

export async function generateChallenge(learnerProfile: object): Promise<Challenge> {
  const response = await request<{ challenge: Challenge }>("/api/case-breaker/challenges/", { learner_profile: learnerProfile });
  return response.challenge;
}

export function gradeChallenge(challengeToken: string, testCase: Record<string, number>): Promise<GradeResult> {
  return request<GradeResult>("/api/case-breaker/grade/", { challenge_token: challengeToken, test_case: testCase });
}
