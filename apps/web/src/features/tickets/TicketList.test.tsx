import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { TicketList, type StudentTicket } from "./TicketList";

describe("TicketList Component (TASK-WEB-TICKET-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockTickets: StudentTicket[] = [
    {
      id: "tck-001",
      code: "TCK-2026-0001",
      title: "Xin cấp giấy xác nhận sinh viên",
      category: "Giấy tờ",
      status: "in_progress",
      createdAt: "2026-09-20",
      description: "Cần giấy xác nhận vay vốn ngân hàng chính sách.",
    },
    {
      id: "tck-002",
      code: "TCK-2026-0002",
      title: "Đề nghị phúc khảo bài thi Kết cấu 1",
      category: "Khảo thí",
      status: "resolved",
      createdAt: "2026-09-18",
      description: "Đề nghị xem lại điểm phần bài tập lớn.",
    },
  ];

  it("renders ticket list and toggles detail view accessibly", () => {
    render(<TicketList tickets={mockTickets} />);

    expect(screen.getByText("TCK-2026-0001")).toBeDefined();
    expect(screen.getByText("Xin cấp giấy xác nhận sinh viên")).toBeDefined();
    expect(screen.getByText("TCK-2026-0002")).toBeDefined();

    // Toggle detail
    const detailBtn = screen.getAllByRole("button", { name: /Chi tiết/i })[0];
    fireEvent.click(detailBtn);

    expect(screen.getByText("Cần giấy xác nhận vay vốn ngân hàng chính sách.")).toBeDefined();
  });

  it("filters tickets by active status", async () => {
    const { fireEvent } = await import("@testing-library/react");
    render(<TicketList tickets={mockTickets} />);

    const activeFilterBtn = screen.getByRole("button", { name: /Đang xử lý/i });
    fireEvent.click(activeFilterBtn);

    expect(screen.getByText("TCK-2026-0001")).toBeDefined();
    expect(screen.queryByText("TCK-2026-0002")).toBeNull();
  });

  it("renders empty state when ticket list is empty", () => {
    render(<TicketList tickets={[]} />);
    expect(screen.getByText(/Bạn chưa có yêu cầu hỗ trợ nào/i)).toBeDefined();
  });
});
