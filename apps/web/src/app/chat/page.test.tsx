import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import ChatPage from "./page";
import * as fs from "fs";
import * as path from "path";

describe("ChatPage Authentication & Session Boundary (TASK-WEB-AUTH-002)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("AC-TASK-WEB-AUTH-002-01: does not embed demo token or bearer credential in source code", () => {
    const pageSourcePath = path.resolve(__dirname, "page.tsx");
    const sourceContent = fs.readFileSync(pageSourcePath, "utf-8");

    // Must NOT contain hardcoded DEFAULT_DEMO_TOKEN or base64 JWT payload
    expect(sourceContent).not.toContain("DEFAULT_DEMO_TOKEN");
    expect(sourceContent).not.toContain("eyJleHAi");
    expect(sourceContent).not.toContain("Bearer ");
  });

  it("AC-TASK-WEB-AUTH-002-02: fails closed with unauthorized state when session is missing or returns 401", async () => {
    // Mock fetch returning 401 Unauthorized for conversation initialization
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: async () => ({
        code: "AUTHENTICATION_REQUIRED",
        title: "Authentication Required",
        detail: "A valid Bearer token or signed session is required.",
      }),
    } as unknown as Response);

    render(<ChatPage />);

    // Attempt to send a message
    const input = screen.getByLabelText(/Đặt câu hỏi/i);
    const sendButton = screen.getByRole("button", { name: /Gửi/i });

    fireEvent.change(input, { target: { value: "Học bổng kỳ này điều kiện gì?" } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      // AsyncState unauthorized heading or text should appear
      expect(screen.getByText(/Yêu cầu đăng nhập|Phiên đăng nhập không hợp lệ|truy cập/i)).toBeDefined();
    });

    // Verify fetch used credentials: "include" and did not send hardcoded token
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/v1/conversations"),
      expect.objectContaining({
        credentials: "include",
      })
    );
  });

  it("AC-TASK-WEB-AUTH-002-03: handles session expiration on stream failure gracefully", async () => {
    // First conversation init succeeds
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ id: "conv-123" }),
      } as unknown as Response)
      // Stream call fails with 401
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      } as unknown as Response);

    render(<ChatPage />);

    const input = screen.getByLabelText(/Đặt câu hỏi/i);
    const sendButton = screen.getByRole("button", { name: /Gửi/i });

    fireEvent.change(input, { target: { value: "Xin chào" } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Yêu cầu đăng nhập|Phiên đăng nhập không hợp lệ|truy cập/i)).toBeDefined();
    });
  });
});
