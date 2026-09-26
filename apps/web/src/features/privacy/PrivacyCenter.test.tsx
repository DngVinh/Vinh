import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { PrivacyCenter, type PrivacyNoticeData, type PrivacyRequestStatus } from "./PrivacyCenter";

describe("PrivacyCenter Component (TASK-WEB-PRIV-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockNotice: PrivacyNoticeData = {
    version: "2026.1",
    effectiveDate: "2026-09-01",
    purpose: "Thu thập câu hỏi học tập và thông tin tài khoản sinh viên nhằm mục đích giải đáp thắc mắc và hỗ trợ một cửa số trong khuôn khổ HUCE Demo.",
    hasConsented: false,
  };

  const mockRequests: PrivacyRequestStatus[] = [
    {
      requestId: "pr-001",
      requestType: "EXPORT_DATA",
      status: "processing",
      submittedAt: "2026-09-21",
    },
  ];

  it("displays notice version and purpose clearly before consent interaction", () => {
    const handleConsent = vi.fn();
    render(
      <PrivacyCenter
        notice={mockNotice}
        requests={mockRequests}
        onConsentChange={handleConsent}
      />
    );

    expect(screen.getByText(/Phiên bản: 2026.1/i)).toBeDefined();
    expect(screen.getByText(/Mục đích xử lý dữ liệu/i)).toBeDefined();
    expect(screen.getByText(/Thu thập câu hỏi học tập/i)).toBeDefined();

    const consentCheckbox = screen.getByRole("checkbox", {
      name: /Tôi đồng ý với chính sách xử lý dữ liệu/i,
    });
    fireEvent.click(consentCheckbox);

    expect(handleConsent).toHaveBeenCalledWith(true);
  });

  it("announces request status accessibly without exposing internal operator notes", () => {
    render(
      <PrivacyCenter
        notice={mockNotice}
        requests={mockRequests}
      />
    );

    const liveRegion = screen.getByText(/Đang xử lý xuất dữ liệu/i);
    expect(liveRegion).toBeDefined();

    // Ensure NO internal notes or internal system pointers are present
    expect(screen.queryByText(/internal_note/i)).toBeNull();
    expect(screen.queryByText(/db_row_id/i)).toBeNull();
  });
});
