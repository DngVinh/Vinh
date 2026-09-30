import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { TicketList, type StudentTicket } from "./TicketList";

describe("TicketList Enhanced Student Interaction", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  const mockTicketWaiting: StudentTicket = {
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
    ],
  };

  const mockTicketResolved: StudentTicket = {
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
        id: "evt-2",
        timestamp: "2026-09-22 10:00",
        description: "Điểm phúc khảo đã cập nhật trên Cổng thông tin đào tạo.",
        actor: "Phòng Khảo thí",
      },
    ],
  };

  it("allows student to supply additional info when status is waiting_student", () => {
    const handleSupplement = vi.fn();
    render(<TicketList tickets={[mockTicketWaiting]} onSupplementInfo={handleSupplement} />);

    // Open detail
    const detailBtn = screen.getByRole("button", { name: /Chi tiết/i });
    fireEvent.click(detailBtn);

    // Button to provide additional info should exist
    const supplementBtn = screen.getByRole("button", { name: /Bổ sung thông tin theo yêu cầu/i });
    fireEvent.click(supplementBtn);

    // Enter supplement text
    const supplementInput = screen.getByPlaceholderText(/Nhập nội dung phản hồi hoặc làm rõ thông tin/i);
    fireEvent.change(supplementInput, { target: { value: "Em đã tải lên ảnh chụp CCCD số 001202000000" } });

    // Submit supplement
    const submitBtn = screen.getByRole("button", { name: /Gửi bổ sung cho cán bộ/i });
    fireEvent.click(submitBtn);

    expect(handleSupplement).toHaveBeenCalledWith(
      "tck-001",
      expect.objectContaining({
        content: "Em đã tải lên ảnh chụp CCCD số 001202000000",
      })
    );
  });

  it("allows student to rate service quality when status is resolved", () => {
    const handleFeedback = vi.fn();
    render(<TicketList tickets={[mockTicketResolved]} onFeedbackRating={handleFeedback} />);

    // Open detail
    const detailBtn = screen.getByRole("button", { name: /Chi tiết/i });
    fireEvent.click(detailBtn);

    // Rating section should be rendered
    expect(screen.getByText(/Đánh giá mức độ hài lòng về kết quả xử lý/i)).toBeDefined();

    // Select 5 stars
    const star5 = screen.getByRole("button", { name: /5 sao/i });
    fireEvent.click(star5);

    // Fill comment
    const commentInput = screen.getByPlaceholderText(/Ý kiến đóng góp cải tiến chất lượng phục vụ/i);
    fireEvent.change(commentInput, { target: { value: "Cán bộ giải quyết rất nhanh và nhiệt tình." } });

    // Send rating
    const sendRatingBtn = screen.getByRole("button", { name: /Gửi đánh giá/i });
    fireEvent.click(sendRatingBtn);

    expect(handleFeedback).toHaveBeenCalledWith(
      "tck-002",
      expect.objectContaining({
        rating: 5,
        comment: "Cán bộ giải quyết rất nhanh và nhiệt tình.",
      })
    );
  });
});
