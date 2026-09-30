import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { ActionOutcome } from "./ActionOutcome";

describe("ActionOutcome Component (TASK-WEB-RESULT-001)", () => {
  afterEach(() => {
    cleanup();
  });

  it("never represents ambiguous transport failure as success or definite failure (AC-TASK-WEB-RESULT-001-01)", () => {
    render(
      <ActionOutcome
        state="result_unknown"
        idempotencyKey="idem-test-001"
        actionTitle="Đặt mượn phòng hội thảo H1-102"
        correlationId="corr-xyz-789"
      />
    );

    // Shows ambiguous result-unknown banner, NOT success or definite failure
    expect(screen.getByText(/Kết quả chưa xác định/i)).toBeDefined();
    expect(screen.getByText(/chưa nhận được phản hồi xác nhận chắc chắn/i)).toBeDefined();
    expect(screen.queryByText(/Thao tác thành công/i)).toBeNull();
    expect(screen.queryByText(/Thao tác thất bại hoàn toàn/i)).toBeNull();
    // Exposes correlation reference
    expect(screen.getByText(/corr-xyz-789/i)).toBeDefined();
  });

  it("blocks unsafe retry while the same idempotency identity is unresolved (AC-TASK-WEB-RESULT-001-02)", () => {
    const handleRetry = vi.fn();
    render(
      <ActionOutcome
        state="result_unknown"
        idempotencyKey="idem-test-001"
        actionTitle="Đặt mượn phòng"
        onRetry={handleRetry}
      />
    );

    // Unsafe re-submit button must be strictly disabled or absent
    const resubmitBtn = screen.queryByRole("button", { name: /Gửi lại yêu cầu/i });
    if (resubmitBtn) {
      expect(resubmitBtn.hasAttribute("disabled")).toBe(true);
    }
    expect(screen.getByText(/tránh thao tác trùng lặp/i)).toBeDefined();
  });

  it("supports authoritative reconciliation updating the same record without duplicate confirmation (AC-TASK-WEB-RESULT-001-03)", () => {
    const handleReconcile = vi.fn();
    render(
      <ActionOutcome
        state="result_unknown"
        idempotencyKey="idem-test-001"
        actionTitle="Đặt mượn phòng"
        onReconcile={handleReconcile}
      />
    );

    const reconcileBtn = screen.getByRole("button", { name: /Kiểm tra đối soát trạng thái/i });
    fireEvent.click(reconcileBtn);

    expect(handleReconcile).toHaveBeenCalledWith("idem-test-001");
  });

  it("renders succeeded and failed states distinctly", () => {
    const { rerender } = render(
      <ActionOutcome
        state="succeeded"
        idempotencyKey="idem-ok-1"
        actionTitle="Đặt mượn phòng"
      />
    );
    expect(screen.getByText(/Thực hiện thành công/i)).toBeDefined();

    rerender(
      <ActionOutcome
        state="failed"
        idempotencyKey="idem-fail-1"
        actionTitle="Đặt mượn phòng"
        errorMessage="Phòng đã có lịch học trùng"
      />
    );
    expect(screen.getByText(/Thao tác thất bại/i)).toBeDefined();
    expect(screen.getByText(/Phòng đã có lịch học trùng/i)).toBeDefined();
  });
});
