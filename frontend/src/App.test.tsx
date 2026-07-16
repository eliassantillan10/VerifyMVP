import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { topicOptions } from "./api";
import { formatElapsedSeconds } from "./formatElapsedSeconds";

const expectedTopics = [
  ["variables", "Variables"],
  ["primitive-data-types", "Primitive data types"],
  ["operations", "Operations"],
  ["iostream", "iostream input/output"],
  ["if", "if statements"],
  ["else-if", "else if statements"],
  ["else", "else statements"],
  ["switch", "switch statements"],
  ["compound-boolean-expressions", "Compound boolean expressions"],
  ["order-of-precedence", "Order of precedence"],
  ["while-loops", "while loops"],
  ["do-while-loops", "do-while loops"],
  ["strings", "string methods and manipulation"],
  ["for-loops", "for loops"],
  ["for-each-loops", "for-each loops"],
  ["arrays", "arrays"],
  ["vectors", "vectors"],
  ["functions", "functions and function prototypes"],
  ["pass-by-reference", "pass-by-reference"],
  ["pass-by-value", "pass-by-value"],
  ["fstream", "fstream file input/output"],
  ["structs", "structs"],
  ["classes", "classes"],
  ["pointers", "pointers"],
] as const;

const generatedGame = {
  title: "CS1 Solution Spotlight",
  tasks: [
    {
      id: "task-1",
      prompt: "Choose the best implementation.",
      specifications: "Use the selected topic correctly.",
      candidate_solutions: [
        { id: "A", label: "Solution A", code: "return true;" },
        { id: "B", label: "Solution B", code: "return false;" },
        { id: "C", label: "Solution C", code: "return value;" },
      ],
      correct_solution_id: "A",
      explanation: "Solution A satisfies the requirement.",
    },
  ],
  scoring: {
    correctness_points: 100,
    time_bonus_points: 25,
    fast_answer_threshold_ms: 8000,
  },
};

describe("App", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the exact atomic topic catalog as a checkbox list", () => {
    expect(topicOptions.map(({ id, label }) => [id, label])).toEqual(expectedTopics);

    render(<App />);

    expect(screen.getByRole("group", { name: "Topics to cover" })).toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")).toHaveLength(expectedTopics.length);
    expect(screen.queryByLabelText("Topics to emphasize")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Problem types")).not.toBeInTheDocument();
    expect(screen.queryByText(/teacher/i)).not.toBeInTheDocument();
  });

  it("enables generation after selecting a topic and sends only cover topics", async () => {
    const fetchMock = vi.fn(async () => new Response(
      JSON.stringify({
        settings: { cover_topics: ["arrays"], emphasize_topics: [] },
        game: generatedGame,
      }),
      { headers: { "Content-Type": "application/json" }, status: 200 },
    ));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    const generateButton = screen.getByRole("button", { name: "Generate game" });
    expect(generateButton).toBeDisabled();

    fireEvent.click(screen.getByRole("checkbox", { name: "arrays" }));
    expect(generateButton).toBeEnabled();

    fireEvent.click(generateButton);
    expect(await screen.findByRole("heading", { name: "CS1 Solution Spotlight" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/games/generate/", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ cover_topics: ["arrays"] }),
    });
  });

  it("keeps selected topics after a failed generation", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("", { status: 500 })));
    render(<App />);

    const arrays = screen.getByRole("checkbox", { name: "arrays" });
    fireEvent.click(arrays);
    fireEvent.click(screen.getByRole("button", { name: "Generate game" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Game generation failed with status 500");
    expect(arrays).toBeChecked();
  });
});

describe("formatElapsedSeconds", () => {
  it("formats milliseconds as readable seconds", () => {
    expect(formatElapsedSeconds(250)).toBe("0.25 seconds");
    expect(formatElapsedSeconds(1000)).toBe("1 second");
    expect(formatElapsedSeconds(1500)).toBe("1.5 seconds");
  });
});
