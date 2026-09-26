import React, { useState } from "react";

export interface PrivacyNoticeData {
  version: string;
  effectiveDate: string;
  purpose: string;
  hasConsented: boolean;
}

export interface PrivacyRequestStatus {
  requestId: string;
  requestType: "EXPORT_DATA" | "DELETE_DATA" | "RECTIFY_DATA";
  status: "received" | "processing" | "completed" | "rejected";
  submittedAt: string;
}

export interface PrivacyCenterProps {
  notice: PrivacyNoticeData;
  requests?: PrivacyRequestStatus[];
  onConsentChange?: (consented: boolean) => void;
}

const requestTypeLabels: Record<PrivacyRequestStatus["requestType"], string> = {
  EXPORT_DATA: "Đang xử lý xuất dữ liệu cá nhân",
  DELETE_DATA: "Yêu cầu xóa dữ liệu cá nhân",
  RECTIFY_DATA: "Yêu cầu đính chính dữ liệu",
};

export function PrivacyCenter({
  notice,
  requests = [],
  onConsentChange,
}: PrivacyCenterProps) {
  const [consented, setConsented] = useState(notice.hasConsented);

  const handleToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.checked;
    setConsented(val);
    onConsentChange?.(val);
  };

  return (
    <div
      role="region"
      aria-label="Trung tâm quyền riêng tư & bảo vệ dữ liệu"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        maxWidth: "800px",
      }}
    >
      <div>
        <h2 style={{ margin: "0 0 6px 0", fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
          Trung tâm Quyền riêng tư & Bảo vệ Dữ liệu (HUCE Demo)
        </h2>
        <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)", lineHeight: 1.6 }}>
          Chính sách minh bạch dữ liệu theo quy định bảo vệ dữ liệu cá nhân Nghị định 13/2023/NĐ-CP.
        </p>
      </div>

      {/* Versioned Notice Section */}
      <div
        style={{
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          borderRadius: "var(--radius-lg, 14px)",
          padding: "24px",
          backgroundColor: "#ffffff",
          boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.04))",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
            Thông cáo Quyền riêng tư
          </h3>
          <span
            style={{
              fontSize: "12px",
              color: "var(--color-primary, #1e3a8a)",
              backgroundColor: "var(--color-primary-light, #eff6ff)",
              padding: "3px 10px",
              borderRadius: "9999px",
              fontWeight: 600,
            }}
          >
            Phiên bản: {notice.version} (Hiệu lực: {notice.effectiveDate})
          </span>
        </div>

        <div style={{ fontSize: "14px", marginBottom: "20px", backgroundColor: "var(--color-slate-50, #f8fafc)", padding: "16px", borderRadius: "var(--radius-md, 8px)" }}>
          <p style={{ fontWeight: 600, margin: "0 0 6px 0", color: "var(--color-slate-800, #1e293b)" }}>
            Mục đích xử lý dữ liệu:
          </p>
          <p style={{ margin: 0, color: "var(--color-slate-600, #475569)", lineHeight: 1.6 }}>
            {notice.purpose}
          </p>
        </div>

        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontSize: "14px",
            fontWeight: 600,
            color: "var(--color-slate-800, #1e293b)",
            cursor: "pointer",
            padding: "12px 16px",
            borderRadius: "var(--radius-md, 8px)",
            backgroundColor: consented ? "var(--color-primary-light, #eff6ff)" : "var(--color-slate-50, #f8fafc)",
            border: `1px solid ${consented ? "var(--color-primary-border, #bfdbfe)" : "var(--color-slate-200, #e2e8f0)"}`,
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          <input
            type="checkbox"
            checked={consented}
            onChange={handleToggle}
            style={{ width: "18px", height: "18px", cursor: "pointer", accentColor: "var(--color-primary, #1e3a8a)" }}
          />
          <span>Tôi đồng ý với chính sách xử lý dữ liệu phục vụ nghiên cứu và hỗ trợ đào tạo</span>
        </label>
      </div>

      {/* Privacy Requests Status */}
      <div
        style={{
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          borderRadius: "var(--radius-lg, 14px)",
          padding: "24px",
          backgroundColor: "#ffffff",
          boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.04))",
        }}
      >
        <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
          Trạng thái yêu cầu dữ liệu của bạn
        </h3>

        {requests.length === 0 ? (
          <p style={{ fontSize: "14px", color: "var(--color-slate-500, #64748b)", margin: 0 }}>
            Bạn chưa gửi yêu cầu trích xuất hoặc xóa dữ liệu nào.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {requests.map((req) => (
              <div
                key={req.requestId}
                aria-live="polite"
                style={{
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  borderRadius: "var(--radius-md, 8px)",
                  padding: "14px 18px",
                  backgroundColor: "var(--color-slate-50, #f8fafc)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "10px",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--color-slate-900, #0f172a)" }}>
                    {requestTypeLabels[req.requestType] || req.requestType}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)", marginTop: "2px" }}>
                    Mã yêu cầu: {req.requestId} • Ngày gửi: {req.submittedAt}
                  </div>
                </div>

                <span
                  style={{
                    padding: "3px 10px",
                    borderRadius: "9999px",
                    fontSize: "12px",
                    fontWeight: 600,
                    backgroundColor: req.status === "completed" ? "#f0fdf4" : "#eff6ff",
                    color: req.status === "completed" ? "#15803d" : "#1d4ed8",
                    border: `1px solid ${req.status === "completed" ? "#bbf7d0" : "#bfdbfe"}`,
                  }}
                >
                  {req.status === "completed" ? "Đã hoàn thành" : "Đang xử lý"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
