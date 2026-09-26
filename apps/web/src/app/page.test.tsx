import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import HomePage from "./page";

describe("HomePage Component (TASK-WEB-HOME-001)", () => {
  it("renders the modernized academic workspace hero, landing actions, and service links", () => {
    render(<HomePage />);

    // Verify main headings
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /Không Gian Làm Việc Học Thuật & Một Cửa Số/i,
      })
    ).toBeDefined();

    // Verify UX-SCR-001 primary landing actions
    expect(screen.getByRole("link", { name: /Đăng nhập/i })).toBeDefined();
    expect(screen.getByRole("link", { name: /Xem trợ giúp/i })).toBeDefined();

    // Verify fast AI prompt input / action
    expect(screen.getByPlaceholderText(/Hỏi Trợ lý AI về quy chế, tín chỉ, lịch thi/i)).toBeDefined();

    // Verify next class spotlight with provenance
    expect(screen.getByText(/Lập trình Web nâng cao/i)).toBeDefined();
    expect(screen.getByText(/Phòng 402-H1/i)).toBeDefined();

    // Verify 4 main service links
    expect(screen.getByRole("link", { name: /Hỏi đáp AI 24\/7/i })).toBeDefined();
    expect(screen.getByRole("link", { name: /Thời khóa biểu & Lịch thi/i })).toBeDefined();
    expect(screen.getByRole("link", { name: /Thủ tục & Một cửa số/i })).toBeDefined();
    expect(screen.getByRole("link", { name: /Đăng ký mượn phòng/i })).toBeDefined();
  });
});
