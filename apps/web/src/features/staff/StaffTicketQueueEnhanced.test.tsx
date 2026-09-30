import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { StaffTicketQueue, type StaffQueueItem } from "./StaffTicketQueue";

describe("StaffTicketQueue Enhanced Checklist & AI Support", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  const mockItems: StaffQueueItem[] = [
    {
      id: "queue-001",
      ticketCode: "TCK-2026-0101",
      studentName: "Trần Văn B",
      studentId: "1912345",
      title: "Đơn xin miễn giảm học phí",
      publicContent: "Em xin nộp bổ sung giấy xác nhận hộ nghèo năm 2026.",
      internalNotes: "Đã kiểm tra sơ bộ hồ sơ trên Cổng thông tin, cần xác minh dấu đỏ.",
      status: "unassigned",
      priority: "urgent",
      createdAt: "2026-09-22 09:00",
      age: "45 phút",
    },
    {
      id: "queue-002",
      ticketCode: "TCK-2026-0102",
      studentName: "Lê Thị C",
      studentId: "2012346",
      title: "Xin cấp lại thẻ sinh viên",
      publicContent: "Thẻ bị gãy chip từ tuần trước.",
      status: "assigned",
      assignedStaffId: "staff-huce-01",
      priority: "normal",
      createdAt: "2026-09-22 09:30",
      age: "15 phút",
    },
  ];

  it("filters items by search query matching code, student name or title", () => {
    render(<StaffTicketQueue items={mockItems} currentStaffId="staff-huce-01" />);

    const searchInput = screen.getByPlaceholderText(/Tìm theo mã, tên sinh viên hoặc tiêu đề/i);
    fireEvent.change(searchInput, { target: { value: "Lê Thị C" } });

    expect(screen.getByText("TCK-2026-0102")).toBeDefined();
    expect(screen.queryByText("TCK-2026-0101")).toBeNull();
  });

  it("renders adaptive intake checklist with verification gates in expanded detail", () => {
    render(<StaffTicketQueue items={mockItems} currentStaffId="staff-huce-01" />);

    // Expand queue-001
    const detailBtn = screen.getByRole("button", { name: /Chi tiết TCK-2026-0101/i });
    fireEvent.click(detailBtn);

    // Checklist heading and items should be visible
    expect(screen.getByText(/Checklist tiếp nhận hồ sơ/i)).toBeDefined();
    expect(screen.getByText(/Xác minh danh tính & MSSV/i)).toBeDefined();
    expect(screen.getByText(/Kiểm tra tính hợp lệ minh chứng đính kèm/i)).toBeDefined();

    // Check completion gate: button to finalize intake is disabled until checklist items are checked or exception reason provided
    const finalizeBtn = screen.getByRole("button", { name: /Xác nhận hoàn tất tiếp nhận/i });
    expect(finalizeBtn.hasAttribute("disabled")).toBe(true);
  });

  it("renders AI Copilot summary and suggested response templates", () => {
    render(<StaffTicketQueue items={mockItems} currentStaffId="staff-huce-01" />);

    const detailBtn = screen.getByRole("button", { name: /Chi tiết TCK-2026-0101/i });
    fireEvent.click(detailBtn);

    // AI Copilot badge
    expect(screen.getByText(/Trợ lý AI Tiếp nhận/i)).toBeDefined();
    expect(screen.getByText(/Tóm tắt AI/i)).toBeDefined();
    expect(screen.getByText(/Đề xuất câu trả lời nhanh/i)).toBeDefined();
  });

  it("supports transferring case to another department with reason", () => {
    const handleTransfer = vi.fn();
    render(
      <StaffTicketQueue
        items={mockItems}
        currentStaffId="staff-huce-01"
        onTransferTicket={handleTransfer}
      />
    );

    const detailBtn = screen.getByRole("button", { name: /Chi tiết TCK-2026-0101/i });
    fireEvent.click(detailBtn);

    // Transfer action
    const transferBtn = screen.getByRole("button", { name: /Chuyển đơn vị chuyên môn/i });
    fireEvent.click(transferBtn);

    const deptSelect = screen.getByLabelText(/Đơn vị tiếp nhận mới/i);
    fireEvent.change(deptSelect, { target: { value: "phong_ctsv" } });

    const confirmTransferBtn = screen.getByRole("button", { name: /Xác nhận chuyển đơn/i });
    fireEvent.click(confirmTransferBtn);

    expect(handleTransfer).toHaveBeenCalledWith(
      "queue-001",
      expect.objectContaining({
        targetDepartment: "phong_ctsv",
      })
    );
  });

  it("opens AI Draft Response dialog and generates customized intake draft response", () => {
    render(<StaffTicketQueue items={mockItems} currentStaffId="staff-huce-01" />);

    const detailBtn = screen.getByRole("button", { name: /Chi tiết TCK-2026-0101/i });
    fireEvent.click(detailBtn);

    const draftBtn = screen.getByRole("button", { name: /AI Dự thảo phản hồi cho SV/i });
    fireEvent.click(draftBtn);

    // AI Draft Modal should be rendered
    expect(screen.getByRole("heading", { name: /Trợ lý AI Soạn Thảo Phản Hồi Cho Sinh Viên/i })).toBeDefined();
    expect(screen.getByDisplayValue(/Kính gửi sinh viên Trần Văn B/i)).toBeDefined();

    // Switch template to supplement request
    const supplementTab = screen.getByRole("button", { name: /Yêu cầu bổ sung hồ sơ/i });
    fireEvent.click(supplementTab);
    expect(screen.getByDisplayValue(/còn thiếu minh chứng/i)).toBeDefined();

    // Close dialog
    const closeBtn = screen.getByRole("button", { name: /Đóng hộp thoại/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByRole("heading", { name: /Trợ lý AI Soạn Thảo Phản Hồi Cho Sinh Viên/i })).toBeNull();
  });

  it("opens official intake receipt dialog conforming to Mau 01/MC", () => {
    render(<StaffTicketQueue items={mockItems} currentStaffId="staff-huce-01" />);

    const detailBtn = screen.getByRole("button", { name: /Chi tiết TCK-2026-0101/i });
    fireEvent.click(detailBtn);

    const receiptBtn = screen.getByRole("button", { name: /In Phiếu Tiếp Nhận \(Mẫu 01\/MC\)/i });
    fireEvent.click(receiptBtn);

    // Official Receipt Modal should be open
    expect(screen.getByRole("heading", { name: /GIẤY TIẾP NHẬN HỒ SƠ VÀ HẸN TRẢ KẾT QUẢ/i })).toBeDefined();
    expect(screen.getByText(/Mẫu số 01\/MC/i)).toBeDefined();
    expect(screen.getByText(/Mã số biên nhận: TCK-2026-0101/i)).toBeDefined();
    expect(screen.getByText(/TRƯỜNG ĐẠI HỌC XÂY DỰNG HÀ NỘI/i)).toBeDefined();

    // Close button
    const closeReceiptBtn = screen.getByRole("button", { name: /Đóng/i });
    fireEvent.click(closeReceiptBtn);
    expect(screen.queryByRole("heading", { name: /GIẤY TIẾP NHẬN HỒ SƠ VÀ HẸN TRẢ KẾT QUẢ/i })).toBeNull();
  });

  it("displays student attached documents with OCR verification badge in expanded view", () => {
    const itemsWithDocs: StaffQueueItem[] = [
      {
        ...mockItems[0],
        attachments: [
          { name: "don_xin_mien_giam_hoc_phi.pdf", ocrBadge: "Dấu đỏ hợp lệ", confidence: "98.5%", type: "pdf" },
          { name: "giay_xac_nhan_ho_ngheo.jpg", ocrBadge: "Chữ ký xác nhận", confidence: "97.2%", type: "image" },
        ],
      },
    ];

    render(<StaffTicketQueue items={itemsWithDocs} currentStaffId="staff-huce-01" />);

    const detailBtn = screen.getByRole("button", { name: /Chi tiết TCK-2026-0101/i });
    fireEvent.click(detailBtn);

    // Attachment list heading & items
    expect(screen.getByText(/Minh chứng & Hồ sơ sinh viên đính kèm/i)).toBeDefined();
    expect(screen.getByText("don_xin_mien_giam_hoc_phi.pdf")).toBeDefined();
    expect(screen.getByText(/Dấu đỏ hợp lệ \(98.5%\)/i)).toBeDefined();
    expect(screen.getByText("giay_xac_nhan_ho_ngheo.jpg")).toBeDefined();
  });

  it("provides 1-click preset actions for fast disposition", () => {
    render(<StaffTicketQueue items={mockItems} currentStaffId="staff-huce-01" />);

    const detailBtn = screen.getByRole("button", { name: /Chi tiết TCK-2026-0101/i });
    fireEvent.click(detailBtn);

    // Preset action buttons
    expect(screen.getByText(/Thao tác chuẩn 1-chạm/i)).toBeDefined();
    const presetFullPassBtn = screen.getByRole("button", { name: /Duyệt chuẩn 6\/6 cổng/i });
    expect(presetFullPassBtn).toBeDefined();

    // Clicking full pass automatically completes all 6 gates
    fireEvent.click(presetFullPassBtn);
    expect(screen.getByText(/Đã đạt 100% tiêu chí hợp lệ/i)).toBeDefined();
  });
});

