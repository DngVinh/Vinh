import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { DocumentRequestForm } from "./DocumentRequestForm";

describe("DocumentRequestForm Component (TASK-WEB-DOCREQ-002)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("requires explicit confirmation: preview first, never submit before confirmation", () => {
    const handleSubmit = vi.fn();
    render(<DocumentRequestForm onSubmit={handleSubmit} />);

    // Fill the form in editing state
    const docTypeSelect = screen.getByLabelText(/Loại giấy tờ/i);
    const quantityInput = screen.getByLabelText(/Số lượng bản/i);
    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i);
    const previewBtn = screen.getByRole("button", { name: /Xem trước yêu cầu/i });

    fireEvent.change(docTypeSelect, { target: { value: "xac_nhan_sinh_vien" } });
    fireEvent.change(quantityInput, { target: { value: "2" } });
    fireEvent.change(reasonInput, { target: { value: "Vay vốn sinh viên chính sách" } });

    // Step 1: Click preview button
    fireEvent.click(previewBtn);

    // CRITICAL (AC-TASK-WEB-DOCREQ-002-02): onSubmit MUST NOT be called prior to explicit confirmation
    expect(handleSubmit).not.toHaveBeenCalled();

    // Verify preview screen shows required structured fields: doc type, delivery, fee, timing, reason
    expect(screen.getByText(/Xác nhận thông tin yêu cầu/i)).toBeDefined();
    expect(screen.getByText(/Giấy xác nhận sinh viên/i)).toBeDefined();
    expect(screen.getByText(/2 bản/i)).toBeDefined();
    expect(screen.getByText(/Miễn phí/i)).toBeDefined();
    expect(screen.getByText(/1 - 2 ngày làm việc/i)).toBeDefined();
    expect(screen.getByText("Vay vốn sinh viên chính sách")).toBeDefined();

    // Step 2: Click explicit confirmation CTA
    const confirmBtn = screen.getByRole("button", { name: /Gửi yêu cầu/i });
    fireEvent.click(confirmBtn);

    // Now onSubmit MUST have been called with complete payload
    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        documentType: "xac_nhan_sinh_vien",
        quantity: 2,
        reason: "Vay vốn sinh viên chính sách",
      })
    );
  });

  it("supports returning to edit mode from preview without losing user input", () => {
    const handleSubmit = vi.fn();
    render(<DocumentRequestForm onSubmit={handleSubmit} />);

    fireEvent.change(screen.getByLabelText(/Mục đích xin cấp/i), {
      target: { value: "Xin học bổng khuyến khích" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Xem trước yêu cầu/i }));

    expect(screen.getByText("Xin học bổng khuyến khích")).toBeDefined();

    // Click back to edit
    const editBtn = screen.getByRole("button", { name: /Quay lại chỉnh sửa/i });
    fireEvent.click(editBtn);

    // Verify form is editable again and preserves entered value
    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i) as HTMLTextAreaElement;
    expect(reasonInput.value).toBe("Xin học bổng khuyến khích");
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("validates inline with aria-describedby and role=alert on missing required fields", () => {
    const handleSubmit = vi.fn();
    render(<DocumentRequestForm onSubmit={handleSubmit} />);

    const previewBtn = screen.getByRole("button", { name: /Xem trước yêu cầu/i });
    fireEvent.click(previewBtn);

    // Error announcement
    const alert = screen.getByRole("alert");
    expect(alert).toBeDefined();
    expect(screen.getByText(/Vui lòng nhập mục đích xin cấp/i)).toBeDefined();

    // Textarea has aria-invalid and aria-describedby
    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i);
    expect(reasonInput.getAttribute("aria-invalid")).toBe("true");
    expect(reasonInput.getAttribute("aria-describedby")).toBe("reason-error");

    expect(handleSubmit).not.toHaveBeenCalled();
  });
});
