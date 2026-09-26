import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { RoomBooking, type RoomSlot } from "./RoomBooking";

describe("RoomBooking Component (TASK-WEB-ROOM-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockRooms: RoomSlot[] = [
    {
      id: "room-h1-101",
      name: "Phòng H1-101",
      capacity: 60,
      timeSlot: "08:00 - 11:30",
      isAvailable: true,
    },
    {
      id: "room-h1-102",
      name: "Phòng H1-102",
      capacity: 120,
      timeSlot: "08:00 - 11:30",
      isAvailable: false,
      conflictReason: "Đã có lớp Cơ học đất học bù",
    },
  ];

  it("renders room slots and allows booking an available room", () => {
    const handleBook = vi.fn();
    render(<RoomBooking rooms={mockRooms} onBook={handleBook} />);

    expect(screen.getByText("Phòng H1-101 (60 chỗ)")).toBeDefined();
    expect(screen.getByText("Phòng H1-102 (120 chỗ)")).toBeDefined();

    // Conflict state visible
    expect(screen.getByText(/Đã có lớp Cơ học đất học bù/i)).toBeDefined();

    // Book available room
    const bookBtn = screen.getByRole("button", { name: /Đăng ký mượn H1-101/i });
    fireEvent.click(bookBtn);

    expect(handleBook).toHaveBeenCalledWith("room-h1-101");
  });

  it("negative path: disables booking for conflicted room slots", () => {
    render(<RoomBooking rooms={mockRooms} onBook={() => {}} />);

    const conflictedBtn = screen.getByRole("button", { name: /Đã có lịch - H1-102/i });
    expect(conflictedBtn.hasAttribute("disabled")).toBe(true);
  });

  it("filters rooms by capacity threshold", () => {
    render(<RoomBooking rooms={mockRooms} onBook={() => {}} />);

    const capacitySelect = screen.getByLabelText(/Sức chứa tối thiểu:/i);
    fireEvent.change(capacitySelect, { target: { value: "100" } });

    expect(screen.getByText("Phòng H1-102 (120 chỗ)")).toBeDefined();
    expect(screen.queryByText("Phòng H1-101 (60 chỗ)")).toBeNull();
  });
});
