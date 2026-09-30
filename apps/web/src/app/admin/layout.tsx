import React, { type ReactNode } from "react";
import { AppShell, type Role } from "../../components/AppShell";

export interface AdminLayoutProps {
  children?: ReactNode;
  userRole?: Role;
  capabilities?: string[];
  sessionStatus?: "authenticated" | "unauthenticated" | "expired";
}

export default function AdminLayout({
  children,
  userRole = "admin",
  capabilities = ["ADMIN_ACCESS"],
  sessionStatus = "authenticated",
}: AdminLayoutProps) {
  // AC-TASK-WEB-ADMIN-001-03: Session expiry check
  if (sessionStatus === "expired") {
    return (
      <AppShell userRole="admin" activeNav="admin">
        <div
          role="alert"
          style={{
            padding: "28px",
            backgroundColor: "#fff1f2",
            borderRadius: "12px",
            border: "1px solid #fecaca",
            color: "#991b1b",
            maxWidth: "700px",
            margin: "24px auto",
          }}
        >
          <h3 style={{ margin: "0 0 8px 0", fontSize: "18px", fontWeight: 700 }}>
            Phiên làm việc đã hết hạn
          </h3>
          <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.6 }}>
            Phiên làm việc quản trị đã hết hạn hoặc quyền hạn đã bị thay đổi trên máy chủ. Vui lòng làm mới phiên để tiếp tục truy cập.
          </p>
        </div>
      </AppShell>
    );
  }

  // AC-TASK-WEB-ADMIN-001-01 & AC-TASK-WEB-ADMIN-001-02: Deny-by-default capability boundary
  const hasAdminCapability = userRole === "admin" && capabilities.includes("ADMIN_ACCESS");

  if (!hasAdminCapability) {
    return (
      <AppShell userRole={userRole} activeNav="home">
        <div
          role="alert"
          style={{
            padding: "40px 24px",
            textAlign: "center",
            backgroundColor: "#ffffff",
            borderRadius: "14px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            maxWidth: "600px",
            margin: "40px auto",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          <h2 style={{ fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", marginBottom: "8px" }}>
            Không tìm thấy trang hoặc bạn không có thẩm quyền truy cập
          </h2>
          <p style={{ fontSize: "14px", color: "var(--color-slate-600, #475569)", margin: "0 0 24px 0", lineHeight: 1.6 }}>
            Tài nguyên bạn đang cố truy cập không tồn tại hoặc yêu cầu đặc quyền Quản trị viên hệ thống được cấp phép bởi máy chủ.
          </p>
          <a
            href="/"
            style={{
              display: "inline-block",
              padding: "10px 20px",
              backgroundColor: "var(--color-primary, #1e3a8a)",
              color: "#ffffff",
              borderRadius: "8px",
              textDecoration: "none",
              fontWeight: 600,
              fontSize: "14px",
            }}
          >
            Quay về trang chủ
          </a>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell userRole="admin" activeNav="admin">
      {children}
    </AppShell>
  );
}
