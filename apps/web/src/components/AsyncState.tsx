import React, { type ReactNode } from "react";
import { InboxIcon, WifiOffIcon, AlertTriangleIcon } from "./Icons";

export type AsyncStatus = "loading" | "empty" | "error" | "offline" | "success";

export interface AsyncStateProps {
  status: AsyncStatus;
  loadingMessage?: string;
  emptyMessage?: string;
  errorMessage?: string;
  onRetry?: () => void;
  children?: ReactNode;
}

export function AsyncState({
  status,
  loadingMessage = "Đang tải dữ liệu...",
  emptyMessage = "Không có dữ liệu",
  errorMessage = "Đã xảy ra lỗi khi tải dữ liệu",
  onRetry,
  children,
}: AsyncStateProps) {
  if (status === "success") {
    return <>{children}</>;
  }

  if (status === "loading") {
    return (
      <div
        aria-live="polite"
        style={{
          padding: "48px 24px",
          textAlign: "center",
          backgroundColor: "#ffffff",
          borderRadius: "var(--radius-lg, 14px)",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.04))",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "12px",
        }}
      >
        <div
          style={{
            width: "28px",
            height: "28px",
            border: "3px solid var(--color-slate-200, #e2e8f0)",
            borderTopColor: "var(--color-primary, #1e3a8a)",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
          }}
        />
        <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)", fontWeight: 500 }}>
          {loadingMessage}
        </p>
      </div>
    );
  }

  if (status === "empty") {
    return (
      <div
        aria-live="polite"
        style={{
          padding: "48px 24px",
          textAlign: "center",
          backgroundColor: "#ffffff",
          borderRadius: "var(--radius-lg, 14px)",
          border: "1px dashed var(--color-slate-300, #cbd5e1)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <div style={{ color: "var(--color-slate-400, #94a3b8)" }}>
          <InboxIcon size={36} />
        </div>
        <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)", fontWeight: 600 }}>
          {emptyMessage}
        </p>
      </div>
    );
  }

  if (status === "offline") {
    return (
      <div
        role="alert"
        aria-live="assertive"
        style={{
          padding: "24px 28px",
          borderRadius: "var(--radius-lg, 14px)",
          backgroundColor: "#fffbeb",
          border: "1px solid #fde68a",
          color: "#92400e",
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
          boxShadow: "var(--shadow-xs)",
        }}
      >
        <div style={{ color: "#d97706" }}>
          <WifiOffIcon size={32} />
        </div>
        <p style={{ fontWeight: 700, margin: 0, fontSize: "16px", color: "#b45309" }}>Mất kết nối mạng</p>
        <p style={{ margin: 0, fontSize: "13px", color: "#92400e" }}>
          Vui lòng kiểm tra lại đường truyền internet của bạn.
        </p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            style={{
              marginTop: "8px",
              padding: "8px 20px",
              borderRadius: "var(--radius-sm, 6px)",
              border: "1px solid #f59e0b",
              backgroundColor: "#ffffff",
              color: "#92400e",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            Thử lại
          </button>
        )}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div
        role="alert"
        aria-live="assertive"
        style={{
          padding: "24px 28px",
          borderRadius: "var(--radius-lg, 14px)",
          backgroundColor: "#fef2f2",
          border: "1px solid #fecaca",
          color: "#991b1b",
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
          boxShadow: "var(--shadow-xs)",
        }}
      >
        <div style={{ color: "#dc2626" }}>
          <AlertTriangleIcon size={32} />
        </div>
        <p style={{ fontWeight: 700, margin: 0, fontSize: "15px" }}>{errorMessage}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            style={{
              marginTop: "8px",
              padding: "8px 20px",
              borderRadius: "var(--radius-sm, 6px)",
              border: "1px solid #ef4444",
              backgroundColor: "#ffffff",
              color: "#b91c1c",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            Thử lại
          </button>
        )}
      </div>
    );
  }

  return null;
}

