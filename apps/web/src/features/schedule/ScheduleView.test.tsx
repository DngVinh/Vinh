import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { ScheduleView, type ScheduleEntry } from "./ScheduleView";

describe("ScheduleView Component (TASK-WEB-SCHEDULE-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockEntries: ScheduleEntry[] = [
    {
      id: "sch-1",
      courseCode: "XD101",
      courseName: "Cơ học kết cấu 1",
      dayOfWeek: "Thứ 2",
      time: "07:00 - 09:30",
      room: "H1-201",
      lecturer: "TS. Nguyễn Văn A",
      type: "class",
    },
    {
      id: "sch-2",
      courseCode: "XD205",
      courseName: "Bê tông cốt thép 2",
      dayOfWeek: "Thứ 5",
      time: "13:30 - 16:00",
      room: "H2-105",
      lecturer: "PGS.TS. Trần Thị B",
      type: "exam",
    },
  ];

  it("renders schedule entries with semantic table and freshness indicator", () => {
    render(
      <ScheduleView
        entries={mockEntries}
        freshnessTimestamp="2026-09-22T08:00:00Z"
      />
    );

    expect(screen.getByRole("table")).toBeDefined();
    expect(screen.getByText("Cơ học kết cấu 1")).toBeDefined();
    expect(screen.getByText("H1-201")).toBeDefined();
    expect(screen.getByText("Bê tông cốt thép 2")).toBeDefined();
    expect(screen.getByText("H2-105")).toBeDefined();

    // Freshness state
    expect(screen.getByText(/Thời điểm đồng bộ/i)).toBeDefined();
    expect(screen.getByText(/2026/)).toBeDefined();
  });

  it("filters entries by class and exam types", async () => {
    const { fireEvent } = await import("@testing-library/react");
    render(<ScheduleView entries={mockEntries} />);

    // Click Exam filter
    const examFilterBtn = screen.getByRole("button", { name: /Lịch thi/i });
    fireEvent.click(examFilterBtn);

    expect(screen.getByText("Bê tông cốt thép 2")).toBeDefined();
    expect(screen.queryByText("Cơ học kết cấu 1")).toBeNull();
  });

  it("renders accessible empty state when no schedule entries exist", () => {
    render(<ScheduleView entries={[]} />);
    expect(screen.getByText(/Chưa có lịch học hoặc lịch thi nào/i)).toBeDefined();
  });
});
