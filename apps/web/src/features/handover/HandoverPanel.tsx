import React, { useState, useEffect } from "react";
import { ShieldCheckIcon, CheckCircle2Icon, ClockIcon, XIcon } from "../../components/Icons";

export interface HandoverReceipt {
  receiptId: string;
  department: string;
  reason: string;
  assignedQueue: string;
  estimatedResponseHours: number;
  status: "queued" | "assigned" | "in_review";
}

export interface HandoverPanelProps {
  receipt: HandoverReceipt;
  isAvailable?: boolean;
}

export function HandoverPanel({
  receipt,
  isAvailable = true,
}: HandoverPanelProps) {
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);

  useEffect(() => {
    if (!showEmergencyModal) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowEmergencyModal(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showEmergencyModal]);

  return (
    <div
      role="region"
      aria-label="Thông tin chuyển tiếp chuyên viên"
      style={{
        border: "1px solid var(--color-slate-200, #e2e8f0)",
        borderRadius: "var(--radius-xl, 20px)",
        padding: "28px",
        backgroundColor: "#ffffff",
        boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {/* Header Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "14px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "var(--radius-md, 10px)",
              backgroundColor: "var(--color-primary-light, #eff6ff)",
              color: "var(--color-primary, #1e3a8a)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ShieldCheckIcon size={24} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}>
              Chuyển tiếp chuyên viên hỗ trợ (Human-in-the-Loop)
            </h2>
            <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
              Trường hợp cần can thiệp xử lý ngoài phạm vi của AI trợ lý ảo
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setShowEmergencyModal(true)}
          style={{
            padding: "9px 18px",
            borderRadius: "var(--radius-md, 10px)",
            border: "1px solid #fca5a5",
            backgroundColor: "#fef2f2",
            color: "#991b1b",
            fontWeight: 600,
            fontSize: "13px",
            cursor: "pointer",
            minHeight: "44px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
            transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
          }}
        >
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: "#dc2626",
            }}
          />
          <span>Đường dây nóng khẩn cấp</span>
        </button>
      </div>

      {/* Availability Notice */}
      {!isAvailable ? (
        <div
          role="alert"
          style={{
            padding: "16px 20px",
            borderRadius: "var(--radius-lg, 14px)",
            backgroundColor: "#fffbeb",
            border: "1px solid #fde68a",
            color: "#92400e",
            fontSize: "13px",
            lineHeight: 1.6,
          }}
        >
          <p style={{ margin: "0 0 4px 0", fontWeight: 700 }}>
            Hiện ngoài giờ tiếp nhận trực tuyến (Giờ làm việc: 08:00 - 17:00 các ngày trong tuần).
          </p>
          <p style={{ margin: 0 }}>
            Yêu cầu của bạn đã được ghi nhận vào hàng đợi và sẽ được xử lý vào phiên làm việc tiếp theo.
          </p>
        </div>
      ) : (
        <div
          style={{
            padding: "14px 20px",
            borderRadius: "var(--radius-lg, 14px)",
            backgroundColor: "#ecfdf5",
            border: "1px solid #a7f3d0",
            color: "#065f46",
            fontSize: "13px",
            fontWeight: 500,
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <CheckCircle2Icon size={18} style={{ color: "#10b981" }} />
          <span>Chuyên viên tiếp nhận đã được thông báo và đang xem xét yêu cầu của bạn.</span>
        </div>
      )}

      {/* Handover Details */}
      <div
        style={{
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          borderRadius: "var(--radius-lg, 14px)",
          padding: "20px 24px",
          backgroundColor: "var(--color-slate-50, #f8fafc)",
          fontSize: "14px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <span style={{ color: "var(--color-slate-600, #475569)" }}>Mã tiếp nhận: </span>
            <strong style={{ color: "var(--color-slate-900, #0f172a)" }}>Mã biên nhận: {receipt.receiptId}</strong>
          </div>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <ClockIcon size={15} style={{ color: "var(--color-primary, #1e3a8a)" }} />
            <span style={{ color: "var(--color-slate-600, #475569)" }}>Thời gian ước tính: </span>
            <strong style={{ color: "var(--color-primary, #1e3a8a)" }}>Thời gian phản hồi dự kiến: {receipt.estimatedResponseHours} giờ</strong>
          </div>
        </div>
        <div>
          <span style={{ color: "var(--color-slate-600, #475569)" }}>Đơn vị xử lý: </span>
          <strong style={{ color: "var(--color-slate-900, #0f172a)" }}>{receipt.department}</strong>
        </div>
        <div>
          <span style={{ color: "var(--color-slate-600, #475569)" }}>Lý do chuyển tiếp: </span>
          <span style={{ color: "var(--color-slate-800, #1e293b)" }}>{receipt.reason}</span>
        </div>
      </div>

      {/* Emergency Modal */}
      {showEmergencyModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="emergency-title"
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(15, 23, 42, 0.6)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 3000,
            padding: "20px",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-xl, 20px)",
              padding: "28px",
              maxWidth: "500px",
              width: "100%",
              boxShadow: "var(--shadow-modal, 0 20px 25px -5px rgba(0,0,0,0.12))",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 id="emergency-title" style={{ margin: 0, color: "#991b1b", fontSize: "18px", fontWeight: 700, letterSpacing: "-0.3px" }}>
                Hotline Y tế & Tâm lý HUCE
              </h3>
              <button
                type="button"
                onClick={() => setShowEmergencyModal(false)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "18px",
                  color: "var(--color-slate-500, #64748b)",
                  padding: "4px 8px",
                  borderRadius: "var(--radius-sm, 6px)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                aria-label="Đóng dialog"
              >
                <XIcon size={18} />
              </button>
            </div>
            <p style={{ fontSize: "14px", color: "var(--color-slate-700, #334155)", lineHeight: 1.6, margin: "0 0 16px 0" }}>
              Trong trường hợp khẩn cấp về an ninh, y tế hoặc tâm lý sinh viên, vui lòng liên hệ ngay:
            </p>
            <ul style={{ fontSize: "14px", paddingLeft: "20px", margin: "16px 0", color: "var(--color-slate-900, #0f172a)", lineHeight: 2 }}>
              <li>Trực ban bảo vệ / Khẩn cấp: <strong style={{ color: "#991b1b" }}>024-3869-XXXX</strong></li>
              <li>Phòng Y tế trường: <strong style={{ color: "#991b1b" }}>024-3869-YYYY</strong></li>
            </ul>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "24px" }}>
              <button
                type="button"
                onClick={() => setShowEmergencyModal(false)}
                style={{
                  padding: "10px 24px",
                  borderRadius: "var(--radius-md, 10px)",
                  border: "none",
                  backgroundColor: "var(--color-primary, #1e3a8a)",
                  color: "#ffffff",
                  fontWeight: 600,
                  fontSize: "14px",
                  cursor: "pointer",
                  minHeight: "44px",
                  boxShadow: "var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.06))",
                  transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                }}
              >
                Đã hiểu
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
