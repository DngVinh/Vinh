import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import StaffPage from "./page";
import { ApiClient } from "../../lib/api/client";

vi.mock("../../lib/api/client", () => {
  const MockApiClient = vi.fn();
  MockApiClient.prototype.get = vi.fn();
  class MockApiClientError extends Error {
    problem: any;
    constructor(message: string, problem: any) {
      super(message);
      this.problem = problem;
    }
  }
  return {
    ApiClient: MockApiClient,
    ApiClientError: MockApiClientError,
  };
});

describe("StaffPage Component - Enhanced Intake & Checklist", () => {
  let mockGet: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockGet = vi.fn();
    (ApiClient.prototype.get as unknown as ReturnType<typeof vi.fn>) = mockGet;
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("fails honestly when API throws error and never fabricates demo tickets", async () => {
    mockGet.mockRejectedValueOnce(new Error("Network Error"));

    render(<StaffPage />);

    await waitFor(() => {
      expect(screen.getByText(/Không thể tải danh sách hàng đợi/i)).toBeDefined();
    });

    // Ensure demo tickets are NOT rendered
    const demoId = screen.queryByText("HO-019234");
    expect(demoId).toBeNull();
  });

  it("renders empty state when API returns empty", async () => {
    mockGet.mockResolvedValueOnce({ items: [] });

    render(<StaffPage />);

    await waitFor(() => {
      expect(screen.getByText(/Không có yêu cầu hỗ trợ/i)).toBeDefined();
    });

    // Ensure demo tickets are NOT rendered
    const demoId = screen.queryByText("HO-019234");
    expect(demoId).toBeNull();
  });
});
