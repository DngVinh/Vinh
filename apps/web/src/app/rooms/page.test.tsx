import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import RoomsPage from "./page";
import { ApiClient, ApiClientError } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => {
  const MockApiClient = vi.fn();
  MockApiClient.prototype.get = vi.fn();
  MockApiClient.prototype.post = vi.fn();
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

describe("RoomsPage Component - Fail Honestly (TASK-WEB-ROOM-003)", () => {
  let mockGet: ReturnType<typeof vi.fn>;
  let mockPost: ReturnType<typeof vi.fn>;

  const mockRoomItems = [
    {
      id: "room-real-101",
      room_code: "H1-101",
      display_name: "Giảng đường H1-101",
      capacity: 80,
      features: ["Máy chiếu", "Điều hòa"],
      status: "AVAILABLE",
    },
  ];

  beforeEach(() => {
    mockGet = vi.fn();
    mockPost = vi.fn();
    (ApiClient.prototype.get as unknown as ReturnType<typeof vi.fn>) = mockGet;
    (ApiClient.prototype.post as unknown as ReturnType<typeof vi.fn>) = mockPost;
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("fetch failure renders error state and NEVER fabricates demo rooms", async () => {
    mockGet.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/service-unavailable",
        title: "Dịch vụ phòng học gián đoạn",
        status: 503,
        detail: "Hệ thống quản lý phòng học đang bảo trì.",
        code: "SERVICE_UNAVAILABLE",
      })
    );

    render(<RoomsPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeDefined();
    });

    expect(screen.getByText(/Hệ thống quản lý phòng học đang bảo trì/i)).toBeDefined();

    // MUST NOT render fabricated demo rooms
    expect(screen.queryByText(/Giảng đường H1-301/i)).toBeNull();
    expect(screen.queryByText(/Phòng tự học H2-205/i)).toBeNull();
  });

  it("network timeout renders offline state", async () => {
    mockGet.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/timeout",
        title: "Timeout",
        status: 0,
        detail: "Mất kết nối mạng.",
        code: "TIMEOUT",
      })
    );

    render(<RoomsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Vui lòng kiểm tra lại đường truyền internet/i)).toBeDefined();
    });
  });

  it("booking failure never renders fabricated receipt or success notice", async () => {
    mockGet.mockResolvedValueOnce({ items: mockRoomItems });
    mockPost.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/conflict",
        title: "Xung đột lịch mượn",
        status: 409,
        detail: "Phòng học này vừa được một lớp học phần khác đăng ký.",
        code: "ROOM_CONFLICT",
      })
    );

    render(<RoomsPage />);

    // Wait for rooms to load
    const bookBtn = await screen.findByRole("button", { name: /Đăng ký mượn.*H1-101/i });
    fireEvent.click(bookBtn);

    // Confirm booking in preview
    const confirmBtn = screen.getByRole("button", { name: /Xác nhận đặt phòng/i });
    fireEvent.click(confirmBtn);

    // Verify failure is honestly reported and NO success receipt appears
    await waitFor(() => {
      expect(screen.getByText(/Phòng học này vừa được một lớp học phần khác đăng ký/i)).toBeDefined();
    });

    expect(screen.queryByText(/Yêu cầu mượn phòng đã được ghi nhận thành công/i)).toBeNull();
  });

  it("booking timeout represents outcome as result-unknown and guides user against duplicate submissions", async () => {
    mockGet.mockResolvedValueOnce({ items: mockRoomItems });
    mockPost.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/timeout",
        title: "Hết thời gian chờ",
        status: 504,
        detail: "Mất kết nối với máy chủ quản lý phòng học trong khi xác nhận.",
        code: "TIMEOUT",
      })
    );

    render(<RoomsPage />);

    const bookBtn = await screen.findByRole("button", { name: /Đăng ký mượn.*H1-101/i });
    fireEvent.click(bookBtn);

    const confirmBtn = screen.getByRole("button", { name: /Xác nhận đặt phòng/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getAllByText(/Kết quả chưa xác định/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/không gửi lại để tránh trùng lặp/i)).toBeDefined();
    });

    expect(screen.queryByText(/Yêu cầu mượn phòng đã được ghi nhận thành công/i)).toBeNull();
  });

  it("authoritative booking success renders real booking confirmation", async () => {
    mockGet.mockResolvedValueOnce({ items: mockRoomItems });
    mockPost.mockResolvedValueOnce({
      booking_id: "BOOK-HUCE-8888",
      room_id: "room-real-101",
      status: "CONFIRMED",
      time_slot: "08:00 - 11:30",
    });

    render(<RoomsPage />);

    const bookBtn = await screen.findByRole("button", { name: /Đăng ký mượn.*H1-101/i });
    fireEvent.click(bookBtn);

    const confirmBtn = screen.getByRole("button", { name: /Xác nhận đặt phòng/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/Mã đặt chỗ: BOOK-HUCE-8888/i)).toBeDefined();
    });
  });
});
