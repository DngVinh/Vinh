import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { RoomBooking, type RoomSlot } from "./RoomBooking";

describe("RoomBooking Component (TASK-WEB-ROOM-002)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  const mockRooms: RoomSlot[] = [
    {
      id: "room-h1-101",
      name: "Phòng H1-101",
      capacity: 60,
      timeSlot: "08:00 - 11:30",
      isAvailable: true,
      accessibility: "Có lối đi xe lăn, tầng 1",
      equipment: "Máy chiếu, micro, điều hòa",
    },
    {
      id: "room-h1-102",
      name: "Phòng H1-102",
      capacity: 120,
      timeSlot: "08:00 - 11:30",
      isAvailable: false,
      conflictReason: "Đã có lớp Cơ học đất học bù",
      accessibility: "Thang máy tòa H1",
      equipment: "Âm thanh hội trường, 2 máy chiếu",
    },
  ];

  it("exposes capacity and accessibility facts in room cards", () => {
    render(<RoomBooking rooms={mockRooms} onBook={() => {}} />);

    expect(screen.getByText("Phòng H1-101 (60 chỗ)")).toBeDefined();
    expect(screen.getByText(/Có lối đi xe lăn, tầng 1/i)).toBeDefined();
    expect(screen.getByText(/Máy chiếu, micro, điều hòa/i)).toBeDefined();
  });

  it("shows conflict explanation and disables action for conflicted room slots", () => {
    render(<RoomBooking rooms={mockRooms} onBook={() => {}} />);

    expect(screen.getByText(/Đã có lớp Cơ học đất học bù/i)).toBeDefined();
    const conflictedBtn = screen.getByRole("button", { name: /Đã có lịch - H1-102/i });
    expect(conflictedBtn.hasAttribute("disabled")).toBe(true);
  });

  it("requires explicit confirmation: opens structured preview before calling onBook", () => {
    const handleBook = vi.fn();
    render(<RoomBooking rooms={mockRooms} onBook={handleBook} />);

    const bookBtn = screen.getByRole("button", { name: /Đăng ký mượn H1-101/i });
    fireEvent.click(bookBtn);

    // CRITICAL (AC-TASK-WEB-ROOM-002-02): onBook MUST NOT be called before confirmation
    expect(handleBook).not.toHaveBeenCalled();

    // Verify structured preview shows room, timezone, capacity, approval rule, cancellation rule
    expect(screen.getByText(/Xác nhận đăng ký mượn phòng/i)).toBeDefined();
    expect(screen.getByText(/Phòng H1-101/i)).toBeDefined();
    expect(screen.getByText(/08:00 - 11:30/i)).toBeDefined();
    expect(screen.getByText(/Giờ Việt Nam/i)).toBeDefined();
    expect(screen.getByText(/Quy định hủy/i)).toBeDefined();
    expect(screen.getByText(/Quy trình phê duyệt/i)).toBeDefined();

    // Confirm booking
    const confirmBtn = screen.getByRole("button", { name: /Xác nhận đặt phòng/i });
    fireEvent.click(confirmBtn);

    // Now onBook MUST have been called with room id
    expect(handleBook).toHaveBeenCalledTimes(1);
    expect(handleBook).toHaveBeenCalledWith("room-h1-101");
  });

  it("allows returning to discovery from preview without booking", () => {
    const handleBook = vi.fn();
    render(<RoomBooking rooms={mockRooms} onBook={handleBook} />);

    fireEvent.click(screen.getByRole("button", { name: /Đăng ký mượn H1-101/i }));
    expect(screen.getByText(/Xác nhận đăng ký mượn phòng/i)).toBeDefined();

    const backBtn = screen.getByRole("button", { name: /Quay lại/i });
    fireEvent.click(backBtn);

    // Back to room discovery list
    expect(screen.getByText("Phòng H1-101 (60 chỗ)")).toBeDefined();
    expect(handleBook).not.toHaveBeenCalled();
  });

  it("filters rooms by capacity threshold", () => {
    render(<RoomBooking rooms={mockRooms} onBook={() => {}} />);

    const capacitySelect = screen.getByLabelText(/Sức chứa tối thiểu:/i);
    fireEvent.change(capacitySelect, { target: { value: "100" } });

    expect(screen.getByText("Phòng H1-102 (120 chỗ)")).toBeDefined();
    expect(screen.queryByText("Phòng H1-101 (60 chỗ)")).toBeNull();
  });
});
