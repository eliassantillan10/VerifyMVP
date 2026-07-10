import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { formatElapsedSeconds } from "./formatElapsedSeconds";

const generatedGame = {
  title: "CS1 Solution Spotlight",
  tasks: [
    {
      id: "task-1",
      prompt: "Does the best solution satisfy the specification?",
      specifications: "A function should return the larger of two values.",
      candidate_solutions: [
        {
          id: "A",
          label: "Solution A",
          code: "int larger(int a, int b) { return std::max(a, b); }",
        },
        { id: "B", label: "Solution B", code: "int larger(int a, int b) { return a; }" },
        { id: "C", label: "Solution C", code: "int larger(int a, int b) { return b; }" },
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
    const fetchMock = vi.fn(async () => {
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
    });
    vi.stubGlobal("fetch", fetchMock);

    let currentTime = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => currentTime);

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Generate game" }));

    expect(
      await screen.findByRole("heading", { name: "CS1 Solution Spotlight" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/games/generate/", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        cover_topics: ["loops", "functions"],
        emphasize_topics: ["conditionals"],
        problem_types: ["solution comparison"],
      }),
    });
    expect(screen.getAllByText("Task 1 of 1")).toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: /Solution A/ }));
    currentTime = 2500;
    fireEvent.click(screen.getByRole("button", { name: "Submit answer" }));

    const feedback = await screen.findByText("Correct");
    expect(feedback).toBeInTheDocument();
    expect(screen.getByText("Solution A satisfies the specification.")).toBeInTheDocument();
    expect(screen.getByText(/You answered in 1.5 seconds and selected A\./)).toBeInTheDocument();

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

describe("formatElapsedSeconds", () => {
  it("formats milliseconds as readable seconds", () => {
    expect(formatElapsedSeconds(250)).toBe("0.25 seconds");
    expect(formatElapsedSeconds(1000)).toBe("1 second");
    expect(formatElapsedSeconds(1500)).toBe("1.5 seconds");
  });
});
