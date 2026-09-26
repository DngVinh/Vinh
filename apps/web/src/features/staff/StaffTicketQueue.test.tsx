import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { StaffTicketQueue, type StaffQueueItem } from "./StaffTicketQueue";

describe("StaffTicketQueue Component (TASK-WEB-STAFF-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockItems: StaffQueueItem[] = [
    {
      id: "queue-001",
      ticketCode: "TCK-2026-0101",
      studentName: "Trần Văn B",
      studentId: "1912345",
      title: "Đơn xin miễn giảm học phí",
      status: "unassigned",
      priority: "high",
      createdAt: "2026-09-22 09:00",
    },
    {
      id: "queue-002",
      ticketCode: "TCK-2026-0102",
      studentName: "Lê Thị C",
      studentId: "2012346",
      title: "Xin cấp lại thẻ sinh viên",
      status: "assigned",
      assignedStaffId: "staff-huce-01",
      priority: "normal",
      createdAt: "2026-09-22 09:30",
    },
  ];

  it("renders queue items and supports atomic claim", () => {
    const handleClaim = vi.fn();
    render(
      <StaffTicketQueue
        items={mockItems}
        currentStaffId="staff-huce-01"
        onClaimTicket={handleClaim}
      />
    );

    expect(screen.getByText("TCK-2026-0101")).toBeDefined();
    expect(screen.getByText("Đơn xin miễn giảm học phí")).toBeDefined();
    expect(screen.getByText("Trần Văn B (1912345)")).toBeDefined();

    // Claim unassigned ticket
    const claimBtn = screen.getByRole("button", { name: /Nhận xử lý TCK-2026-0101/i });
    fireEvent.click(claimBtn);

    expect(handleClaim).toHaveBeenCalledWith("queue-001");
  });

  it("negative path: disables claim button for tickets already claimed by others", () => {
    render(
      <StaffTicketQueue
        items={mockItems}
        currentStaffId="staff-huce-99"
        onClaimTicket={() => {}}
      />
    );

    const alreadyClaimedBtn = screen.getByRole("button", { name: /Đã nhận - TCK-2026-0102/i });
    expect(alreadyClaimedBtn.hasAttribute("disabled")).toBe(true);
  });
});
