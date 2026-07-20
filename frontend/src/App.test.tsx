import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const challenge = {
  challenge_token: "signed-token", topic: "if", topic_label: "if statements",
  specification: "Return true only inside [low, high].", prompt: "Find an input that breaks the code.",
  code: "bool isAllowed(int value, int low, int high) { return value >= low || value <= high; }",
  input_schema: [
    { name: "value", label: "Value", description: "The value to check." },
    { name: "low", label: "Lower bound", description: "The lowest allowed value." },
    { name: "high", label: "Upper bound", description: "The highest allowed value." },
  ],
};

describe("App", () => {
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); document.cookie = "case_breaker_progress=; Max-Age=0; Path=/"; });

  it("creates one hidden-oracle challenge and unlocks feedback after a failed test", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ is_breaking: false, hint: "Check a boundary." }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    expect(screen.queryByText("Topics to cover")).not.toBeInTheDocument();
    expect(screen.queryByText(/Hint unlocked/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "New challenge" }));
    expect(await screen.findByRole("heading", { name: "Find the breaking case" })).toBeInTheDocument();
    expect(fetchMock.mock.calls[0]).toEqual([
      "/api/case-breaker/challenges/",
      expect.objectContaining({ body: JSON.stringify({ learner_profile: {} }) }),
    ]);
    expect(screen.queryByText(/explanation/i)).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "5" } });
    fireEvent.change(screen.getByLabelText("Lower bound"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Upper bound"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Test this case" }));
    expect(await screen.findByText("Hint unlocked")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/case-breaker/grade/", expect.objectContaining({ body: JSON.stringify({ challenge_token: "signed-token", test_case: { value: 5, low: 0, high: 10 } }) }));
  });

  it("reveals the explanation only after a breaking test and records progress", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ is_breaking: true, expected_output: false, actual_output: true, explanation: "The OR accepts values outside the range." }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "New challenge" }));
    await screen.findByRole("heading", { name: "Find the breaking case" });
    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "11" } });
    fireEvent.change(screen.getByLabelText("Lower bound"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Upper bound"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Test this case" }));
    expect(await screen.findByText("The OR accepts values outside the range.")).toBeInTheDocument();
    expect(document.cookie).toContain("case_breaker_progress=");
  });
});
