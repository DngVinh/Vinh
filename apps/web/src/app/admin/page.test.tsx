import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import AdminDashboardPage from "./page";

describe("AdminDashboardPage Component", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("renders key operational KPI cards and backlog metrics", () => {
    render(<AdminDashboardPage />);

    // KPI headings
    expect(screen.getByText(/Tổng hồ sơ tiếp nhận/i)).toBeDefined();
    expect(screen.getByText(/Tỷ lệ đúng hạn SLA/i)).toBeDefined();
    expect(screen.getByText(/Hồ sơ đang tồn đọng/i)).toBeDefined();
    expect(screen.getByText(/Mức độ hài lòng CSAT/i)).toBeDefined();

    // Specific KPI numbers
    expect(screen.getByText("98.5%")).toBeDefined();
  });

  it("supports configuring SLA turnaround times per document category", () => {
    render(<AdminDashboardPage />);

    // SLA configuration table
    expect(screen.getByText(/Cấu hình cam kết thời hạn xử lý \(SLA\)/i)).toBeDefined();
    expect(screen.getByText(/Bảng điểm tạm thời/i)).toBeDefined();

    // SLA adjustment
    const editBtn = screen.getByRole("button", { name: /Chỉnh sửa SLA Bảng điểm tạm thời/i });
    fireEvent.click(editBtn);

    const slaInput = screen.getByLabelText(/Thời hạn SLA mới \(giờ\)/i);
    fireEvent.change(slaInput, { target: { value: "36" } });

    const saveBtn = screen.getByRole("button", { name: /Lưu cấu hình SLA/i });
    fireEvent.click(saveBtn);

    expect(screen.getByText("36 giờ")).toBeDefined();
  });

  it("displays real-time audit log with actor attribution and export capability", () => {
    render(<AdminDashboardPage />);

    expect(screen.getByText(/Nhật ký kiểm toán Một cửa số \(Audit Trail\)/i)).toBeDefined();
    expect(screen.getByText(/staff-huce-01/i)).toBeDefined();

    // Export button
    const exportBtn = screen.getByRole("button", { name: /Xuất dữ liệu kiểm toán/i });
    expect(exportBtn).toBeDefined();
  });
});
