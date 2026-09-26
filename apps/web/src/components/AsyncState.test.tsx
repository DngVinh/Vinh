import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AsyncState } from "./AsyncState";

describe("AsyncState Component (TASK-WEB-STATE-001)", () => {
  it("renders loading state with polite aria-live region", () => {
    render(<AsyncState status="loading" loadingMessage="Đang tải dữ liệu..." />);
    const liveRegion = screen.getByText("Đang tải dữ liệu...");
    expect(liveRegion).toBeDefined();
    expect(liveRegion.closest("[aria-live='polite']")).not.toBeNull();
  });

  it("renders empty state with appropriate message", () => {
    render(<AsyncState status="empty" emptyMessage="Không có dữ liệu hiển thị" />);
    expect(screen.getByText("Không có dữ liệu hiển thị")).toBeDefined();
  });

  it("renders error state with retry button and triggers callback", () => {
    const handleRetry = vi.fn();
    render(
      <AsyncState
        status="error"
        errorMessage="Không thể kết nối máy chủ"
        onRetry={handleRetry}
      />
    );

    expect(screen.getByRole("alert")).toBeDefined();
    expect(screen.getByText("Không thể kết nối máy chủ")).toBeDefined();

    const retryBtn = screen.getByRole("button", { name: /Thử lại/i });
    expect(retryBtn).toBeDefined();
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it("renders offline state with network warning", () => {
    render(<AsyncState status="offline" />);
    expect(screen.getByText(/Mất kết nối mạng/i)).toBeDefined();
  });

  it("renders children when status is success", () => {
    render(
      <AsyncState status="success">
        <div>Nội dung thành công</div>
      </AsyncState>
    );
    expect(screen.getByText("Nội dung thành công")).toBeDefined();
  });

  it("negative path: renders fallback error when error status has no message", () => {
    render(<AsyncState status="error" />);
    expect(screen.getByText(/Đã xảy ra lỗi/i)).toBeDefined();
  });
});
