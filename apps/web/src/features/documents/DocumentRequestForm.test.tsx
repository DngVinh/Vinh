import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { DocumentRequestForm } from "./DocumentRequestForm";

describe("DocumentRequestForm Component (TASK-WEB-DOCREQ-001)", () => {
  afterEach(() => {
    cleanup();
  });

  it("submits valid form data and triggers submit callback", () => {
    const handleSubmit = vi.fn();
    render(<DocumentRequestForm onSubmit={handleSubmit} />);

    const docTypeSelect = screen.getByLabelText(/Loại giấy tờ/i);
    const quantityInput = screen.getByLabelText(/Số lượng bản/i);
    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i);
    const submitBtn = screen.getByRole("button", { name: /Tiếp tục xác nhận/i });

    fireEvent.change(docTypeSelect, { target: { value: "xac_nhan_sinh_vien" } });
    fireEvent.change(quantityInput, { target: { value: "2" } });
    fireEvent.change(reasonInput, { target: { value: "Vay vốn sinh viên chính sách" } });
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledWith({
      documentType: "xac_nhan_sinh_vien",
      quantity: 2,
      reason: "Vay vốn sinh viên chính sách",
    });
  });

  it("negative path: validates required fields before submitting", () => {
    const handleSubmit = vi.fn();
    render(<DocumentRequestForm onSubmit={handleSubmit} />);

    const submitBtn = screen.getByRole("button", { name: /Tiếp tục xác nhận/i });
    fireEvent.click(submitBtn);

    expect(screen.getByText(/Vui lòng nhập mục đích xin cấp/i)).toBeDefined();
    expect(handleSubmit).not.toHaveBeenCalled();
  });
});
