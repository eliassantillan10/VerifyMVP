const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export const topicOptions = [
  {
    id: "variables",
    label: "Variables",
  },
  {
    id: "primitive-data-types",
    label: "Primitive data types",
  },
  {
    id: "operations",
    label: "Operations",
  },
  {
    id: "iostream",
    label: "iostream input/output",
  },
  {
    id: "if",
    label: "if statements",
  },
  {
    id: "else-if",
    label: "else if statements",
  },
  {
    id: "else",
    label: "else statements",
  },
  {
    id: "switch",
    label: "switch statements",
  },
  {
    id: "compound-boolean-expressions",
    label: "Compound boolean expressions",
  },
  {
    id: "order-of-precedence",
    label: "Order of precedence",
  },
  {
    id: "while-loops",
    label: "while loops",
  },
  {
    id: "do-while-loops",
    label: "do-while loops",
  },
  {
    id: "strings",
    label: "string methods and manipulation",
  },
  {
    id: "for-loops",
    label: "for loops",
  },
  {
    id: "for-each-loops",
    label: "for-each loops",
  },
  {
    id: "arrays",
    label: "arrays",
  },
  {
    id: "vectors",
    label: "vectors",
  },
  {
    id: "functions",
    label: "functions and function prototypes",
  },
  {
    id: "pass-by-reference",
    label: "pass-by-reference",
  },
  {
    id: "pass-by-value",
    label: "pass-by-value",
  },
  {
    id: "fstream",
    label: "fstream file input/output",
  },
  {
    id: "structs",
    label: "structs",
  },
  {
    id: "classes",
    label: "classes",
  },
  {
    id: "pointers",
    label: "pointers",
  },
] as const;

export type TopicOption = (typeof topicOptions)[number]["id"];

export interface StudentSettings {
  coverTopics: TopicOption[];
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
  };
  game: GeneratedGame;
}

export async function generateGame(
  settings: StudentSettings,
): Promise<GeneratedGameResponse> {
  const response = await fetch(`${apiBaseUrl}/api/games/generate/`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      cover_topics: settings.coverTopics,
    }),
  });

  if (!response.ok) {
    throw new Error(`Game generation failed with status ${response.status}`);
  }

  return (await response.json()) as GeneratedGameResponse;
}
