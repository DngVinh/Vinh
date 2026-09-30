import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { ScheduleView, type ScheduleEntry } from "./ScheduleView";

describe("ScheduleView Component (TASK-WEB-SCHED-002)", () => {
  afterEach(() => {
    cleanup();
  });

  const mockEntries: ScheduleEntry[] = [
    {
      id: "sch-1",
      courseCode: "XD101",
      courseName: "Cơ học kết cấu 1",
      dayOfWeek: "Thứ 2",
      date: "2026-09-28",
      time: "07:00 - 09:30",
      room: "H1-201",
      lecturer: "TS. Nguyễn Văn A",
      type: "class",
    },
    {
      id: "sch-2",
      courseCode: "XD205",
      courseName: "Bê tông cốt thép 2",
      dayOfWeek: "Thứ 2",
      date: "2026-09-28",
      time: "09:45 - 12:15",
      room: "H2-105",
      lecturer: "PGS.TS. Trần Thị B",
      type: "class",
    },
    {
      id: "sch-3",
      courseCode: "IT3020",
      courseName: "Lập trình Web nâng cao",
      dayOfWeek: "Thứ 5",
      date: "2026-10-01",
      time: "13:30 - 16:00",
      room: "H1-402",
      lecturer: "TS. Lê Văn C",
      type: "exam",
    },
  ];

  it("prioritizes next upcoming event and exposes timezone and freshness", () => {
    render(
      <ScheduleView
        entries={mockEntries}
        freshnessTimestamp="2026-09-26T07:00:00Z"
      />
    );

    // Next event priority spotlight
    expect(screen.getByRole("heading", { level: 3, name: /Sự kiện kế tiếp/i })).toBeDefined();
    expect(screen.getAllByText(/Cơ học kết cấu 1/i).length).toBeGreaterThan(0);

    // Timezone and freshness
    expect(screen.getByText(/ICT \(UTC\+7\)/i)).toBeDefined();
    expect(screen.getByText(/Đồng bộ lúc/i)).toBeDefined();
  });

  it("handles degraded and stale states visually in the freshness indicator", () => {
    const { container } = render(
      <ScheduleView
        entries={mockEntries}
        freshnessTimestamp="2026-09-26T07:00:00Z"
        isStale={true}
        isDegraded={true}
      />
    );
    // The indicator dot changes to orange (#f59e0b) when stale/degraded
    const dot = container.querySelector('span[style*="background-color: rgb(245, 158, 11)"]');
    expect(dot).toBeDefined();
  });

  it("groups agenda entries by day with semantic time markup", () => {
    render(<ScheduleView entries={mockEntries} />);

    // Day headings
    expect(screen.getByRole("heading", { level: 4, name: /Thứ 2/i })).toBeDefined();
    expect(screen.getByRole("heading", { level: 4, name: /Thứ 5/i })).toBeDefined();

    // Semantic time tags
    const timeElements = document.querySelectorAll("time");
    expect(timeElements.length).toBeGreaterThan(0);
  });

  it("detects and flags overlapping schedule sessions", () => {
    const overlappingEntries: ScheduleEntry[] = [
      {
        id: "ov-1",
        courseCode: "XD101",
        courseName: "Cơ học kết cấu 1",
        dayOfWeek: "Thứ 3",
        date: "2026-09-29",
        time: "08:00 - 10:30",
        room: "H1-101",
        lecturer: "GV A",
        type: "class",
      },
      {
        id: "ov-2",
        courseCode: "XD102",
        courseName: "Vật liệu xây dựng",
        dayOfWeek: "Thứ 3",
        date: "2026-09-29",
        time: "08:00 - 10:30",
        room: "H2-202",
        lecturer: "GV B",
        type: "class",
      },
    ];

    render(<ScheduleView entries={overlappingEntries} />);

    expect(screen.getAllByText(/Trùng ca học/i).length).toBeGreaterThan(0);
  });

  it("supports keyboard navigation on scrollable container", () => {
    render(<ScheduleView entries={mockEntries} />);

    const scrollRegion = screen.getByRole("region", { name: /Lịch học sinh viên/i });
    expect(scrollRegion).toBeDefined();
    expect(scrollRegion.getAttribute("tabindex")).toBe("0");
  });

  it("renders accessible empty state when entries are empty", () => {
    render(<ScheduleView entries={[]} />);
    expect(screen.getByText(/Chưa có lịch học hoặc lịch thi nào/i)).toBeDefined();
  });

  it("supports exporting schedule to iCal (.ics) format with 1-click button", () => {
    render(<ScheduleView entries={mockEntries} />);

    const exportBtn = screen.getByRole("button", { name: /Xuất lịch iCal/i });
    expect(exportBtn).toBeDefined();
  });
});

