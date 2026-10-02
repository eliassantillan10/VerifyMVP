import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const challenge = {
  id: "case-breaker-001-001",
  topic: "Variables, primitive data types, and their operations",
  description: "Calculates the total cost for several identical items.",
  code: "int main() { return 0; }",
};

describe("App", () => {
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); vi.useRealTimers(); });

  it("shows a problem without revealing its answer and provides local practice controls", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    expect(screen.getByRole("heading", { name: "READY TO INVESTIGATE?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Begin Investigation" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    expect(await screen.findByRole("heading", { name: "CASE TO REVIEW" })).toBeInTheDocument();
    expect(screen.getByText(challenge.topic)).toBeInTheDocument();
    expect(screen.getByText(challenge.description)).toBeInTheDocument();
    expect(screen.getByText(challenge.code)).toBeInTheDocument();
    expect(screen.queryByText("The total is calculated incorrectly.")).not.toBeInTheDocument();
    expect(screen.queryByText("Input 3 produces 8 instead of 9.")).not.toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Your test case draft" })).toHaveAttribute(
      "placeholder",
      "Submit a test case that will expose the code's logic.",
    );
    const submit = screen.getByRole("button", { name: "Submit" });
    const hint = screen.getByRole("button", { name: "Hint" });
    expect(submit).toBeDisabled();
    expect(submit.parentElement).toContainElement(hint);
    expect(screen.getByRole("button", { name: "Open Another Case" })).toBeInTheDocument();
    expect(fetchMock.mock.calls[0]).toEqual([
      "/api/case-breaker/challenges/",
      expect.objectContaining({ body: JSON.stringify({}) }),
    ]);
  });

  it("keeps hint and test-case drafts local to the browser", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    const draft = await screen.findByRole("textbox", { name: "Your test case draft" });
    fireEvent.change(draft, { target: { value: "Use one item as the smallest input." } });
    fireEvent.click(screen.getByRole("button", { name: "Hint" }));

    expect(draft).toHaveValue("Use one item as the smallest input.");
    expect(screen.getByText("Look for the smallest input that makes the code disagree with the problem statement.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("submits a test case for local AI-assisted grading when enabled", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false, gradingEnabled: true }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ grade: { challengeId: challenge.id, verdict: "EXPOSES_FLAW", message: "This input is likely to expose the flaw." } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    const draft = await screen.findByRole("textbox", { name: "Your test case draft" });
    const submit = screen.getByRole("button", { name: "Submit" });
    fireEvent.change(draft, { target: { value: "3 4" } });
    fireEvent.click(submit);

    expect(await screen.findByRole("status")).toHaveTextContent("This input is likely to expose the flaw.");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/case-breaker/grade/",
      expect.objectContaining({ body: JSON.stringify({ challengeId: challenge.id, testCase: "3 4" }) }),
    );
  });

  it("shows elapsed evaluation time while a grade request is pending", async () => {
    let resolveGrade: (response: Response) => void;
    const gradeResponse = new Promise<Response>((resolve) => { resolveGrade = resolve; });
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false, gradingEnabled: true }), { status: 200 }))
      .mockReturnValueOnce(gradeResponse);
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    fireEvent.change(await screen.findByRole("textbox", { name: "Your test case draft" }), { target: { value: "3 4" } });
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(screen.getByRole("button", { name: "Evaluating. 0 seconds elapsed." })).toHaveTextContent("Evaluating... 0s");
    await vi.advanceTimersByTimeAsync(5000);
    expect(screen.getByRole("button", { name: "Evaluating. 5 seconds elapsed." })).toHaveTextContent("Evaluating... 5s");

    resolveGrade!(new Response(JSON.stringify({ grade: { challengeId: challenge.id, verdict: "EXPOSES_FLAW", message: "This input is likely to expose the flaw." } }), { status: 200 }));
    await vi.advanceTimersByTimeAsync(0);
    expect(screen.getByText("Likely exposes the flaw.")).toBeInTheDocument();
  });

  it("shows the model's explanation when its assessment is unclear", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false, gradingEnabled: true }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ grade: { challengeId: challenge.id, verdict: "UNCLEAR", message: "The supplied input does not isolate the condition." } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    fireEvent.change(await screen.findByRole("textbox", { name: "Your test case draft" }), { target: { value: "example" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByRole("status")).toHaveTextContent("The model's assessment is unclear.");
    expect(screen.getByRole("status")).toHaveTextContent("The supplied input does not isolate the condition.");
  });

  it("shows the structured-output compatibility guidance from the grader", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false, gradingEnabled: true }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "The local LM Studio grader returned an unusable response. Check that the configured model supports structured JSON output, then retry." }), { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    fireEvent.change(await screen.findByRole("textbox", { name: "Your test case draft" }), { target: { value: "example" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("supports structured JSON output");
    expect(screen.getByRole("button", { name: "Submit" })).toBeEnabled();
  });

  it("requests another display-only case", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge: { ...challenge, id: "case-breaker-001-002" }, coachEnabled: false }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    await screen.findByRole("button", { name: "Open Another Case" });
    fireEvent.change(screen.getByRole("textbox", { name: "Your test case draft" }), { target: { value: "Try an empty input." } });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(screen.getByRole("status")).toHaveTextContent("Draft saved locally.");
    fireEvent.click(screen.getByRole("button", { name: "Hint" }));
    fireEvent.click(screen.getByRole("button", { name: "Open Another Case" }));

    await screen.findByRole("button", { name: "Open Another Case" });
    expect(fetchMock.mock.calls[1]).toEqual([
      "/api/case-breaker/challenges/",
      expect.objectContaining({ body: JSON.stringify({}) }),
    ]);
    expect(screen.getByRole("textbox", { name: "Your test case draft" })).toHaveValue("");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(screen.queryByText("Look for the smallest input that makes the code disagree with the problem statement.")).not.toBeInTheDocument();
  });

  it("clears the previous case when the problem pool is empty", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: false }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ error: "No Case Breaker problems are available." }), { status: 400 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    await screen.findByRole("button", { name: "Open Another Case" });
    fireEvent.click(screen.getByRole("button", { name: "Open Another Case" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No Case Breaker problems are available.");
    expect(screen.queryByText(challenge.topic)).not.toBeInTheDocument();
    expect(screen.queryByText(challenge.description)).not.toBeInTheDocument();
    expect(screen.queryByText(challenge.code)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Begin Investigation" })).toBeInTheDocument();
  });

  it("requests a hint for the loaded case and renders the coach reply", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ challenge, coachEnabled: true }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ coach: { challengeId: challenge.id, mode: "HINT", message: "Inspect the loop boundary." } }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Begin Investigation" }));
    await screen.findByRole("button", { name: "Ask AI Coach for Hint" });
    fireEvent.click(screen.getByRole("button", { name: "Ask AI Coach for Hint" }));

    expect(await screen.findByText("Inspect the loop boundary.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/case-breaker/coach/",
      expect.objectContaining({ body: JSON.stringify({ challengeId: challenge.id, mode: "HINT", learnerText: "" }) }),
    );
  });
});
