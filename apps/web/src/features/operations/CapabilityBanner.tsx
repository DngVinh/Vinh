import React from "react";
import { AlertTriangleIcon } from "../../components/Icons";

export type OperationalMode = "healthy" | "degraded" | "safe_mode" | "outage";

export interface SystemOperationalStatus {
  mode: OperationalMode;
  message: string;
  affectedServices: string[];
}

export interface CapabilityBannerProps {
  status: SystemOperationalStatus;
}

export function CapabilityBanner({ status }: CapabilityBannerProps) {
  if (status.mode === "healthy") {
    return null;
  }

  const isCritical = status.mode === "outage" || status.mode === "safe_mode";

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        backgroundColor: isCritical ? "#fef2f2" : "#fffbeb",
        borderBottom: `1px solid ${isCritical ? "#fca5a5" : "#fde68a"}`,
        color: isCritical ? "#991b1b" : "#92400e",
        padding: "12px 24px",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        fontSize: "13px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700 }}>
        <AlertTriangleIcon size={18} />
        <span>Cảnh báo vận hành hệ thống ({status.mode.toUpperCase()}):</span>
        <span style={{ fontWeight: 500 }}>{status.message}</span>
      </div>

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
    </div>
  );
}
