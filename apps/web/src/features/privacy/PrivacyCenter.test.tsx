import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { PrivacyCenter, type PrivacyNoticeData, type PrivacyRequestStatus } from "./PrivacyCenter";

describe("PrivacyCenter Component (TASK-WEB-PRIV-002)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  const mockNotice: PrivacyNoticeData = {
    version: "2026.1",
    effectiveDate: "01/09/2026",
    purpose: "Thu thập câu hỏi học tập và thông tin tài khoản sinh viên nhằm mục đích giải đáp thắc mắc và hỗ trợ một cửa số trong khuôn khổ HUCE Demo.",
    hasConsented: false,
  };

  const mockRequests: PrivacyRequestStatus[] = [
    {
      requestId: "pr-001",
      requestType: "EXPORT_DATA",
      status: "processing",
      submittedAt: "21/09/2026",
    },
    {
      requestId: "pr-002",
      requestType: "DELETE_DATA",
      status: "completed",
      submittedAt: "15/09/2026",
    },
  ];

  it("distinguishes required core processing from optional processing", () => {
    render(<PrivacyCenter notice={mockNotice} requests={mockRequests} />);

    // Required processing section
    expect(screen.getByText(/Xử lý dữ liệu bắt buộc/i)).toBeDefined();
    expect(screen.getByText(/vận hành tài khoản và dịch vụ Một cửa số/i)).toBeDefined();

    // Optional processing section
    expect(screen.getByText(/Xử lý dữ liệu tùy chọn/i)).toBeDefined();
  });

  it("preserves version and effective date directly adjacent to the consent control", () => {
    render(<PrivacyCenter notice={mockNotice} requests={mockRequests} />);

    expect(screen.getByText(/Phiên bản 2026.1 · Có hiệu lực từ 01\/09\/2026/i)).toBeDefined();
  });

  it("never preselects consent by default and updates consent state with accessible feedback", () => {
    const handleConsentChange = vi.fn();
    render(
      <PrivacyCenter
        notice={mockNotice}
        requests={mockRequests}
        onConsentChange={handleConsentChange}
      />
    );

    const checkbox = screen.getByRole("checkbox", {
      name: /Đồng ý chia sẻ dữ liệu hội thoại ẩn danh để nâng cao chất lượng AI/i,
    }) as HTMLInputElement;

    // Consent MUST NOT be preselected (AC-TASK-WEB-PRIV-002-02)
    expect(checkbox.checked).toBe(false);

    fireEvent.click(checkbox);
    expect(checkbox.checked).toBe(true);
    expect(handleConsentChange).toHaveBeenCalledWith(true);

    // Live status announcement
    expect(screen.getByRole("status")).toBeDefined();
  });

  it("displays transparent privacy request statuses without exposing internal identifiers", () => {
    render(<PrivacyCenter notice={mockNotice} requests={mockRequests} />);

    expect(screen.getByText(/Yêu cầu xuất dữ liệu cá nhân/i)).toBeDefined();
    expect(screen.getByText(/Yêu cầu xóa dữ liệu cá nhân/i)).toBeDefined();

    // Verify no internal technical artifacts leaked
    expect(screen.queryByText(/internal_note/i)).toBeNull();
    expect(screen.queryByText(/db_row_id/i)).toBeNull();
    expect(screen.queryByText(/tenant_id/i)).toBeNull();
  });

  it("does not imply consent or completion when pending server confirmation (AC-TASK-WEB-PRIV-003-01)", () => {
    render(
      <PrivacyCenter
        notice={mockNotice}
        requests={mockRequests}
        isPendingConfirmation={true}
      />
    );

    expect(screen.getByText(/Đang chờ máy chủ xác nhận/i)).toBeDefined();
    const checkbox = screen.getByRole("checkbox") as HTMLInputElement;
    expect(checkbox.hasAttribute("disabled")).toBe(true);
  });

  it("requires explicit confirmation and displays scope and effect for consequential actions (AC-TASK-WEB-PRIV-003-02)", () => {
    const handleErasure = vi.fn();
    render(
      <PrivacyCenter
        notice={mockNotice}
        requests={mockRequests}
        onRequestErasure={handleErasure}
      />
    );

    const triggerBtn = screen.getByRole("button", { name: /Yêu cầu xóa dữ liệu vĩnh viễn/i });
    fireEvent.click(triggerBtn);

    // Confirm dialog / card appears with explicit scope and effect
    expect(screen.getByText(/Phạm vi áp dụng:/i)).toBeDefined();
    expect(screen.getByText(/Hệ quả pháp lý:/i)).toBeDefined();
    expect(screen.getByText(/Hành động không thể hoàn tác/i)).toBeDefined();

    // Action not called until explicit confirmation button clicked
    expect(handleErasure).not.toHaveBeenCalled();

    const confirmBtn = screen.getByRole("button", { name: /Xác nhận xóa vĩnh viễn/i });
    fireEvent.click(confirmBtn);
    expect(handleErasure).toHaveBeenCalledTimes(1);
  });

  it("explains legal hold and denial truthfully without leaking restricted data (AC-TASK-WEB-PRIV-003-03)", () => {
    const legalHoldRequests: PrivacyRequestStatus[] = [
      {
        requestId: "pr-hold-01",
        requestType: "DELETE_DATA",
        status: "legal_hold",
        submittedAt: "25/09/2026",
      },
      {
        requestId: "pr-denied-02",
        requestType: "DELETE_DATA",
        status: "denied",
        submittedAt: "20/09/2026",
      },
    ];

    render(<PrivacyCenter notice={mockNotice} requests={legalHoldRequests} />);

    expect(screen.getByText(/Tạm giữ pháp lý/i)).toBeDefined();
    expect(screen.getByText(/Dữ liệu đang được lưu trữ bắt buộc theo quy định/i)).toBeDefined();

    expect(screen.getByText(/Bị từ chối theo quy định/i)).toBeDefined();
    expect(screen.getByText(/Yêu cầu không thể thực hiện do không đáp ứng quy định/i)).toBeDefined();

    // No leaked secrets or internal tags
    expect(screen.queryByText(/restricted_policy/i)).toBeNull();
    expect(screen.queryByText(/secret_evidence/i)).toBeNull();
  });
});
