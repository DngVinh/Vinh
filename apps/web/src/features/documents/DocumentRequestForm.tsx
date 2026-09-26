import React, { useState, type FormEvent } from "react";
import { ArrowRightIcon, FileTextIcon, ClockIcon } from "../../components/Icons";

export interface DocumentRequestPayload {
  documentType: string;
  quantity: number;
  reason: string;
}

export interface DocumentRequestFormProps {
  onSubmit?: (data: DocumentRequestPayload) => void;
  hideTitle?: boolean;
}

export function DocumentRequestForm({ onSubmit, hideTitle = false }: DocumentRequestFormProps) {
  const [documentType, setDocumentType] = useState("xac_nhan_sinh_vien");
  const [quantity, setQuantity] = useState(1);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const textarea = document.getElementById("reason") as HTMLTextAreaElement | null;
    const finalReason = (reason || textarea?.value || "").trim();
    if (!finalReason) {
      setError("Vui lòng nhập mục đích xin cấp giấy tờ.");
      return;
    }
    setError(null);
    onSubmit?.({
      documentType,
      quantity: Number(quantity),
      reason: finalReason,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        backgroundColor: "#ffffff",
        padding: hideTitle ? "8px 0 0 0" : "32px",
        borderRadius: hideTitle ? "0" : "var(--radius-xl, 20px)",
        border: hideTitle ? "none" : "1px solid var(--color-slate-200, #e2e8f0)",
        boxShadow: hideTitle ? "none" : "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
      }}
    >
      {!hideTitle && (
        <div style={{ borderBottom: "1px solid var(--color-slate-100, #f1f5f9)", paddingBottom: "18px" }}>
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
              <FileTextIcon size={20} />
            </div>
            <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}>
              Đăng ký cấp giấy tờ sinh viên
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)" }}>
            Hệ thống một cửa số tiếp nhận và chuyển tiếp tới Phòng Quản lý Đào tạo HUCE xử lý
          </p>
        </div>
      )}

      {error && (
        <div
          role="alert"
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-md, 10px)",
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#991b1b",
            fontSize: "13px",
            fontWeight: 500,
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: "#dc2626",
              flexShrink: 0,
            }}
          />
          <span>{error}</span>
        </div>
      )}

      {/* Document Type */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <label htmlFor="doc-type" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
          Loại giấy tờ <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <select
          id="doc-type"
          value={documentType}
          onChange={(e) => setDocumentType(e.target.value)}
          style={{
            padding: "10px 14px",
            borderRadius: "var(--radius-md, 10px)",
            border: "1.5px solid var(--color-slate-300, #cbd5e1)",
            backgroundColor: "#ffffff",
            fontSize: "14px",
            color: "var(--color-slate-900, #0f172a)",
            minHeight: "44px",
            boxShadow: "inset 0 1px 2px rgba(0,0,0,0.03)",
            cursor: "pointer",
          }}
        >
          <option value="xac_nhan_sinh_vien">Giấy xác nhận sinh viên (mục đích chung)</option>
          <option value="bang_diem_tam_thoi">Bảng điểm tạm thời (xác nhận học phần đã hoàn thành)</option>
          <option value="gioi_thieu_thuc_tap">Giấy giới thiệu thực tập doanh nghiệp</option>
          <option value="hoan_nghia_vu_quan_su">Giấy xác nhận tạm hoãn NVQS</option>
        </select>
      </div>

      {/* Quantity */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <label htmlFor="quantity" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
          Số lượng bản <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <input
            id="quantity"
            type="number"
            min={1}
            max={5}
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, Math.min(5, Number(e.target.value))))}
            style={{
              padding: "10px 14px",
              borderRadius: "var(--radius-md, 10px)",
              border: "1.5px solid var(--color-slate-300, #cbd5e1)",
              fontSize: "14px",
              color: "var(--color-slate-900, #0f172a)",
              minHeight: "44px",
              width: "100px",
              boxShadow: "inset 0 1px 2px rgba(0,0,0,0.03)",
            }}
          />
          <span style={{ fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
            (Tối đa 5 bản/lần đăng ký)
          </span>
        </div>
      </div>

      {/* Purpose / Reason */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <label htmlFor="reason" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
          Mục đích xin cấp <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <textarea
          id="reason"
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Ví dụ: Vay vốn sinh viên chính sách tại địa phương, bổ sung hồ sơ xin thực tập..."
          style={{
            padding: "12px 14px",
            borderRadius: "var(--radius-md, 10px)",
            border: "1.5px solid var(--color-slate-300, #cbd5e1)",
            fontSize: "14px",
            color: "var(--color-slate-900, #0f172a)",
            fontFamily: "inherit",
            lineHeight: 1.5,
            resize: "vertical",
            boxShadow: "inset 0 1px 2px rgba(0,0,0,0.03)",
          }}
        />
      </div>

      {/* Turnaround expectation & Submit Button */}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "16px", marginTop: "8px" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
          <ClockIcon size={16} />
          <span>Thời gian xử lý dự kiến: 1 - 2 ngày làm việc</span>
        </div>

        <button
          type="submit"
          style={{
            padding: "12px 24px",
            minHeight: "44px",
            backgroundColor: "var(--color-primary, #1e3a8a)",
            color: "#ffffff",
            border: "none",
            borderRadius: "var(--radius-md, 10px)",
            fontWeight: 600,
            fontSize: "14px",
            cursor: "pointer",
            boxShadow: "var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.06))",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
          }}
        >
          <span>Tiếp tục xác nhận</span>
          <ArrowRightIcon size={16} />
        </button>
      </div>
    </form>
  );
}
