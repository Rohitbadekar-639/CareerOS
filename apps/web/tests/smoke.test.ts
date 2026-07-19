import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { GET } from "../app/healthz/route";
import LandingPage from "../app/page";

describe("web skeleton smoke", () => {
  it("healthz route returns ok", async () => {
    const response = GET();
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ status: "ok" });
  });

  it("landing page renders", () => {
    const html = renderToStaticMarkup(createElement(LandingPage));
    expect(html).toContain("CareerOS");
  });
});
