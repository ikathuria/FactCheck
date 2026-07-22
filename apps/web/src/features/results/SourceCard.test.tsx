import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Source } from "@/lib/types";
import { SourceCard } from "./SourceCard";

afterEach(cleanup);

const baseSource: Source = {
  url: "https://www.cdc.gov/flu/data.html",
  title: "Flu surveillance data",
  snippet: "Weekly influenza surveillance report.",
  credibility_score: 1.0,
  domain_type: "government",
};

describe("SourceCard", () => {
  it("renders title, cleaned hostname, domain badge, and credibility %", () => {
    render(<SourceCard source={baseSource} />);
    expect(screen.getByText("Flu surveillance data")).toBeTruthy();
    expect(screen.getByText("cdc.gov")).toBeTruthy(); // www. stripped
    expect(screen.getByText("Government")).toBeTruthy();
    expect(screen.getByText("100%")).toBeTruthy();
  });

  it("links out to the source in a new tab safely", () => {
    render(<SourceCard source={baseSource} />);
    const link = screen.getByRole("link", { name: "Flu surveillance data" });
    expect(link.getAttribute("href")).toBe(baseSource.url);
    expect(link.getAttribute("rel")).toContain("noopener");
  });

  it("flags low-credibility sources", () => {
    render(
      <SourceCard source={{ ...baseSource, credibility_score: 0.3, domain_type: "other" }} />,
    );
    expect(screen.getByText(/Low credibility/i)).toBeTruthy();
  });

  it("does not flag credible sources", () => {
    render(<SourceCard source={baseSource} />);
    expect(screen.queryByText(/Low credibility/i)).toBeNull();
  });
});
