"use client";

import React, { useState } from "react";
import { AlertTriangleIcon } from "../../components/Icons";

export type OperationalMode = "healthy" | "degraded" | "safe_mode" | "outage";

export interface OperationalMetric {
  name: string;
  value: number | string;
  unit: string;
  timeWindow: string;
  freshness: string;
  source: string;
  status: "normal" | "degraded" | "unavailable" | "stale";
}

export interface SystemOperationalStatus {
  mode: OperationalMode;
  message: string;
  affectedServices: string[];
  metrics?: OperationalMetric[];
  isDismissible?: boolean;
  impact?: string;
  safeNextAction?: string;
}

export interface CapabilityBannerProps {
  status: SystemOperationalStatus;
  onDismiss?: () => void;
}

export function CapabilityBanner({ status, onDismiss }: CapabilityBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  const hasAbnormalMetrics =
    status.metrics && status.metrics.some((m) => m.status !== "normal");

  if (dismissed || (status.mode === "healthy" && !hasAbnormalMetrics)) {
    return null;
  }

  const isCritical = status.mode === "outage" || status.mode === "safe_mode";

  const getModeLabel = (mode: OperationalMode) => {
    switch (mode) {
      case "outage":
        return "[✕] SỰ CỐ NGỪNG DỊCH VỤ";
      case "safe_mode":
        return "[S] CHẾ ĐỘ AN TOÀN";
      case "degraded":
        return "[!] SUY GIẢM";
      case "healthy":
      default:
        return "[✓] BÌNH THƯỜNG";
    }
  };

  const getMetricBadge = (mStatus: OperationalMetric["status"]) => {
    switch (mStatus) {
      case "unavailable":
        return {
          label: "[✕] Không khả dụng",
          bg: "#fee2e2",
          color: "#991b1b",
          border: "#fca5a5",
        };
      case "degraded":
        return {
          label: "[!] Suy giảm",
          bg: "#fef3c7",
          color: "#92400e",
          border: "#fde68a",
        };
      case "stale":
        return {
          label: "[~] Dữ liệu cũ",
          bg: "#f1f5f9",
          color: "#475569",
          border: "#cbd5e1",
        };
      case "normal":
      default:
        return {
          label: "[•] Bình thường",
          bg: "#ecfdf5",
          color: "#065f46",
          border: "#a7f3d0",
        };
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  return (
    <section
      role="region"
      aria-label="Cảnh báo vận hành và chỉ số KPI"
      aria-live={isCritical ? "assertive" : "polite"}
      style={{
        backgroundColor: isCritical ? "#fef2f2" : "#fffbeb",
        borderBottom: `1px solid ${isCritical ? "#fca5a5" : "#fde68a"}`,
        color: isCritical ? "#991b1b" : "#92400e",
        padding: "16px 24px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        fontSize: "13px",
      }}
    >
      {/* Header and dismiss control */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, flexWrap: "wrap" }}>
          <AlertTriangleIcon size={18} />
          <span>
            Cảnh báo vận hành hệ thống {getModeLabel(status.mode)}:
          </span>
          <span style={{ fontWeight: 500 }}>{status.message}</span>
        </div>

        {status.isDismissible && (
          <button
            type="button"
            onClick={handleDismiss}
            aria-label="Đóng thông báo"
            style={{
              background: "transparent",
              border: "1px solid currentColor",
              borderRadius: "4px",
              padding: "4px 8px",
              fontSize: "12px",
              color: "inherit",
              cursor: "pointer",
              fontWeight: 600,
              flexShrink: 0,
            }}
          >
            Đóng thông báo ✕
          </button>
        )}
      </div>

      {/* Affected services list */}
      {status.affectedServices.length > 0 && (
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontWeight: 600 }}>Dịch vụ bị ảnh hưởng:</span>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {status.affectedServices.map((svc) => (
              <span
                key={svc}
                style={{
                  backgroundColor: isCritical ? "#fee2e2" : "#fef3c7",
                  border: `1px solid ${isCritical ? "#fca5a5" : "#fde68a"}`,
                  color: isCritical ? "#7f1d1d" : "#78350f",
                  padding: "2px 8px",
                  borderRadius: "var(--radius-full, 9999px)",
                  fontWeight: 600,
                  fontSize: "12px",
                }}
              >
                {svc}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Impact and Safe Next Action details */}
      {(status.impact || status.safeNextAction) && (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            padding: "8px 12px",
            borderRadius: "6px",
            backgroundColor: isCritical ? "rgba(254, 226, 226, 0.6)" : "rgba(254, 243, 199, 0.6)",
            fontSize: "12px",
          }}
        >
          {status.impact && (
            <div>
              <strong style={{ color: isCritical ? "#7f1d1d" : "#78350f" }}>Ảnh hưởng thực tế: </strong>
              <span>{status.impact}</span>
            </div>
          )}
          {status.safeNextAction && (
            <div>
              <strong style={{ color: isCritical ? "#7f1d1d" : "#78350f" }}>Hành động an toàn khuyến nghị: </strong>
              <span>{status.safeNextAction}</span>
            </div>
          )}
        </div>
      )}

      {/* Operational Metrics & KPI Context */}
      {status.metrics && status.metrics.length > 0 && (
        <div
          style={{
            marginTop: "4px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "12px",
          }}
        >
          {status.metrics.map((metric, idx) => {
            const badge = getMetricBadge(metric.status);
            return (
              <div
                key={idx}
                style={{
                  backgroundColor: "#ffffff",
                  padding: "12px 14px",
                  borderRadius: "8px",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  color: "var(--color-slate-800, #1e293b)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 700, fontSize: "13px" }}>{metric.name}</span>
                  <span
                    style={{
                      padding: "2px 8px",
                      borderRadius: "9999px",
                      fontSize: "11px",
                      fontWeight: 600,
                      backgroundColor: badge.bg,
                      color: badge.color,
                      border: `1px solid ${badge.border}`,
                    }}
                  >
                    {badge.label}
                  </span>
                </div>

                <div style={{ fontSize: "18px", fontWeight: 700, color: "var(--color-primary, #1e3a8a)" }}>
                  <span>{metric.value}</span>{" "}
                  <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--color-slate-500, #64748b)" }}>
                    {metric.unit}
                  </span>
                </div>

                <div style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)", display: "flex", flexDirection: "column", gap: "2px" }}>
                  <div>Khung thời gian: <strong>{metric.timeWindow}</strong></div>
                  <div>Độ tươi: <strong>{metric.freshness}</strong></div>
                  <div>Nguồn: <code>{metric.source}</code></div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
