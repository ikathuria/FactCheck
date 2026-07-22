import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ConfidenceBar } from "./ConfidenceBar";

afterEach(cleanup);

describe("ConfidenceBar", () => {
  it("renders the percentage and a High label for high confidence", () => {
    render(<ConfidenceBar confidence={0.9} />);
    expect(screen.getByText("90%")).toBeTruthy();
    expect(screen.getByText(/High/)).toBeTruthy();
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "90",
    );
  });

  it("labels mid-range confidence as Moderate", () => {
    render(<ConfidenceBar confidence={0.5} />);
    expect(screen.getByText(/Moderate/)).toBeTruthy();
    expect(screen.getByText("50%")).toBeTruthy();
  });

  it("clamps out-of-range values to 0–100", () => {
    render(<ConfidenceBar confidence={1.4} />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "100",
    );
  });
});
