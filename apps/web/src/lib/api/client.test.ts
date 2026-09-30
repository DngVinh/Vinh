import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiClient, ApiClientError, type ProblemDetails } from "./client";

describe("Typed API Client & Problem Mapping (TASK-WEB-API-001)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("handles successful JSON response", async () => {
    const mockData = { id: "ticket-123", status: "open" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => mockData,
    });

    const client = new ApiClient({ baseUrl: "https://api.example.com" });
    const result = await client.get<{ id: string; status: string }>("/v1/tickets/ticket-123");

    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      "https://api.example.com/v1/tickets/ticket-123",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("safely maps RFC 9457 Problem Details error response", async () => {
    const problem: ProblemDetails = {
      type: "https://campus247.example/problems/validation-failed",
      title: "Dữ liệu không hợp lệ",
      status: 422,
      detail: "Một hoặc nhiều trường cần được sửa.",
      code: "VALIDATION_FAILED",
      request_id: "req-abc-123",
      retryable: false,
      errors: [{ code: "REQUIRED", pointer: "/subject", detail: "Bắt buộc nhập tiêu đề" }],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      headers: new Headers({
        "content-type": "application/problem+json",
        "x-request-id": "req-abc-123",
      }),
      json: async () => problem,
    });

    const client = new ApiClient();

    await expect(client.post("/v1/tickets", {})).rejects.toThrowError(ApiClientError);

    try {
      await client.post("/v1/tickets", {});
    } catch (err) {
      const apiErr = err as ApiClientError;
      expect(apiErr.problem.code).toBe("VALIDATION_FAILED");
      expect(apiErr.problem.status).toBe(422);
      expect(apiErr.problem.request_id).toBe("req-abc-123");
      expect(apiErr.problem.errors?.length).toBe(1);
    }
  });

  it("negative path: handles unexpected network failure safely without exposing internal stack traces", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Network connection dropped"));

    const client = new ApiClient();
    try {
      await client.get("/v1/schedule/me");
      expect.unreachable();
    } catch (err) {
      const apiErr = err as ApiClientError;
      expect(apiErr).toBeInstanceOf(ApiClientError);
      expect(apiErr.problem.code).toBe("NETWORK_ERROR");
      expect(apiErr.problem.status).toBe(0);
      expect(apiErr.problem.retryable).toBe(true);
    }
  });
});
