import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { CitationDrawer, type CitationItem } from "./CitationDrawer";

describe("CitationDrawer Component (TASK-WEB-CITE-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockCitations: CitationItem[] = [
    {
      id: "cite-1",
      title: "Quy định Đào tạo Đại học Chính quy HUCE 2025",
      documentRef: "QĐ-2025/ĐH-HUCE",
      quote: "Sinh viên hoàn thành học phí trước tuần 5 của học kỳ.",
      confidence: 0.95,
    },
  ];

  it("renders open citation drawer with evidence details and confidence score", () => {
    const handleClose = vi.fn();
    render(
      <CitationDrawer
        isOpen={true}
        citations={mockCitations}
        onClose={handleClose}
      />
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeDefined();
    expect(screen.getByText("Nguồn trích dẫn & Bằng chứng")).toBeDefined();
    expect(screen.getByText("Quy định Đào tạo Đại học Chính quy HUCE 2025")).toBeDefined();
    expect(screen.getByText(/QĐ-2025\/ĐH-HUCE/i)).toBeDefined();
    expect(screen.getByText(/Độ tin cậy: 95%/i)).toBeDefined();

    const closeBtn = screen.getByRole("button", { name: "Đóng" });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("closes on Escape key press", () => {
    const handleClose = vi.fn();
    render(
      <CitationDrawer
        isOpen={true}
        citations={mockCitations}
        onClose={handleClose}
      />
    );

    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("does not render when isOpen is false", () => {
    render(
      <CitationDrawer
        isOpen={false}
        citations={mockCitations}
        onClose={() => {}}
      />
    );

    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
