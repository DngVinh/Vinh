import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { ActionConfirmation, type ActionPreviewData } from "./ActionConfirmation";

describe("ActionConfirmation Component (TASK-WEB-CONFIRM-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockAction: ActionPreviewData = {
    actionId: "act-preview-001",
    actionType: "DOCUMENT_REQUEST_SUBMIT",
    title: "Xác nhận gửi yêu cầu cấp giấy xác nhận sinh viên",
    targetEntity: "Sinh viên: Nguyễn Văn A (MSV: 12345)",
    parameters: [
      { label: "Loại giấy tờ", value: "Giấy xác nhận sinh viên" },
      { label: "Số lượng", value: "2 bản" },
    ],
    expiresInSeconds: 300,
  };

  it("renders immutable action details, parameters and countdown", () => {
    const handleConfirm = vi.fn();
    const handleCancel = vi.fn();

    render(
      <ActionConfirmation
        isOpen={true}
        action={mockAction}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeDefined();
    expect(screen.getByText("Xác nhận gửi yêu cầu cấp giấy xác nhận sinh viên")).toBeDefined();
    expect(screen.getByText("Sinh viên: Nguyễn Văn A (MSV: 12345)")).toBeDefined();
    expect(screen.getByText("Giấy xác nhận sinh viên")).toBeDefined();
    expect(screen.getByText("2 bản")).toBeDefined();

    // Confirm button
    const confirmBtn = screen.getByRole("button", { name: /Xác nhận thực hiện/i });
    expect(confirmBtn).toBeDefined();
    fireEvent.click(confirmBtn);
    expect(handleConfirm).toHaveBeenCalledWith("act-preview-001");

    // Cancel button
    const cancelBtn = screen.getByRole("button", { name: /Hủy bỏ/i });
    fireEvent.click(cancelBtn);
    expect(handleCancel).toHaveBeenCalledTimes(1);
  });

  it("disables confirm button when token countdown reaches zero", () => {
    const expiredAction: ActionPreviewData = {
      ...mockAction,
      expiresInSeconds: 0,
    };

    render(
      <ActionConfirmation
        isOpen={true}
        action={expiredAction}
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );

    expect(screen.getByText(/Phiên xác nhận đã hết hạn/i)).toBeDefined();
    const confirmBtn = screen.getByRole("button", { name: /Xác nhận thực hiện/i });
    expect(confirmBtn.hasAttribute("disabled")).toBe(true);
  });
});
