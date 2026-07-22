import { expect, test } from "@playwright/test";

const mockVerify = {
  claim: "The Eiffel Tower is in Paris",
  verdict: "supported",
  confidence: 0.95,
  reasoning:
    "Multiple authoritative sources confirm the Eiffel Tower is located in Paris, France.",
  sources: [
    {
      url: "https://www.britannica.com/topic/Eiffel-Tower-Paris-France",
      title: "Eiffel Tower | History, Height, Facts",
      snippet: "The Eiffel Tower is a wrought-iron lattice tower in Paris.",
      credibility_score: 0.7,
      domain_type: "established_news",
    },
  ],
  cached: false,
  cached_at: new Date().toISOString(),
  ttl_expires_at: null,
  sub_claims: ["The Eiffel Tower is in Paris"],
  source_mode: "strict",
  source_mode_fallback: false,
};

test("submit a claim in Strict mode and see a verdict with a source", async ({
  page,
}) => {
  // Mock the backend so the test is deterministic and needs no live API/LLM.
  await page.route("**/recent-searches**", (route) =>
    route.fulfill({ json: { searches: [], total: 0 } }),
  );
  await page.route("**/verify", (route) => route.fulfill({ json: mockVerify }));

  await page.goto("/");

  await page
    .getByPlaceholder(/Enter a claim/i)
    .fill("The Eiffel Tower is in Paris");
  await page.getByRole("radio", { name: /Strict/ }).click();
  await page.getByRole("button", { name: /Fact-check/i }).click();

  const panel = page.getByTestId("results-panel");
  await expect(panel).toBeVisible();
  await expect(panel.getByTestId("verdict-badge")).toHaveAttribute(
    "data-verdict",
    "supported",
  );
  await expect(page.getByTestId("source-card").first()).toBeVisible();
});
