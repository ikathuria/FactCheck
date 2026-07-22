import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Verdict } from "@/lib/types";
import { VERDICT_META } from "@/lib/verdict";
import { VerdictBadge } from "./VerdictBadge";

afterEach(cleanup);

describe("VerdictBadge", () => {
  const verdicts: Verdict[] = [
    "supported",
    "refuted",
    "contested",
    "insufficient_evidence",
  ];

  it.each(verdicts)("renders the human label for %s", (verdict) => {
    render(<VerdictBadge verdict={verdict} />);
    expect(screen.getByText(VERDICT_META[verdict].label)).toBeTruthy();
  });

  it("exposes the verdict via a data attribute for styling/testing", () => {
    render(<VerdictBadge verdict="refuted" />);
    const badge = screen.getByTestId("verdict-badge");
    expect(badge.getAttribute("data-verdict")).toBe("refuted");
  });

  it("never renders a bare TRUE/FALSE label", () => {
    render(<VerdictBadge verdict="supported" />);
    expect(screen.queryByText(/^(true|false)$/i)).toBeNull();
  });
});
