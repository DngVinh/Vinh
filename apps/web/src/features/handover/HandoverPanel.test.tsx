import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { HandoverPanel, type HandoverReceipt } from "./HandoverPanel";

describe("HandoverPanel Component (TASK-WEB-HITL-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockReceipt: HandoverReceipt = {
    receiptId: "rcpt-hitl-001",
    department: "Phòng Đào tạo & Quản lý Sinh viên",
    reason: "Vấn đề khiếu nại điểm thi vượt thẩm quyền AI",
    assignedQueue: "QUEUE_EXAM_REVIEW",
    estimatedResponseHours: 4,
    status: "queued",
  };

  it("renders handover receipt with department and estimated response time", () => {
    render(<HandoverPanel receipt={mockReceipt} isAvailable={true} />);

    expect(screen.getByText(/Chuyển tiếp chuyên viên hỗ trợ/i)).toBeDefined();
    expect(screen.getByText("Phòng Đào tạo & Quản lý Sinh viên")).toBeDefined();
    expect(screen.getByText(/Thời gian phản hồi dự kiến: 4 giờ/i)).toBeDefined();
    expect(screen.getByText(/Mã biên nhận: rcpt-hitl-001/i)).toBeDefined();
  });

  it("renders emergency modal toggle and hotlines accessibly", () => {
    render(<HandoverPanel receipt={mockReceipt} isAvailable={true} />);

    const emergencyBtn = screen.getByRole("button", { name: /Đường dây nóng khẩn cấp/i });
    fireEvent.click(emergencyBtn);

    expect(screen.getByText(/Hotline Y tế & Tâm lý HUCE/i)).toBeDefined();
    expect(screen.getByText("024-3869-XXXX")).toBeDefined();
  });

  it("renders unavailable state outside working hours", () => {
    render(<HandoverPanel receipt={mockReceipt} isAvailable={false} />);

    expect(screen.getByText(/Hiện ngoài giờ tiếp nhận trực tuyến/i)).toBeDefined();
    expect(screen.getByText(/Yêu cầu của bạn đã được ghi nhận vào hàng đợi/i)).toBeDefined();
  });
});
