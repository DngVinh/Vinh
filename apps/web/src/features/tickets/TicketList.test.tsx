import React from "react";
import { describe, it, expect, afterEach, vi } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { TicketList, type StudentTicket } from "./TicketList";

describe("TicketList Component (TASK-WEB-TICK-002)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  const mockTickets: StudentTicket[] = [
    {
      id: "tck-001",
      code: "TCK-2026-0001",
      title: "Xin cấp giấy xác nhận sinh viên",
      category: "Giấy tờ học vụ",
      status: "waiting_student",
      createdAt: "2026-09-20",
      updatedAt: "2026-09-21 14:30",
      description: "Cần giấy xác nhận vay vốn ngân hàng chính sách.",
      nextAction: "Vui lòng đính kèm bản chụp CCCD hai mặt để hoàn tất hồ sơ.",
      events: [
        {
          id: "evt-1",
          timestamp: "2026-09-20 09:00",
          description: "Tiếp nhận hồ sơ trực tuyến.",
          actor: "Hệ thống Một cửa",
        },
        {
          id: "evt-2",
          timestamp: "2026-09-21 14:30",
          description: "Yêu cầu bổ sung ảnh chụp CCCD hai mặt.",
          actor: "Cán bộ phụ trách",
        },
      ],
      // Internal notes that MUST NEVER be rendered to student UI
      internalNotes: "Đã kiểm tra đối chiếu danh sách lớp, chờ sinh viên tải CCCD",
    } as any,
    {
      id: "tck-002",
      code: "TCK-2026-0002",
      title: "Đề nghị phúc khảo bài thi Kết cấu 1",
      category: "Khảo thí",
      status: "resolved",
      createdAt: "2026-09-18",
      updatedAt: "2026-09-22 10:00",
      description: "Đề nghị xem lại điểm phần bài tập lớn.",
      events: [
        {
          id: "evt-3",
          timestamp: "2026-09-18 08:30",
          description: "Hồ sơ đã được tiếp nhận.",
          actor: "Hệ thống Một cửa",
        },
        {
          id: "evt-4",
          timestamp: "2026-09-22 10:00",
          description: "Điểm phúc khảo đã cập nhật trên Cổng thông tin đào tạo.",
          actor: "Phòng Khảo thí & ĐBCL",
        },
      ],
    },
  ];

  it("renders student-centric status vocabulary conforming to UX-CONTENT-005", () => {
    render(<TicketList tickets={mockTickets} />);

    // waiting_student MUST be "Cần bạn bổ sung thông tin"
    expect(screen.getByText("Cần bạn bổ sung thông tin")).toBeDefined();
    // resolved MUST be "Đã có kết quả"
    expect(screen.getByText("Đã có kết quả")).toBeDefined();

    // Verify update time is displayed alongside submission time
    expect(screen.getByText(/Cập nhật: 2026-09-21 14:30/i)).toBeDefined();
  });

  it("presents actionable next steps when student action is required", () => {
    render(<TicketList tickets={mockTickets} />);

    // Next action banner/text for waiting_student
    expect(screen.getByText(/Vui lòng đính kèm bản chụp CCCD hai mặt để hoàn tất hồ sơ/i)).toBeDefined();
  });

  it("toggles detail view with aria-controls and shows ordered public history without exposing internal notes", () => {
    render(<TicketList tickets={mockTickets} />);

    const detailBtn = screen.getAllByRole("button", { name: /Chi tiết/i })[0];
    expect(detailBtn.getAttribute("aria-controls")).toBe("ticket-detail-tck-001");
    expect(detailBtn.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(detailBtn);
    expect(detailBtn.getAttribute("aria-expanded")).toBe("true");

    const detailPanel = document.getElementById("ticket-detail-tck-001");
    expect(detailPanel).not.toBeNull();

    // Public timeline events are shown
    expect(screen.getByText("Tiếp nhận hồ sơ trực tuyến.")).toBeDefined();
    expect(screen.getByText("Yêu cầu bổ sung ảnh chụp CCCD hai mặt.")).toBeDefined();

    // Internal notes MUST NOT appear anywhere in the DOM
    expect(screen.queryByText(/Đã kiểm tra đối chiếu danh sách lớp/i)).toBeNull();
  });

  it("distinguishes zero filter results from no tickets at all", () => {
    const { rerender } = render(<TicketList tickets={mockTickets} />);

    // Filter to active - wait, both mockTickets are active/resolved. Filter to something with zero results
    // Let's filter tickets with a specific search or filter that returns empty
    const filterButtons = screen.getAllByRole("button");
    // Filter to resolved tickets
    const resolvedBtn = screen.getByRole("button", { name: /Đã hoàn thành/i });
    fireEvent.click(resolvedBtn);
    expect(screen.getByText("TCK-2026-0002")).toBeDefined();

    // When there are no tickets at all
    rerender(<TicketList tickets={[]} />);
    expect(screen.getByText(/Bạn chưa có yêu cầu hỗ trợ nào/i)).toBeDefined();

    // When filtered results is empty
    rerender(
      <TicketList
        tickets={[
          {
            id: "tck-003",
            code: "TCK-2026-0003",
            title: "Đơn xin thôi học",
            category: "Học vụ",
            status: "resolved",
            createdAt: "2026-09-01",
            description: "Thôi học",
          },
        ]}
      />
    );
    const activeBtn = screen.getByRole("button", { name: /Đang xử lý/i });
    fireEvent.click(activeBtn);
    // Distinct empty state for filter: "Không có kết quả phù hợp"
    expect(screen.getByText(/Không có kết quả phù hợp/i)).toBeDefined();
  });

  it("supports copying ticket code with accessible status announcement", async () => {
    // Mock navigator.clipboard
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: writeTextMock },
      writable: true,
      configurable: true,
    });

    render(<TicketList tickets={mockTickets} />);

    const copyBtn = screen.getAllByRole("button", { name: /Sao chép mã TCK-2026-0001/i })[0];
    fireEvent.click(copyBtn);

    expect(writeTextMock).toHaveBeenCalledWith("TCK-2026-0001");
    // Live region status
    expect(await screen.findByRole("status")).toBeDefined();
  });
});
