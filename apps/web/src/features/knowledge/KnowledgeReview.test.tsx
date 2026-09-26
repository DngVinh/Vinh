import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { KnowledgeReview, type KnowledgeDocItem } from "./KnowledgeReview";

describe("KnowledgeReview Component (TASK-WEB-KNOW-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockDoc: KnowledgeDocItem = {
    id: "kdoc-001",
    documentRef: "QD-2026-05",
    title: "Quy định Đóng học phí và Xét miễn giảm năm học 2026",
    status: "pending_review",
    authorId: "staff-author-01",
    department: "Phòng Kế hoạch Tài chính",
    version: "1.2.0",
  };

  it("enforces four-eyes principle by disabling self-approval for author", () => {
    render(
      <KnowledgeReview
        document={mockDoc}
        currentUserId="staff-author-01"
        onApprove={() => {}}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(true);
    expect(screen.getByText(/Quy tắc 4 mắt: Tác giả không thể tự phê duyệt tài liệu/i)).toBeDefined();
  });

  it("allows a different reviewer to approve document", () => {
    const handleApprove = vi.fn();
    render(
      <KnowledgeReview
        document={mockDoc}
        currentUserId="staff-reviewer-02"
        onApprove={handleApprove}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(false);

    fireEvent.click(approveBtn);
    expect(handleApprove).toHaveBeenCalledWith("kdoc-001");
  });
});
