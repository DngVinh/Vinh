import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { CapabilityBanner, type SystemOperationalStatus } from "./CapabilityBanner";

describe("CapabilityBanner Component (TASK-WEB-OPS-001)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders degradation warning banner with affected capabilities", () => {
    const status: SystemOperationalStatus = {
      mode: "degraded",
      message: "Hệ thống đang hoạt động ở chế độ suy giảm năng lực. Dịch vụ AI đang dùng mô hình dự phòng.",
      affectedServices: ["LLM Streaming", "Vector Search"],
    };

    render(<CapabilityBanner status={status} />);

    expect(screen.getByRole("alert")).toBeDefined();
    expect(screen.getByText(/suy giảm năng lực/i)).toBeDefined();
    expect(screen.getByText(/LLM Streaming/i)).toBeDefined();
    expect(screen.getByText(/Vector Search/i)).toBeDefined();
  });

  it("does not render alert banner when system is fully operational", () => {
    const status: SystemOperationalStatus = {
      mode: "healthy",
      message: "Tất cả các dịch vụ đang hoạt động bình thường.",
      affectedServices: [],
    };

    render(<CapabilityBanner status={status} />);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
