const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type TopicOption =
  | "variables"
  | "conditionals"
  | "loops"
  | "functions"
  | "arrays"
  | "strings";

export type ProblemType =
  | "solution comparison"
  | "specification checking"
  | "debugging";

export interface TeacherSettings {
  coverTopics: TopicOption[];
  emphasizeTopics: TopicOption[];
  problemTypes: ProblemType[];
}

export interface CandidateSolution {
  id: string;
  label: string;
  code: string;
}

export interface GameTask {
  id: string;
  prompt: string;
  specifications: string;
  candidate_solutions: CandidateSolution[];
  correct_solution_id: string;
  explanation: string;
}

export interface GeneratedGame {
  title: string;
  tasks: GameTask[];
  scoring: {
    correctness_points: number;
    time_bonus_points: number;
    fast_answer_threshold_ms: number;
  };
}

export interface GeneratedGameResponse {
  settings: {
    cover_topics: TopicOption[];
    emphasize_topics: TopicOption[];
    problem_types: ProblemType[];
  };
  game: GeneratedGame;
}

export async function generateGame(
  settings: TeacherSettings,
): Promise<GeneratedGameResponse> {
  const response = await fetch(`${apiBaseUrl}/api/games/generate/`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      cover_topics: settings.coverTopics,
      emphasize_topics: settings.emphasizeTopics,
      problem_types: settings.problemTypes,
    }),
  });

  if (!response.ok) {
    throw new Error(`Game generation failed with status ${response.status}`);
  }

  return (await response.json()) as GeneratedGameResponse;
}
