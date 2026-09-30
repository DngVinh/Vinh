import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import AdminLayout from "./layout";

describe("AdminLayout Component (TASK-WEB-ADMIN-001)", () => {
  afterEach(() => {
    cleanup();
  });

  const SensitiveChild = () => (
    <div data-testid="sensitive-admin-content">
      Dữ liệu mật cấu hình hệ thống và khóa bảo mật
    </div>
  );

  it("denies access and conceals sensitive child content when user lacks admin capability (AC-TASK-WEB-ADMIN-001-01, AC-TASK-WEB-ADMIN-001-02)", () => {
    render(
      <AdminLayout userRole="student" capabilities={[]}>
        <SensitiveChild />
      </AdminLayout>
    );

    // Denial / concealment view rendered
    expect(screen.getByText(/Không tìm thấy trang hoặc bạn không có thẩm quyền truy cập/i)).toBeDefined();
    // Sensitive child NEVER rendered
    expect(screen.queryByTestId("sensitive-admin-content")).toBeNull();
    expect(screen.queryByText(/Dữ liệu mật cấu hình/i)).toBeNull();
  });

  it("allows access and renders child content when user has admin capability (AC-TASK-WEB-ADMIN-001-02)", () => {
    render(
      <AdminLayout userRole="admin" capabilities={["ADMIN_ACCESS"]}>
        <SensitiveChild />
      </AdminLayout>
    );

    expect(screen.getByTestId("sensitive-admin-content")).toBeDefined();
    expect(screen.getByText(/Dữ liệu mật cấu hình hệ thống/i)).toBeDefined();
    expect(screen.queryByText(/Không tìm thấy trang hoặc bạn không có thẩm quyền/i)).toBeNull();
  });

  it("handles session expiry and forces recheck without trusting stale client state (AC-TASK-WEB-ADMIN-001-03)", () => {
    render(
      <AdminLayout
        userRole="admin"
        capabilities={["ADMIN_ACCESS"]}
        sessionStatus="expired"
      >
        <SensitiveChild />
      </AdminLayout>
    );

    expect(screen.getByText(/Phiên làm việc đã hết hạn/i)).toBeDefined();
    expect(screen.queryByTestId("sensitive-admin-content")).toBeNull();
  });
});
