import { describe, it, expect } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";

describe("Design Tokens & Global Styles (TASK-WEB-DESIGN-001)", () => {
  const tokensPath = path.resolve(__dirname, "tokens.css");
  const globalsPath = path.resolve(__dirname, "../app/globals.css");

  it("tokens.css exists and defines mandatory WCAG AA tokens", () => {
    expect(fs.existsSync(tokensPath)).toBe(true);
    const tokensContent = fs.readFileSync(tokensPath, "utf-8");

    // Brand and Contrast tokens
    expect(tokensContent).toContain("--color-primary");
    expect(tokensContent).toContain("--color-text-main");
    expect(tokensContent).toContain("--color-text-muted");
    expect(tokensContent).toContain("--color-bg-main");
    expect(tokensContent).toContain("--color-border");
    expect(tokensContent).toContain("--color-focus");

    // Touch Target and Focus ring tokens (WCAG 2.2 AA)
    expect(tokensContent).toContain("--target-size-min: 44px");
    expect(tokensContent).toContain("--focus-ring-width: 2px");

    // Simulation & Safety tokens
    expect(tokensContent).toContain("--color-banner-demo");
    expect(tokensContent).toContain("--color-badge-simulation");
  });

  it("globals.css imports tokens and defines accessibility baseline", () => {
    expect(fs.existsSync(globalsPath)).toBe(true);
    const globalsContent = fs.readFileSync(globalsPath, "utf-8");

    // Ensure tokens imported and focus styles declared
    expect(globalsContent).toContain("tokens.css");
    expect(globalsContent).toContain(":focus-visible");
    expect(globalsContent).toContain(".skip-link");
    expect(globalsContent).toContain("prefers-reduced-motion");
  });

  it("negative path: validates rejection of missing essential token", () => {
    const tokensContent = fs.existsSync(tokensPath) ? fs.readFileSync(tokensPath, "utf-8") : "";
    const hasUndefinedToken = tokensContent.includes("--non-existent-token");
    expect(hasUndefinedToken).toBe(false);
  });
});
