import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import { AppShell } from "./AppShell";

describe("AppShell Component (TASK-WEB-SHELL-001)", () => {
  afterEach(() => { cleanup(); });
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


  it("filters navigation items based on userRole", () => {
    const { rerender, queryByText } = render(
      <AppShell userRole="student">
        <div>Content</div>
      </AppShell>
    );
    expect(queryByText("Hỏi đáp AI")).not.toBeNull();
    expect(queryByText("Cán bộ")).toBeNull();

    rerender(
      <AppShell userRole="staff">
        <div>Content</div>
      </AppShell>
    );
    expect(queryByText("Cán bộ")).not.toBeNull();
    expect(queryByText("Hỏi đáp AI")).toBeNull();
  });

  it("negative path: handles empty or null children without crashing", () => {
    const { container } = render(<AppShell>{null}</AppShell>);
    const main = container.querySelector("main");
    expect(main).not.toBeNull();
    expect(main?.children.length).toBe(0);
  });
});
