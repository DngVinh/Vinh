import React, { useState } from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { AppShell } from "../src/components/AppShell";
import { TicketList, type StudentTicket } from "../src/features/tickets/TicketList";
import { ActionConfirmation, type ActionPreviewData } from "../src/features/actions/ActionConfirmation";

function TicketConfirmJourney({ initialExpired = false }: { initialExpired?: boolean }) {
  const [tickets, setTickets] = useState<StudentTicket[]>([
    {
      id: "tck-001",
      code: "TCK-2026-0001",
      title: "Xin cấp bảng điểm tạm thời",
      category: "Giấy tờ",
      status: "in_progress",
      createdAt: "2026-09-22",
      description: "Cần bảng điểm 5 kỳ đầu.",
    },
  ]);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const previewData: ActionPreviewData = {
    actionId: "act-preview-ticket-001",
    actionType: "TICKET_CREATE",
    title: "Xác nhận gửi yêu cầu hỗ trợ mới",
    targetEntity: "Sinh viên: Trần Văn B",
    parameters: [
      { label: "Tiêu đề", value: "Đăng ký cấp lại thẻ sinh viên" },
      { label: "Phòng ban", value: "Công tác sinh viên" },
    ],
    expiresInSeconds: initialExpired ? 0 : 300,
  };

  const handleConfirm = () => {
    setIsPreviewOpen(false);
    setTickets((prev) => [
      ...prev,
      {
        id: "tck-002",
        code: "TCK-2026-0002",
        title: "Đăng ký cấp lại thẻ sinh viên",
        category: "Thẻ SV",
        status: "submitted",
        createdAt: "2026-09-22",
        description: "Bị mất thẻ sinh viên tại thư viện.",
      },
    ]);
  };

  return React.createElement(
    AppShell,
    null,
    React.createElement(
      "div",
      { className: "p-4" },
      React.createElement(
        "button",
        {
          onClick: () => setIsPreviewOpen(true),
          className: "mb-4 px-4 py-2 bg-blue-600 text-white rounded",
        },
        "Tạo yêu cầu hỗ trợ mới"
      ),
      React.createElement(TicketList, { tickets }),
      React.createElement(ActionConfirmation, {
        isOpen: isPreviewOpen,
        action: previewData,
        onConfirm: handleConfirm,
        onCancel: () => setIsPreviewOpen(false),
      })
    )
  );
}

describe("Confirmed Ticket Browser Journey E2E (TASK-TEST-E2E-002)", () => {
  afterEach(() => {
    cleanup();
  });

  it("completes preview and confirmation flow to create new ticket", () => {
    render(React.createElement(TicketConfirmJourney));

    // 1. Initial ticket present
    expect(screen.getByText("TCK-2026-0001")).toBeDefined();
    expect(screen.queryByText("TCK-2026-0002")).toBeNull();

    // 2. Click create -> opens preview modal
    const createBtn = screen.getByRole("button", { name: "Tạo yêu cầu hỗ trợ mới" });
    fireEvent.click(createBtn);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeDefined();
    expect(screen.getByText("Xác nhận gửi yêu cầu hỗ trợ mới")).toBeDefined();
    expect(screen.getByText("Đăng ký cấp lại thẻ sinh viên")).toBeDefined();

    // 3. Confirm action
    const confirmBtn = screen.getByRole("button", { name: /Xác nhận thực hiện/i });
    fireEvent.click(confirmBtn);

    // 4. Modal closes and new ticket is listed
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByText("TCK-2026-0002")).toBeDefined();
  });

  it("negative path: blocks confirmation when preview token is expired", () => {
    render(React.createElement(TicketConfirmJourney, { initialExpired: true }));

    const createBtn = screen.getByRole("button", { name: "Tạo yêu cầu hỗ trợ mới" });
    fireEvent.click(createBtn);

    expect(screen.getByText(/Phiên xác nhận đã hết hạn/i)).toBeDefined();
    const confirmBtn = screen.getByRole("button", { name: /Xác nhận thực hiện/i });
    expect(confirmBtn.hasAttribute("disabled")).toBe(true);
  });
});
