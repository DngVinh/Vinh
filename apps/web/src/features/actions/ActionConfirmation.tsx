import React, { useState, useEffect } from "react";
import { AlertTriangleIcon, ClockIcon } from "../../components/Icons";

export interface ActionParameter {
  label: string;
  value: string;
}

export interface ActionPreviewData {
  actionId: string;
  actionType: string;
  title: string;
  targetEntity: string;
  parameters: ActionParameter[];
  expiresInSeconds: number;
}

export interface ActionConfirmationProps {
  isOpen: boolean;
  action: ActionPreviewData;
  onConfirm: (actionId: string) => void;
  onCancel: () => void;
}

export function ActionConfirmation({
  isOpen,
  action,
  onConfirm,
  onCancel,
}: ActionConfirmationProps) {
  const [secondsLeft, setSecondsLeft] = useState(action.expiresInSeconds);

  useEffect(() => {
    setSecondsLeft(action.expiresInSeconds);
  }, [action.expiresInSeconds]);

  useEffect(() => {
    if (!isOpen || secondsLeft <= 0) return;
    const timer = setInterval(() => {
      setSecondsLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [isOpen, secondsLeft]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const isExpired = secondsLeft <= 0;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(15, 23, 42, 0.5)",
        backdropFilter: "blur(3px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 2000,
        padding: "16px",
      }}
    >
      <div
        style={{
          backgroundColor: "#ffffff",
          borderRadius: "var(--radius-lg, 14px)",
          maxWidth: "540px",
          width: "100%",
          padding: "28px",
          boxShadow: "var(--shadow-modal, 0 20px 25px -5px rgba(0, 0, 0, 0.15))",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        {/* Header */}
        <div>
          <h2 id="confirm-dialog-title" style={{ margin: "0 0 6px 0", fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
            {action.title}
          </h2>
          <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-500, #64748b)" }}>
            Đối tượng tác động: <strong>{action.targetEntity}</strong>
          </p>
        </div>

        {/* Immutable Parameters Preview */}
        <div
          style={{
            backgroundColor: "var(--color-slate-50, #f8fafc)",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            borderRadius: "var(--radius-md, 8px)",
            padding: "16px",
          }}
        >
          <p style={{ margin: "0 0 10px 0", fontSize: "13px", fontWeight: 700, color: "var(--color-slate-800, #1e293b)" }}>
            Chi tiết tham số:
          </p>
          <dl style={{ margin: 0, display: "grid", gridTemplateColumns: "140px 1fr", rowGap: "8px", fontSize: "13px" }}>
            {action.parameters.map((param, idx) => (
              <React.Fragment key={idx}>
                <dt style={{ color: "var(--color-slate-500, #64748b)", fontWeight: 500 }}>{param.label}:</dt>
                <dd style={{ margin: 0, fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>{param.value}</dd>
              </React.Fragment>
            ))}
          </dl>
        </div>

        {/* Expiration Countdown Warning */}
        <div
          aria-live="polite"
          style={{
            padding: "10px 14px",
            borderRadius: "var(--radius-sm, 6px)",
            fontSize: "13px",
            backgroundColor: isExpired ? "#fef2f2" : "#fffbeb",
            color: isExpired ? "#b91c1c" : "#b45309",
            border: `1px solid ${isExpired ? "#fecaca" : "#fde68a"}`,
            fontWeight: 500,
          }}
        >
          {isExpired ? (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <AlertTriangleIcon size={16} />
              <span>Phiên xác nhận đã hết hạn. Vui lòng đóng và thao tác lại.</span>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <ClockIcon size={16} />
              <span>Thời gian xác nhận còn lại: {secondsLeft} giây</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "4px" }}>
          <button
            type="button"
            onClick={onCancel}
            style={{
              padding: "10px 18px",
              borderRadius: "var(--radius-sm, 6px)",
              border: "1px solid var(--color-slate-300, #cbd5e1)",
              backgroundColor: "#ffffff",
              color: "var(--color-slate-700, #334155)",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
              transition: "var(--transition-fast, 150ms ease)",
            }}
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            onClick={() => onConfirm(action.actionId)}
            disabled={isExpired}
            style={{
              padding: "10px 22px",
              borderRadius: "var(--radius-sm, 6px)",
              border: "none",
              backgroundColor: isExpired ? "var(--color-slate-300, #cbd5e1)" : "var(--color-primary, #1e3a8a)",
              color: isExpired ? "var(--color-slate-500, #64748b)" : "#ffffff",
              fontWeight: 600,
              fontSize: "13px",
              cursor: isExpired ? "not-allowed" : "pointer",
              boxShadow: isExpired ? "none" : "var(--shadow-sm)",
              transition: "var(--transition-fast, 150ms ease)",
            }}
          >
            Xác nhận thực hiện
          </button>
        </div>
      </div>
    </div>
  );
}

