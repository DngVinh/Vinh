import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { KnowledgeReview, type KnowledgeDocItem } from "./KnowledgeReview";

describe("KnowledgeReview Component (TASK-WEB-KNOW-002)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockCompleteDoc: KnowledgeDocItem = {
    id: "kdoc-001",
    documentRef: "QD-2026-05",
    title: "Quy định Đóng học phí và Xét miễn giảm năm học 2026",
    status: "pending_review",
    authorId: "staff-author-01",
    department: "Phòng Kế hoạch Tài chính",
    version: "1.2.0",
    effectiveFrom: "01/01/2026",
    effectiveTo: "31/12/2026",
    freshnessStatus: "fresh",
    parseStatus: "parsed",
    reviewEvidenceComplete: true,
    chunks: [
      {
        id: "chunk-01",
        locator: "Điều 4, Khoản 1, Trang 2",
        content: "Sinh viên diện chính sách nghèo được giảm 100% học phí theo quy định hiện hành.",
        wordCount: 16,
      },
      {
        id: "chunk-02",
        locator: "Điều 4, Khoản 2, Trang 3",
        content: "Hồ sơ xin miễn giảm nộp trước ngày 30/10 hàng năm tại bộ phận Một cửa.",
        wordCount: 17,
      },
    ],
  };

  it("enforces four-eyes principle by disabling self-approval for author", () => {
    render(
      <KnowledgeReview
        document={mockCompleteDoc}
        currentUserId="staff-author-01"
        onApprove={() => {}}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(true);
    expect(screen.getByText(/Quy tắc 4 mắt: Tác giả không thể tự phê duyệt tài liệu/i)).toBeDefined();
  });

  it("allows a different reviewer to approve document when evidence is complete", () => {
    const handleApprove = vi.fn();
    render(
      <KnowledgeReview
        document={mockCompleteDoc}
        currentUserId="staff-reviewer-02"
        onApprove={handleApprove}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(false);

    fireEvent.click(approveBtn);
    expect(handleApprove).toHaveBeenCalledWith("kdoc-001");
  });

  it("renders source-to-chunk hierarchy with locators and chunk contents", () => {
    render(
      <KnowledgeReview
        document={mockCompleteDoc}
        currentUserId="staff-reviewer-02"
      />
    );

    expect(screen.getByText("Điều 4, Khoản 1, Trang 2")).toBeDefined();
    expect(screen.getByText(/Sinh viên diện chính sách nghèo được giảm 100%/i)).toBeDefined();
    expect(screen.getByText("Điều 4, Khoản 2, Trang 3")).toBeDefined();
  });

  it("displays parse status and freshness status transparently", () => {
    render(
      <KnowledgeReview
        document={mockCompleteDoc}
        currentUserId="staff-reviewer-02"
      />
    );

    expect(screen.getByText(/Trạng thái trích xuất/i)).toBeDefined();
    expect(screen.getByText(/Đã phân tích cú pháp/i)).toBeDefined();
    expect(screen.getByText(/Hiệu lực: 01\/01\/2026 - 31\/12\/2026/i)).toBeDefined();
  });

  it("prevents publish when review evidence is incomplete with accessible explanation", () => {
    const incompleteDoc: KnowledgeDocItem = {
      ...mockCompleteDoc,
      reviewEvidenceComplete: false,
      warnings: ["Thiếu bằng chứng đối chiếu kiểm định (Eval evidence)"],
    };

    render(
      <KnowledgeReview
        document={incompleteDoc}
        currentUserId="staff-reviewer-02"
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(true);

    expect(screen.getByText(/Chưa đủ bằng chứng thẩm định/i)).toBeDefined();
    expect(screen.getByText(/Thiếu bằng chứng đối chiếu kiểm định/i)).toBeDefined();
  });

  it("prevents publish when parsing has failed", () => {
    const failedParseDoc: KnowledgeDocItem = {
      ...mockCompleteDoc,
      parseStatus: "failed",
      chunks: [],
    };

    render(
      <KnowledgeReview
        document={failedParseDoc}
        currentUserId="staff-reviewer-02"
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(true);
    expect(screen.getAllByText(/Lỗi trích xuất cú pháp/i).length).toBeGreaterThanOrEqual(1);
  });

  it("renders non-color-dependent warning indicators for chunk issues", () => {
    const docWithChunkWarning: KnowledgeDocItem = {
      ...mockCompleteDoc,
      chunks: [
        {
          id: "chunk-w1",
          locator: "Điều 9, Mục 3",
          content: "Đoạn văn bản có dấu hiệu xung đột với Quyết định 12.",
          warnings: ["Xung đột tiềm ẩn với QĐ-2025-12"],
        },
      ],
    };

    render(
      <KnowledgeReview
        document={docWithChunkWarning}
        currentUserId="staff-reviewer-02"
      />
    );

    expect(screen.getByText(/\[CẢNH BÁO\]/i)).toBeDefined();
    expect(screen.getByText(/Xung đột tiềm ẩn với QĐ-2025-12/i)).toBeDefined();
  });

  it("disables publish if user role lacks publish authority (AC-TASK-WEB-KNOW-003-02)", () => {
    render(
      <KnowledgeReview
        document={mockCompleteDoc}
        currentUserId="staff-reviewer-02"
        userRole="STAFF"
        onApprove={() => {}}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(true);
    expect(screen.getByText(/Không có thẩm quyền ban hành/i)).toBeDefined();
  });

  it("disables approve when document is stale or version changed (AC-TASK-WEB-KNOW-003-01)", () => {
    const staleDoc: KnowledgeDocItem = {
      ...mockCompleteDoc,
      freshnessStatus: "stale",
      isStale: true,
    };

    render(
      <KnowledgeReview
        document={staleDoc}
        currentUserId="staff-reviewer-02"
        userRole="ADMIN"
        onApprove={() => {}}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(true);
    expect(screen.getByText(/Văn bản đã bị thay đổi hoặc hết hạn/i)).toBeDefined();
  });

  it("displays quarantine warning and blocks approval when quarantined (AC-TASK-WEB-KNOW-003-03)", () => {
    const quarantinedDoc: KnowledgeDocItem = {
      ...mockCompleteDoc,
      quarantineStatus: true,
      policyViolations: ["Phát hiện chỉ thị prompt injection độc hại"],
    };

    render(
      <KnowledgeReview
        document={quarantinedDoc}
        currentUserId="staff-reviewer-02"
        userRole="ADMIN"
        onApprove={() => {}}
      />
    );

    const approveBtn = screen.getByRole("button", { name: /Phê duyệt ban hành/i });
    expect(approveBtn.hasAttribute("disabled")).toBe(true);
    expect(screen.getByText(/\[CÁCH LY KIỂM DUYỆT\]/i)).toBeDefined();
    expect(screen.getByText(/Phát hiện chỉ thị prompt injection độc hại/i)).toBeDefined();
  });

  it("renders immutable provenance attributes: sourceUri and contentHash (AC-TASK-WEB-KNOW-003-03)", () => {
    const docWithProvenance: KnowledgeDocItem = {
      ...mockCompleteDoc,
      sourceUri: "https://huce.edu.vn/docs/qd-2026-05.pdf",
      contentHash: "sha256:abcd1234ef5678",
    };

    render(
      <KnowledgeReview
        document={docWithProvenance}
        currentUserId="staff-reviewer-02"
        userRole="ADMIN"
      />
    );

    expect(screen.getByText(/Nguồn gốc xuất xứ/i)).toBeDefined();
    expect(screen.getByText(/https:\/\/huce\.edu\.vn\/docs\/qd-2026-05\.pdf/i)).toBeDefined();
    expect(screen.getByText(/sha256:abcd1234ef5678/i)).toBeDefined();
  });
});
