"use client";

import React, { type ReactNode } from "react";

export type Role = "student" | "staff" | "admin" | "guest";

export interface AppShellProps {
  children?: ReactNode;
  activeNav?: string;
  userRole?: Role;
}

interface NavItem {
  key: string;
  label: string;
  href: string;
  roles: Role[];
}

const NAV_ITEMS: NavItem[] = [
  { key: "home", label: "Trang chủ", href: "/", roles: ["student", "guest"] },
  { key: "chat", label: "Hỏi đáp AI", href: "/chat", roles: ["student"] },
  { key: "schedule", label: "Thời khóa biểu", href: "/schedule", roles: ["student"] },
  { key: "tickets", label: "Thủ tục & Yêu cầu", href: "/tickets", roles: ["student", "staff", "admin"] },
  { key: "rooms", label: "Mượn phòng", href: "/rooms", roles: ["student", "staff", "admin"] },
  { key: "staff", label: "Cán bộ", href: "/staff", roles: ["staff", "admin"] },
  { key: "knowledge", label: "Tri thức", href: "/knowledge", roles: ["admin", "staff"] },
  { key: "admin", label: "Quản trị", href: "/admin", roles: ["admin"] },
  { key: "privacy", label: "Quyền riêng tư", href: "/privacy", roles: ["student", "staff", "admin", "guest"] },
];

export function AppShell({ children, activeNav, userRole = "student" }: AppShellProps) {
  const currentKey = activeNav || "home";
  const visibleNavItems = NAV_ITEMS.filter((item) => item.roles.includes(userRole));

  React.useEffect(() => {
    if (typeof window !== "undefined" && process.env.NODE_ENV !== "test") {
      fetch("http://localhost:8000/v1/auth/demo-session", { credentials: "include" })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data?.token && typeof window.localStorage !== "undefined") {
            window.localStorage.setItem("campus247_token", data.token);
          }
        })
        .catch(() => {});
    }
  }, []);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "var(--color-slate-50, #f8fafc)" }}>
      {/* Skip Link for Keyboard Navigation (UX-A11Y-001) */}
      <a href="#main-content" className="skip-link">
        Bỏ qua tới nội dung chính
      </a>

      {/* Persistent Disclaimer Header (REQ-F-GOV-001) */}
      <header
        role="banner"
        style={{
          background: "linear-gradient(90deg, #b91c1c 0%, #dc2626 100%)",
          color: "#ffffff",
          padding: "6px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "13px",
          fontWeight: 500,
          boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ display: "inline-block", width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#fef08a" }} />
          <span>Campus 24/7 — HUCE Demo (Mô phỏng không chính thức)</span>
        </div>
        <span
          style={{
            backgroundColor: "rgba(255, 255, 255, 0.95)",
            color: "var(--color-banner-demo, #dc2626)",
            padding: "2px 8px",
            borderRadius: "9999px",
            fontSize: "11px",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            fontWeight: 700,
          }}
        >
          Dữ liệu mô phỏng
        </span>
      </header>

      {/* Main Navigation Bar */}
      <nav
        role="navigation"
        aria-label="Điều hướng chính"
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          backgroundColor: "#ffffff",
          borderBottom: "1px solid var(--color-slate-200, #e2e8f0)",
          boxShadow: "var(--shadow-xs, 0 1px 2px 0 rgba(0,0,0,0.05))",
          padding: "0 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "60px",
        }}
      >
        {/* Brand Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0, marginRight: "16px" }}>
          <a
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                backgroundColor: "var(--color-primary, #1e3a8a)",
                color: "#ffffff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 800,
                fontSize: "15px",
              }}
            >
              C
            </div>
            <div>
              <span style={{ fontSize: "16px", fontWeight: 700, color: "var(--color-primary, #1e3a8a)", letterSpacing: "-0.3px" }}>
                Campus 24/7
              </span>
              <span
                style={{
                  marginLeft: "6px",
                  fontSize: "11px",
                  fontWeight: 600,
                  color: "var(--color-slate-500, #64748b)",
                  backgroundColor: "var(--color-slate-100, #f1f5f9)",
                  padding: "1px 6px",
                  borderRadius: "4px",
                }}
              >
                HUCE
              </span>
            </div>
          </a>
        </div>

        {/* Navigation Links with Horizontal Scroll Support */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            overflowX: "auto",
            scrollbarWidth: "none",
            msOverflowStyle: "none",
            padding: "4px 0",
          }}
        >
          {visibleNavItems.map((item) => {
            const isActive = currentKey === item.key;
            return (
              <a
                key={item.key}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                style={{
                  padding: "8px 12px",
                  borderRadius: "var(--radius-md, 8px)",
                  fontSize: "13px",
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-600, #475569)",
                  backgroundColor: isActive ? "var(--color-primary-light, #eff6ff)" : "transparent",
                  textDecoration: "none",
                  whiteSpace: "nowrap",
                  transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                }}
              >
                {item.label}
              </a>
            );
          })}
        </div>

        {/* User Identity Pill Badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0, marginLeft: "12px" }}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "9999px",
              backgroundColor: "#f1f5f9",
              color: "#334155",
              fontSize: "12px",
              fontWeight: 600,
            }}
          >
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#10b981" }} />
            SV240000 (Demo)
          </span>
        </div>
      </nav>

      {/* Main Content Area */}
      <main
        id="main-content"
        role="main"
        style={{
          flex: 1,
          padding: "24px 20px 48px 20px",
          maxWidth: "1200px",
          width: "100%",
          margin: "0 auto",
          boxSizing: "border-box",
        }}
      >
        {children}
      </main>

      {/* Footer */}
      <footer
        role="contentinfo"
        style={{
          borderTop: "1px solid var(--color-slate-200, #e2e8f0)",
          padding: "24px 20px",
          backgroundColor: "#ffffff",
          textAlign: "center",
          fontSize: "13px",
          color: "var(--color-slate-500, #64748b)",
          marginTop: "auto",
        }}
      >
        <div style={{ maxWidth: "1200px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "8px", alignItems: "center" }}>
          <p style={{ margin: 0, fontWeight: 500 }}>
            Campus 24/7 HUCE Demo — Hệ thống thử nghiệm nội bộ, không thay thế quy trình hành chính chính thức.
          </p>
          <p style={{ margin: 0, fontSize: "12px", color: "var(--color-slate-400, #94a3b8)" }}>
            Đại học Xây dựng Hà Nội • Tuân thủ chuẩn tiếp cận WCAG 2.2 AA & Nghị định 13/2023/NĐ-CP
          </p>
        </div>
      </footer>
    </div>
  );
}

