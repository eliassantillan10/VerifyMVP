import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const generatedGame = {
  title: "CS1 Solution Spotlight",
  tasks: [
    {
      id: "task-1",
      prompt: "Does the best solution satisfy the specification?",
      specifications: "A function should return the larger of two values.",
      candidate_solutions: [
        { id: "A", label: "Solution A", code: "return max(a, b)" },
        { id: "B", label: "Solution B", code: "return a" },
        { id: "C", label: "Solution C", code: "return b" },
      ],
      correct_solution_id: "A",
      explanation: "Solution A satisfies the specification.",
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
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("generates a game from teacher settings and renders the student flow", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(
          JSON.stringify({
            settings: {
              cover_topics: ["loops", "functions"],
              emphasize_topics: ["conditionals"],
              problem_types: ["solution comparison"],
            },
            game: generatedGame,
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 200,
          },
        );
      }),
    );

    vi.spyOn(performance, "now")
      .mockReturnValueOnce(1000)
      .mockReturnValueOnce(2000)
      .mockReturnValueOnce(2500);

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Generate game" }));

    expect(
      await screen.findByRole("heading", { name: "CS1 Solution Spotlight" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Task 1 of 1")).toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: /Solution A/ }));
    fireEvent.click(screen.getByRole("button", { name: "Submit answer" }));

    const feedback = await screen.findByText("Correct");
    expect(feedback).toBeInTheDocument();
    expect(screen.getByText("Solution A satisfies the specification.")).toBeInTheDocument();
    expect(screen.getByText(/You answered in .*selected A\./)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Finish game" }));

    expect(screen.getByText("Final score: 125")).toBeInTheDocument();
    expect(screen.getByText(/Completed 1 tasks/)).toBeInTheDocument();
  });

  it("shows an error when game generation fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("", { status: 500 })),
    );

    render(<App />);
    fireEvent.click(screen.getAllByRole("button", { name: "Generate game" })[0]);

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent("Game generation failed with status 500");
  });
});
