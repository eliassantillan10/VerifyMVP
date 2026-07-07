import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the verified backend health contract", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(
          JSON.stringify({
            status: "ok",
            service: "VerifyMVP API",
            database: "postgresql",
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 200,
          },
        );
      }),
    );

    render(<App />);

    expect(
      screen.getByRole("heading", { name: "VerifyMVP" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("online")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
    expect(await screen.findByText(/VerifyMVP API/)).toBeInTheDocument();
  });
});
