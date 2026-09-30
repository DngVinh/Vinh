import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup, act } from "@testing-library/react";
import SchedulePage from "./page";
import { ApiClient, ApiClientError } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => {
  const MockApiClient = vi.fn();
  MockApiClient.prototype.get = vi.fn();
  return {
    ApiClient: MockApiClient,
    ApiClientError: class ApiClientError extends Error {
      problem: any;
      constructor(problem: any) {
        super(problem.detail || problem.title || "API Error");
        this.name = "ApiClientError";
        this.problem = problem;
      }
    },
  };
});

describe("SchedulePage Component - Demo Fallback (TASK-WEB-SCHED-003)", () => {
  let mockGet: ReturnType<typeof vi.fn>;

  const mockRealSchedule = {
    items: [
      {
        id: "sched-real-01",
        course_code: "XD-ARCH-301",
        course_name: "Kiến trúc công trình ngầm",
        starts_at: "2026-09-28T08:00:00Z",
        ends_at: "2026-09-28T11:30:00Z",
        location_label: "H3-205",
        instructor_display_name: "TS. Nguyễn Minh Châu",
      },
    ],
  };

  beforeEach(() => {
    mockGet = vi.fn();
    (ApiClient.prototype.get as unknown as ReturnType<typeof vi.fn>) = mockGet;
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("subsequent refresh failure marks data as stale without wiping out verified cached schedule", async () => {
    mockGet.mockResolvedValue(mockRealSchedule);

    render(<SchedulePage />);

    // Real schedule renders
    const realCourses = await screen.findAllByText(/Kiến trúc công trình ngầm/i, {}, { timeout: 5000 });
    expect(realCourses.length).toBeGreaterThan(0);

    // Refresh fails
    mockGet.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/network-error",
        title: "Mất kết nối",
        status: 0,
        detail: "Không thể kết nối lại máy chủ lịch học.",
        code: "NETWORK_ERROR",
      })
    );

    const refreshBtn = screen.getByRole("button", { name: /Đồng bộ lại/i });
    await act(async () => {
      fireEvent.click(refreshBtn);
    });

    // Stale indicator is surfaced
    await waitFor(() => {
      expect(screen.getByText(/Dữ liệu cũ/i)).toBeDefined();
    }, { timeout: 5000 });

    // Verified cached data is preserved
    expect(screen.getAllByText(/Kiến trúc công trình ngầm/i).length).toBeGreaterThan(0);
  });
});
