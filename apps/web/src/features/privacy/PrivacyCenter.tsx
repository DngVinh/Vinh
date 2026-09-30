import React, { useState } from "react";
import { ShieldCheckIcon, ClockIcon, AlertTriangleIcon } from "../../components/Icons";

export interface PrivacyNoticeData {
  version: string;
  effectiveDate: string;
  purpose: string;
  hasConsented: boolean;
}

export interface PrivacyRequestStatus {
  requestId: string;
  requestType: "EXPORT_DATA" | "DELETE_DATA" | "RECTIFY_DATA";
  status: "received" | "processing" | "completed" | "rejected" | "legal_hold" | "denied";
  submittedAt: string;
}

export interface PrivacyCenterProps {
  notice: PrivacyNoticeData;
  requests?: PrivacyRequestStatus[];
  isPendingConfirmation?: boolean;
  onConsentChange?: (consented: boolean) => void;
  onRequestErasure?: () => void;
}

const requestTypeLabels: Record<PrivacyRequestStatus["requestType"], string> = {
  EXPORT_DATA: "Yêu cầu xuất dữ liệu cá nhân",
  DELETE_DATA: "Yêu cầu xóa dữ liệu cá nhân",
  RECTIFY_DATA: "Yêu cầu đính chính dữ liệu",
};

const requestStatusLabels: Record<
  PrivacyRequestStatus["status"],
  { label: string; bg: string; color: string; border: string; explanation?: string }
> = {
  received: { label: "Đã tiếp nhận", bg: "var(--color-slate-100, #f1f5f9)", color: "var(--color-slate-700, #334155)", border: "var(--color-slate-300, #cbd5e1)" },
  processing: { label: "Đang xử lý", bg: "var(--color-blue-50, #eff6ff)", color: "var(--color-blue-700, #1d4ed8)", border: "var(--color-blue-200, #bfdbfe)" },
  completed: { label: "Đã hoàn thành", bg: "var(--color-emerald-50, #ecfdf5)", color: "var(--color-emerald-800, #065f46)", border: "var(--color-emerald-200, #a7f3d0)" },
  rejected: { label: "Không thể thực hiện", bg: "var(--color-amber-50, #fffbeb)", color: "var(--color-amber-800, #92400e)", border: "var(--color-amber-200, #fde68a)" },
  legal_hold: {
    label: "Tạm giữ pháp lý",
    bg: "#fef3c7",
    color: "#92400e",
    border: "#fde68a",
    explanation: "Dữ liệu đang được lưu trữ bắt buộc theo quy định lưu trữ của cơ sở đào tạo.",
  },
  denied: {
    label: "Bị từ chối theo quy định",
    bg: "#fef2f2",
    color: "#991b1b",
    border: "#fecaca",
    explanation: "Yêu cầu không thể thực hiện do không đáp ứng quy định hiện hành.",
  },
};

export function PrivacyCenter({
  notice,
  requests = [],
  isPendingConfirmation = false,
  onConsentChange,
  onRequestErasure,
}: PrivacyCenterProps) {
  const [consented, setConsented] = useState<boolean>(Boolean(notice.hasConsented));
  const [announcement, setAnnouncement] = useState<string | null>(null);
  const [isConfirmingErasure, setIsConfirmingErasure] = useState<boolean>(false);

  const handleToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isPendingConfirmation) return;
    const nextConsent = e.target.checked;
    setConsented(nextConsent);
    setAnnouncement(`Đã cập nhật lựa chọn đồng ý: ${nextConsent ? "Đã bật" : "Đã tắt"}`);
    onConsentChange?.(nextConsent);
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
      {/* Accessible Status Announcement */}
      {announcement && (
        <div
          role="status"
          aria-live="polite"
          style={{
            position: "absolute",
            width: "1px",
            height: "1px",
            padding: 0,
            margin: "-1px",
            overflow: "hidden",
            clip: "rect(0, 0, 0, 0)",
            whiteSpace: "nowrap",
            border: 0,
          }}
        >
          {announcement}
        </div>
      )}

      {/* Header */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "var(--radius-md, 10px)",
              backgroundColor: "var(--color-primary-light, #eff6ff)",
              color: "var(--color-primary, #1e3a8a)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ShieldCheckIcon size={20} />
          </div>
          <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
            Trung tâm Quyền riêng tư & Bảo vệ Dữ liệu (HUCE Demo)
          </h2>
        </div>
        <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)", lineHeight: 1.6 }}>
          Chính sách minh bạch dữ liệu theo quy định bảo vệ dữ liệu cá nhân Nghị định 13/2023/NĐ-CP.
        </p>
      </div>

      {/* Section 1: Required Processing */}
      <div
        style={{
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          borderRadius: "var(--radius-lg, 14px)",
          padding: "24px",
          backgroundColor: "#ffffff",
          boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        }}
      >
        <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
          1. Xử lý dữ liệu bắt buộc
        </h3>
        <div style={{ fontSize: "14px", backgroundColor: "var(--color-slate-50, #f8fafc)", padding: "16px", borderRadius: "var(--radius-md, 10px)", border: "1px solid var(--color-slate-200, #e2e8f0)" }}>
          <p style={{ fontWeight: 600, margin: "0 0 6px 0", color: "var(--color-slate-800, #1e293b)" }}>
            Cơ sở pháp lý & Phạm vi phục vụ:
          </p>
          <p style={{ margin: 0, color: "var(--color-slate-700, #334155)", lineHeight: 1.6 }}>
            Dữ liệu tài khoản (Mã sinh viên, họ tên, lớp, lịch học và yêu cầu hành chính) được xử lý bắt buộc để vận hành tài khoản và dịch vụ Một cửa số phục vụ hoạt động đào tạo tại Trường Đại học Xây dựng Hà Nội (HUCE Demo).
          </p>
        </div>
      </div>

      {/* Section 2: Optional Processing & Granular Consent */}
      <div
        style={{
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          borderRadius: "var(--radius-lg, 14px)",
          padding: "24px",
          backgroundColor: "#ffffff",
          boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
            2. Xử lý dữ liệu tùy chọn
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
            Phiên bản {notice.version} · Có hiệu lực từ {notice.effectiveDate}
          </span>
        </div>

        <div style={{ fontSize: "14px", marginBottom: "20px", backgroundColor: "var(--color-slate-50, #f8fafc)", padding: "16px", borderRadius: "var(--radius-md, 10px)", border: "1px solid var(--color-slate-200, #e2e8f0)" }}>
          <p style={{ fontWeight: 600, margin: "0 0 6px 0", color: "var(--color-slate-800, #1e293b)" }}>
            Mục đích nghiên cứu & Nâng cao chất lượng AI:
          </p>
          <p style={{ margin: 0, color: "var(--color-slate-700, #334155)", lineHeight: 1.6 }}>
            {notice.purpose} Bạn có quyền tự do lựa chọn đồng ý hoặc từ chối. Việc không đồng ý hoàn toàn không làm suy giảm quyền lợi của bạn đối với dịch vụ Một cửa số.
          </p>
        </div>

        {/* Server Confirmation State (AC-TASK-WEB-PRIV-003-01) */}
        {isPendingConfirmation && (
          <div
            role="status"
            style={{
              padding: "10px 14px",
              marginBottom: "14px",
              borderRadius: "8px",
              backgroundColor: "#eff6ff",
              border: "1px solid #bfdbfe",
              fontSize: "13px",
              color: "#1d4ed8",
              fontWeight: 500,
            }}
          >
            Đang chờ máy chủ xác nhận trạng thái đồng ý...
          </div>
        )}

        {/* Consent Checkbox Control (Never Preselected, AC-TASK-WEB-PRIV-003-01) */}
        <label
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "12px",
            fontSize: "14px",
            fontWeight: 600,
            color: "var(--color-slate-800, #1e293b)",
            cursor: isPendingConfirmation ? "not-allowed" : "pointer",
            padding: "14px 18px",
            borderRadius: "var(--radius-md, 10px)",
            backgroundColor: consented ? "var(--color-primary-light, #eff6ff)" : "var(--color-slate-50, #f8fafc)",
            border: `1.5px solid ${consented ? "var(--color-primary-border, #bfdbfe)" : "var(--color-slate-200, #e2e8f0)"}`,
            opacity: isPendingConfirmation ? 0.7 : 1,
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          <input
            type="checkbox"
            checked={consented}
            disabled={isPendingConfirmation}
            onChange={handleToggle}
            style={{ width: "18px", height: "18px", marginTop: "2px", cursor: isPendingConfirmation ? "not-allowed" : "pointer", accentColor: "var(--color-primary, #1e3a8a)" }}
          />
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            <span>Đồng ý chia sẻ dữ liệu hội thoại ẩn danh để nâng cao chất lượng AI</span>
            <span style={{ fontSize: "12px", fontWeight: 400, color: "var(--color-slate-500, #64748b)" }}>
              Dữ liệu sẽ được khử định danh toàn diện trước khi đưa vào tập huấn luyện đánh giá chất lượng.
            </span>
          </div>
        </label>
      </div>

      {/* Section 3: Consequential Action - Erasure (AC-TASK-WEB-PRIV-003-02) */}
      <div
        style={{
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          borderRadius: "var(--radius-lg, 14px)",
          padding: "24px",
          backgroundColor: "#ffffff",
          boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        }}
      >
        <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
          3. Thực hiện quyền xóa dữ liệu cá nhân (Right to Erasure)
        </h3>
        <p style={{ margin: "0 0 16px 0", fontSize: "13px", color: "var(--color-slate-600, #475569)", lineHeight: 1.6 }}>
          Bạn có quyền yêu cầu xóa vĩnh viễn các dữ liệu hội thoại và dữ liệu tài khoản theo quy định bảo vệ dữ liệu cá nhân.
        </p>

        {!isConfirmingErasure ? (
          <button
            type="button"
            onClick={() => setIsConfirmingErasure(true)}
            style={{
              padding: "10px 18px",
              backgroundColor: "#fee2e2",
              color: "#b91c1c",
              border: "1px solid #fca5a5",
              borderRadius: "8px",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            Yêu cầu xóa dữ liệu vĩnh viễn
          </button>
        ) : (
          <div
            style={{
              padding: "16px 20px",
              backgroundColor: "#fff1f2",
              borderRadius: "8px",
              border: "1.5px solid #f43f5e",
              fontSize: "13px",
              color: "#881337",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, fontSize: "14px", marginBottom: "8px" }}>
              <AlertTriangleIcon size={18} />
              <span>Xác nhận yêu cầu xóa dữ liệu có hệ quả nghiêm trọng</span>
            </div>
            <p style={{ margin: "0 0 6px 0" }}>
              <strong>Phạm vi áp dụng:</strong> Toàn bộ dữ liệu hội thoại, lịch học và yêu cầu hành chính cá nhân trên hệ thống.
            </p>
            <p style={{ margin: "0 0 12px 0" }}>
              <strong>Hệ quả pháp lý:</strong> Hành động không thể hoàn tác. Dữ liệu sẽ bị xóa hoặc ẩn danh vĩnh viễn, bạn sẽ không thể khôi phục lại lịch sử hỗ trợ.
            </p>
            <div style={{ display: "flex", gap: "10px" }}>
              <button
                type="button"
                onClick={() => setIsConfirmingErasure(false)}
                style={{
                  padding: "8px 16px",
                  backgroundColor: "#ffffff",
                  border: "1px solid #cbd5e1",
                  borderRadius: "6px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  color: "#334155",
                }}
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsConfirmingErasure(false);
                  onRequestErasure?.();
                }}
                style={{
                  padding: "8px 18px",
                  backgroundColor: "#e11d48",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  color: "#ffffff",
                }}
              >
                Xác nhận xóa vĩnh viễn
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Section 4: Privacy Requests Status (AC-TASK-WEB-PRIV-003-03) */}
      <div
        style={{
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          borderRadius: "var(--radius-lg, 14px)",
          padding: "24px",
          backgroundColor: "#ffffff",
          boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        }}
      >
        <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
          4. Trạng thái yêu cầu quyền dữ liệu của bạn
        </h3>

        {requests.length === 0 ? (
          <p style={{ fontSize: "14px", color: "var(--color-slate-500, #64748b)", margin: 0 }}>
            Bạn chưa gửi yêu cầu trích xuất hoặc xóa dữ liệu nào.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {requests.map((request) => {
              const badge = requestStatusLabels[request.status] || requestStatusLabels.received;
              return (
                <div
                  key={request.requestId}
                  style={{
                    border: "1px solid var(--color-slate-200, #e2e8f0)",
                    borderRadius: "var(--radius-md, 10px)",
                    padding: "14px 18px",
                    backgroundColor: "var(--color-slate-50, #f8fafc)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--color-slate-900, #0f172a)" }}>
                        {requestTypeLabels[request.requestType] || requestTypeLabels.EXPORT_DATA}
                      </div>
                      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--color-slate-500, #64748b)", marginTop: "4px" }}>
                        <ClockIcon size={12} />
                        <span>Mã yêu cầu: {request.requestId} • Ngày gửi: {request.submittedAt}</span>
                      </div>
                    </div>

                    <span
                      style={{
                        padding: "3px 12px",
                        borderRadius: "9999px",
                        fontSize: "12px",
                        fontWeight: 600,
                        backgroundColor: badge.bg,
                        color: badge.color,
                        border: `1px solid ${badge.border}`,
                      }}
                    >
                      {badge.label}
                    </span>
                  </div>

                  {badge.explanation && (
                    <div style={{ fontSize: "12px", color: badge.color, backgroundColor: badge.bg, padding: "6px 10px", borderRadius: "4px" }}>
                      {badge.explanation}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
