import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppShell } from "./AppShell";

describe("AppShell Component (TASK-WEB-SHELL-001)", () => {
  it("renders mandatory simulation disclosure banner and HUCE Demo identity", () => {
    render(
      <AppShell>
        <div>Page Content</div>
      </AppShell>
    );

    // Persistent disclaimer (REQ-F-GOV-001)
    expect(screen.getByText(/Campus 24\/7 — HUCE Demo/i)).toBeDefined();
    expect(screen.getByText(/Dữ liệu mô phỏng/i)).toBeDefined();

    // Semantic landmarks
    expect(screen.getByRole("banner")).toBeDefined();
    expect(screen.getByRole("navigation")).toBeDefined();
    expect(screen.getByRole("main")).toBeDefined();

    // Skip to content link
    const skipLink = screen.getByText(/Bỏ qua tới nội dung chính/i);
    expect(skipLink).toBeDefined();
    expect(skipLink.getAttribute("href")).toBe("#main-content");

    // Children rendered in main
    expect(screen.getByText("Page Content")).toBeDefined();
  });

  it("negative path: handles empty or null children without crashing", () => {
    const { container } = render(<AppShell>{null}</AppShell>);
    const main = container.querySelector("main");
    expect(main).not.toBeNull();
    expect(main?.children.length).toBe(0);
  });
});
