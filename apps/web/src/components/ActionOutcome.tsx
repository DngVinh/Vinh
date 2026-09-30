import React from "react";
import {
  CheckCircle2Icon,
  AlertTriangleIcon,
  ClockIcon,
  XIcon,
} from "./Icons";

export type ActionState =
  | "pending"
  | "confirmed"
  | "executing"
  | "succeeded"
  | "failed"
  | "result_unknown"
  | "reconciled";

export interface ActionOutcomeProps {
  state: ActionState;
  idempotencyKey: string;
  actionTitle: string;
  actionDetails?: string;
  correlationId?: string;
  errorMessage?: string;
  onRetry?: () => void;
  onReconcile?: (idempotencyKey: string) => Promise<void> | void;
  onDismiss?: () => void;
}

export function ActionOutcome({
  state,
  idempotencyKey,
  actionTitle,
  actionDetails,
  correlationId,
  errorMessage,
  onRetry,
  onReconcile,
  onDismiss,
}: ActionOutcomeProps) {
  const isUnresolved = state === "executing" || state === "result_unknown";

  if (state === "result_unknown") {
    return (
      <div
        role="alert"
        style={{
          padding: "20px 24px",
          borderRadius: "12px",
          backgroundColor: "#fffbeb",
          border: "2px solid #f59e0b",
          color: "#78350f",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <AlertTriangleIcon size={22} />
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#92400e" }}>
            Kết quả chưa xác định: {actionTitle}
          </h3>
        </div>

        <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.6, color: "#78350f" }}>
          Yêu cầu đã được gửi tới máy chủ nhưng chưa nhận được phản hồi xác nhận chắc chắn do gián đoạn kết nối.
          Hệ thống đang bảo vệ giao dịch, vui lòng không gửi lại để tránh thao tác trùng lặp.
        </p>

        <div style={{ fontSize: "12px", color: "#92400e", display: "flex", flexWrap: "wrap", gap: "16px", backgroundColor: "#fef3c7", padding: "8px 12px", borderRadius: "6px" }}>
          <div>Mã giao dịch (Idempotency): <code>{idempotencyKey}</code></div>
          {correlationId && (
            <div>Mã tham chiếu (Correlation ID): <code>{correlationId}</code></div>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "4px" }}>
          {onReconcile && (
            <button
              type="button"
              onClick={() => onReconcile(idempotencyKey)}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                backgroundColor: "#d97706",
                color: "#ffffff",
                border: "none",
                fontWeight: 600,
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              Kiểm tra đối soát trạng thái
            </button>
          )}

          {onRetry && (
            <button
              type="button"
              disabled={isUnresolved}
              title="Thao tác bị khóa trong khi đang đối soát để bảo vệ giao dịch duy nhất"
              onClick={onRetry}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                backgroundColor: "#ffffff",
                color: "#9ca3af",
                border: "1px solid #d1d5db",
                fontWeight: 600,
                fontSize: "13px",
                cursor: "not-allowed",
              }}
            >
              Gửi lại yêu cầu
            </button>
          )}
        </div>
      </div>
    );
  }

  if (state === "succeeded" || state === "reconciled") {
    return (
      <div
        role="status"
        style={{
          padding: "18px 22px",
          borderRadius: "12px",
          backgroundColor: "#f0fdf4",
          border: "1px solid #86efac",
          color: "#166534",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <CheckCircle2Icon size={20} />
          <div>
            <div style={{ fontWeight: 700, fontSize: "15px" }}>
              {state === "reconciled" ? "Đã đối soát thành công" : "Thực hiện thành công"}: {actionTitle}
            </div>
            {actionDetails && (
              <div style={{ fontSize: "13px", marginTop: "2px", color: "#15803d" }}>
                {actionDetails}
              </div>
            )}
          </div>
        </div>

        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#166534", padding: "4px" }}
            aria-label="Đóng"
          >
            <XIcon size={16} />
          </button>
        )}
      </div>
    );
  }

  if (state === "failed") {
    return (
      <div
        role="alert"
        style={{
          padding: "18px 22px",
          borderRadius: "12px",
          backgroundColor: "#fef2f2",
          border: "1px solid #fecaca",
          color: "#991b1b",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: 700, fontSize: "15px" }}>
          <AlertTriangleIcon size={20} />
          <span>Thao tác thất bại: {actionTitle}</span>
        </div>
        {errorMessage && (
          <p style={{ margin: 0, fontSize: "13px", color: "#7f1d1d" }}>
            {errorMessage}
          </p>
        )}
        {onRetry && (
          <div style={{ marginTop: "6px" }}>
            <button
              type="button"
              onClick={onRetry}
              style={{
                padding: "6px 14px",
                borderRadius: "6px",
                backgroundColor: "#dc2626",
                color: "#ffffff",
                border: "none",
                fontWeight: 600,
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Thử lại
            </button>
          </div>
        )}
      </div>
    );
  }

  // Executing or Pending
  return (
    <div
      role="status"
      style={{
        padding: "18px 22px",
        borderRadius: "12px",
        backgroundColor: "#eff6ff",
        border: "1px solid #bfdbfe",
        color: "#1e40af",
        display: "flex",
        alignItems: "center",
        gap: "10px",
      }}
    >
      <ClockIcon size={20} />
      <div style={{ fontSize: "14px", fontWeight: 600 }}>
        Đang xử lý giao dịch: {actionTitle}...
      </div>
    </div>
  );
}
