import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import TicketsPage from "./page";
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

describe("TicketsPage Component - Fail Honestly (TASK-WEB-TICK-003)", () => {
  let mockGet: ReturnType<typeof vi.fn>;
  let mockPost: ReturnType<typeof vi.fn>;

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

  it("fetch failure renders error state and NEVER fabricates demo tickets", async () => {
    mockGet.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/server-error",
        title: "Lỗi máy chủ",
        status: 500,
        detail: "Không thể kết nối cơ sở dữ liệu phiếu hỗ trợ.",
        code: "INTERNAL_ERROR",
      })
    );

    render(<TicketsPage />);

    // Wait for error state to resolve
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeDefined();
    });

    // Error message must be honest
    expect(screen.getByText(/Không thể kết nối cơ sở dữ liệu phiếu hỗ trợ/i)).toBeDefined();

    // MUST NOT render fabricated demo tickets
    expect(screen.queryByText(/Xin cấp lại thẻ sinh viên bị mất/i)).toBeNull();
    expect(screen.queryByText(/TK-2026-01/i)).toBeNull();
    expect(screen.queryByText(/TK-2026-02/i)).toBeNull();
  });

  it("creation failure never fabricates success receipt and retains form draft", async () => {
    mockGet.mockResolvedValueOnce({ items: [] });
    mockPost.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/validation-error",
        title: "Dữ liệu không hợp lệ",
        status: 422,
        detail: "Mục đích xin cấp không đáp ứng tiêu chuẩn tiếp nhận.",
        code: "VALIDATION_FAILED",
        retryable: false,
      })
    );

    render(<TicketsPage />);

    // Open creation modal
    const openBtn = await screen.findByRole("button", { name: /Tạo yêu cầu mới/i });
    fireEvent.click(openBtn);

    // Enter draft data
    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i);
    fireEvent.change(reasonInput, { target: { value: "Xin cấp bảng điểm nộp học bổng Panasonic" } });

    // Step to preview
    const previewBtn = screen.getByRole("button", { name: /Xem trước yêu cầu/i });
    fireEvent.click(previewBtn);

    // Submit
    const submitBtn = screen.getByRole("button", { name: /Gửi yêu cầu/i });
    fireEvent.click(submitBtn);

    // Verify error shown and NO fabricated success notice
    await waitFor(() => {
      expect(screen.getByText(/Mục đích xin cấp không đáp ứng tiêu chuẩn/i)).toBeDefined();
    });
    expect(screen.queryByText(/thành công! Mã yêu cầu/i)).toBeNull();

    // Form modal remains open and draft is retained
    expect(screen.getByText(/Xin cấp bảng điểm nộp học bổng Panasonic/i)).toBeDefined();
  });

  it("distinguishes failed-with-no-effect from result-unknown on network timeout", async () => {
    mockGet.mockResolvedValueOnce({ items: [] });
    // Simulate timeout / network error during post where backend state is unknown
    mockPost.mockRejectedValueOnce(
      new ApiClientError({
        type: "https://campus247.example/problems/timeout",
        title: "Hết thời gian chờ",
        status: 504,
        detail: "Mất kết nối trong quá trình xử lý.",
        code: "TIMEOUT",
        retryable: true,
      })
    );

    render(<TicketsPage />);

    const openBtn = await screen.findByRole("button", { name: /Tạo yêu cầu mới/i });
    fireEvent.click(openBtn);

    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i);
    fireEvent.change(reasonInput, { target: { value: "Bổ sung hồ sơ tuyển dụng" } });

    fireEvent.click(screen.getByRole("button", { name: /Xem trước yêu cầu/i }));
    fireEvent.click(screen.getByRole("button", { name: /Gửi yêu cầu/i }));

    // Must show result-unknown state with anti-duplicate guidance
    await waitFor(() => {
      expect(screen.getAllByText(/Kết quả chưa xác định/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/không gửi lại để tránh trùng lặp/i)).toBeDefined();
    });

    // Retry is disabled while result is unknown to prevent duplicate tickets
    const retrySubmitBtn = screen.getByRole("button", { name: /Gửi yêu cầu/i });
    expect(retrySubmitBtn.hasAttribute("disabled")).toBe(true);
  });

  it("authoritative success renders real ticket from server response", async () => {
    mockGet.mockResolvedValueOnce({ items: [] });
    mockPost.mockResolvedValueOnce({
      id: "ticket-real-999",
      category: "Thủ tục hành chính",
      status: "submitted",
      subject: "Xin cấp Giấy xác nhận sinh viên (1 bản)",
      description_redacted: "Làm thẻ căn cước",
      created_at: "2026-09-26T15:00:00Z",
      updated_at: "2026-09-26T15:00:00Z",
    });

    render(<TicketsPage />);

    const openBtn = await screen.findByRole("button", { name: /Tạo yêu cầu mới/i });
    fireEvent.click(openBtn);

    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i);
    fireEvent.change(reasonInput, { target: { value: "Làm thẻ căn cước" } });

    fireEvent.click(screen.getByRole("button", { name: /Xem trước yêu cầu/i }));
    fireEvent.click(screen.getByRole("button", { name: /Gửi yêu cầu/i }));

    await waitFor(() => {
      expect(screen.getByText(/Đã gửi yêu cầu thành công/i)).toBeDefined();
    });

    // Authoritative ticket is rendered in list
    expect(screen.getByText("TK-TICKET")).toBeDefined();
  });
});
