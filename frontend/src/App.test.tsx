import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const challenge = {
  challenge_token: "signed-token", topic: "if", topic_label: "if statements",
  specification: "Return true only inside [low, high].", prompt: "Find one concrete input that proves this code violates the specification.",
  code: "bool isAllowed(int value, int low, int high) { return value >= low || value <= high; }",
  input_schema: [
    { name: "value", label: "Value", description: "The value to check." },
    { name: "low", label: "Lower bound", description: "The lowest allowed value." },
    { name: "high", label: "Upper bound", description: "The highest allowed value." },
  ],
};

describe("App", () => {
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); document.cookie = "case_breaker_progress=; Max-Age=0; Path=/"; });

  it("keeps the summary separate from the game controls and unlocks a hint after a failed test", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ is_breaking: false, hint: "Check a boundary." }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    expect(screen.queryByText("Topics to cover")).not.toBeInTheDocument();
    expect(screen.getByText("Cases broken")).toBeInTheDocument();
    expect(screen.queryByText("Breaking cases found")).not.toBeInTheDocument();
    expect(screen.queryByText("if statements")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "READY TO BREAK THE CASE?" })).toBeInTheDocument();
    expect(screen.getByText("Start a game to receive a specification, code, and test inputs.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Begin Investigation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Clue" })).toBeDisabled();
    expect(screen.queryByText("Clue", { selector: "p" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    expect(await screen.findByRole("heading", { name: "BREAK THIS CASE" })).toBeInTheDocument();
    expect(screen.getByText("Find the test case that exposes the logical error in the following code.")).toBeInTheDocument();
    expect(screen.queryByText(challenge.prompt)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open Another Case" })).toBeInTheDocument();
    expect(screen.getByText("Enter inputs only. Case Breaker runs them against the specification and the code, then compares the outputs.")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0]).toEqual([
      "/api/case-breaker/challenges/",
      expect.objectContaining({ body: JSON.stringify({ learner_profile: {} }) }),
    ]);
    expect(screen.queryByText(/explanation/i)).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "5" } });
    fireEvent.change(screen.getByLabelText("Lower bound"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Upper bound"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Test this Case" }));
    expect(await screen.findByRole("button", { name: "Clue" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Clue" }));
    expect(await screen.findByText("Clue", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Case Still Holds")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/case-breaker/grade/", expect.objectContaining({ body: JSON.stringify({ challenge_token: "signed-token", test_case: { value: 5, low: 0, high: 10 } }) }));
  });

  it("reveals the explanation only after a breaking test and records progress", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ is_breaking: true, expected_output: false, actual_output: true, explanation: "The OR accepts values outside the range." }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    await screen.findByRole("heading", { name: "BREAK THIS CASE" });
    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "11" } });
    fireEvent.change(screen.getByLabelText("Lower bound"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Upper bound"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Test this Case" }));
    expect(await screen.findByText("The OR accepts values outside the range.")).toBeInTheDocument();
    expect(screen.getByText("Case Broken")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(document.cookie).toContain("case_breaker_progress=");
  });

  it("disables testing while another case is being generated", async () => {
    let resolveNextChallenge: ((response: Response) => void) | undefined;
    const nextChallenge = new Promise<Response>((resolve) => {
      resolveNextChallenge = resolve;
    });
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge }), { status: 200 }))
      .mockReturnValueOnce(nextChallenge);
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    await screen.findByRole("button", { name: "Open Another Case" });

    fireEvent.click(screen.getByRole("button", { name: "Open Another Case" }));

    expect(screen.getByRole("button", { name: "Creating..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Test this Case" })).toBeDisabled();

    resolveNextChallenge?.(new Response(JSON.stringify({ challenge }), { status: 200 }));

    expect(await screen.findByRole("button", { name: "Open Another Case" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Test this Case" })).toBeEnabled();
  });
});
