"use client";

import React, { type ReactNode, useEffect, useRef } from "react";
import { InboxIcon, WifiOffIcon, AlertTriangleIcon } from "./Icons";

export type AsyncStatus = "loading" | "empty" | "zero-result" | "error" | "offline" | "stale" | "degraded" | "unauthorized" | "result-unknown" | "success";

export interface AsyncStateProps {
  status: AsyncStatus;
  loadingMessage?: string;
  emptyMessage?: string;
  errorMessage?: string;
  onRetry?: () => void;
  autoFocusRetry?: boolean;
  children?: ReactNode;
}

export function AsyncState({
  status,
  loadingMessage = "Đang tải dữ liệu...",
  emptyMessage = "Không có dữ liệu",
  errorMessage = "Đã xảy ra lỗi khi tải dữ liệu",
  onRetry,
  autoFocusRetry = true,
  children,
}: AsyncStateProps) {
  const retryBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (autoFocusRetry && (status === "error" || status === "offline" || status === "result-unknown") && onRetry) {
      retryBtnRef.current?.focus();
    }
  }, [status, autoFocusRetry, onRetry]);

  if (status === "success") {
    return <>{children}</>;
  }

  if (status === "loading") {
    return (
      <div
        role="status"
        aria-live="polite"
        style={{
          padding: "48px 24px",
          textAlign: "center",
          backgroundColor: "rgba(255, 255, 255, 0.7)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
          borderRadius: "var(--radius-lg, 14px)",
          border: "1px solid rgba(226, 232, 240, 0.5)",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px",
          transition: "all 0.3s ease-in-out",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", width: "100%", maxWidth: "320px", opacity: 0.6 }}>
          <div style={{ height: "28px", backgroundColor: "var(--color-slate-200, #e2e8f0)", borderRadius: "6px", width: "100%", animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite" }} />
          <div style={{ height: "20px", backgroundColor: "var(--color-slate-200, #e2e8f0)", borderRadius: "4px", width: "85%", margin: "0 auto", animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite", animationDelay: "0.2s" }} />
          <div style={{ height: "20px", backgroundColor: "var(--color-slate-200, #e2e8f0)", borderRadius: "4px", width: "60%", margin: "0 auto", animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite", animationDelay: "0.4s" }} />
        </div>
        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
          }
        `}</style>
        <p style={{ margin: 0, fontSize: "14px", color: "var(--color-primary, #1e3a8a)", fontWeight: 600 }}>
          {loadingMessage}
        </p>
      </div>
    );
  }

  if (status === "zero-result") {
    return (
      <div role="status" aria-live="polite" style={{ padding: "48px 24px", textAlign: "center", backgroundColor: "#ffffff", borderRadius: "14px", border: "1px dashed #cbd5e1" }}>
        <p style={{ margin: 0, fontSize: "14px", color: "#475569", fontWeight: 600 }}>
          Không tìm thấy kết quả
        </p>
      </div>
    );
  }

  if (status === "stale") {
    return (
      <>
        <div role="status" aria-live="polite" style={{ padding: "16px", backgroundColor: "#fffbeb", border: "1px solid #fde68a", color: "#b45309", borderRadius: "8px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>
            Dữ liệu có thể chưa được cập nhật. {onRetry && <button onClick={onRetry} style={{ background: "none", border: "none", color: "#92400e", textDecoration: "underline", cursor: "pointer", padding: 0 }}>Làm mới</button>}
          </p>
        </div>
        {children}
      </>
    );
  }

  if (status === "degraded") {
    return (
      <>
        <div role="status" aria-live="polite" style={{ padding: "16px", backgroundColor: "#fef3c7", border: "1px solid #fcd34d", color: "#b45309", borderRadius: "8px", marginBottom: "16px" }}>
          <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>
            Hệ thống đang phản hồi chậm. Một số tính năng có thể bị gián đoạn.
          </p>
        </div>
        {children}
      </>
    );
  }

  if (status === "unauthorized") {
    return (
      <div role="alert" aria-live="assertive" style={{ padding: "24px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", borderRadius: "14px", textAlign: "center" }}>
        <p style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Bạn không có quyền truy cập chức năng này</p>
      </div>
    );
  }

  if (status === "result-unknown") {
    return (
      <div role="alert" aria-live="assertive" style={{ padding: "24px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", borderRadius: "14px", textAlign: "center" }}>
        <p style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Trạng thái xử lý không rõ ràng</p>
        <p style={{ margin: "8px 0 0", fontSize: "13px" }}>Vui lòng kiểm tra lại sau hoặc liên hệ hỗ trợ.</p>
        {onRetry && (
          <button
            ref={retryBtnRef}
            type="button"
            onClick={onRetry}
            style={{ marginTop: "12px", padding: "8px 16px", background: "#ffffff", border: "1px solid #ef4444", borderRadius: "6px", cursor: "pointer", color: "#b91c1c" }}
          >
            Kiểm tra lại
          </button>
        )}
      </div>
    );
  }

  if (status === "empty") {
    return (
      <div
        role="status"
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
            ref={retryBtnRef}
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
            ref={retryBtnRef}
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
