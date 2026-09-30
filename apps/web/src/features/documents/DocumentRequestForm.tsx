import React, { useState, type FormEvent, type ChangeEvent } from "react";
import { ArrowRightIcon, FileTextIcon, ClockIcon, CheckCircle2Icon, AlertTriangleIcon, XIcon } from "../../components/Icons";

export interface DocumentRequestPayload {
  documentType: string;
  deliveryMethod?: string;
  quantity: number;
  reason: string;
  attachedFiles?: string[];
}

export interface DocumentRequestFormProps {
  onSubmit?: (data: DocumentRequestPayload) => void;
  onCancel?: () => void;
  hideTitle?: boolean;
}

const docTypeLabels: Record<string, string> = {
  xac_nhan_sinh_vien: "Giấy xác nhận sinh viên (mục đích chung)",
  bang_diem_tam_thoi: "Bảng điểm tạm thời (xác nhận học phần đã hoàn thành)",
  gioi_thieu_thuc_tap: "Giấy giới thiệu thực tập doanh nghiệp",
  hoan_nghia_vu_quan_su: "Giấy xác nhận tạm hoãn NVQS",
};

const docPreparationGuidance: Record<string, { guide: string; documents: string[] }> = {
  xac_nhan_sinh_vien: {
    guide: "Áp dụng cho thủ tục vay vốn, xin trợ cấp hoặc xác nhận tư cách sinh viên.",
    documents: ["Ảnh thẻ 3x4 nếu yêu cầu đóng dấu giáp lai ảnh", "Thông tin chính xác về nơi nộp giấy xác nhận"],
  },
  bang_diem_tam_thoi: {
    guide: "Bảng điểm tính đến học kỳ gần nhất đã có điểm tổng kết chính thức.",
    documents: ["Mã sinh viên và chương trình đào tạo", "Đã hoàn thành đánh giá môn học trên Cổng đào tạo"],
  },
  gioi_thieu_thuc_tap: {
    guide: "Cấp cho sinh viên đủ điều kiện thực tập tốt nghiệp hoặc thực tập chuyên ngành.",
    documents: ["Tên cơ quan, doanh nghiệp hoặc đơn vị tiếp nhận thực tập", "Thời gian dự kiến bắt đầu và kết thúc"],
  },
  hoan_nghia_vu_quan_su: {
    guide: "Giấy xác nhận gửi Ban chỉ huy Quân sự cấp xã/phường nơi đăng ký thường trú.",
    documents: ["Lệnh gọi khám tuyển hoặc giấy báo nhập ngũ của Ban chỉ huy quân sự", "Bản sao CCCD của sinh viên"],
  },
};

const deliveryLabels: Record<string, string> = {
  pickup: "Nhận trực tiếp tại bộ phận Một cửa (Phòng 102 - Tòa H1)",
  email: "Bản điện tử (PDF gửi qua email sinh viên)",
};

interface AiSuggestion {
  targetType: string;
  label: string;
  confidence: number;
  reason: string;
}

export function DocumentRequestForm({ onSubmit, onCancel, hideTitle = false }: DocumentRequestFormProps) {
  const [step, setStep] = useState<"editing" | "preview">("editing");
  const [documentType, setDocumentType] = useState("xac_nhan_sinh_vien");
  const [deliveryMethod, setDeliveryMethod] = useState("pickup");
  const [quantity, setQuantity] = useState(1);
  const [reason, setReason] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  // AI Assistant suggestion state
  const [aiSuggestion, setAiSuggestion] = useState<AiSuggestion | null>(null);

  const analyzeReasonWithAi = (text: string, currentDocType: string) => {
    const lower = text.toLowerCase();
    if (lower.includes("thực tập") || lower.includes("doanh nghiệp") || lower.includes("công ty")) {
      if (currentDocType !== "gioi_thieu_thuc_tap") {
        setAiSuggestion({
          targetType: "gioi_thieu_thuc_tap",
          label: "Giấy giới thiệu thực tập doanh nghiệp",
          confidence: 94,
          reason: "Phát hiện từ khóa thực tập/doanh nghiệp trong lý do xin cấp",
        });
        return;
      }
    } else if (lower.includes("bảng điểm") || lower.includes("học phần") || lower.includes("kết quả học tập") || lower.includes("gpa")) {
      if (currentDocType !== "bang_diem_tam_thoi") {
        setAiSuggestion({
          targetType: "bang_diem_tam_thoi",
          label: "Bảng điểm tạm thời (xác nhận học phần đã hoàn thành)",
          confidence: 92,
          reason: "Phát hiện từ khóa bảng điểm/học phần trong lý do xin cấp",
        });
        return;
      }
    } else if (lower.includes("nghĩa vụ") || lower.includes("quân sự") || lower.includes("nhập ngũ") || lower.includes("nvqs")) {
      if (currentDocType !== "hoan_nghia_vu_quan_su") {
        setAiSuggestion({
          targetType: "hoan_nghia_vu_quan_su",
          label: "Giấy xác nhận tạm hoãn NVQS",
          confidence: 96,
          reason: "Phát hiện nội dung liên quan đến nghĩa vụ quân sự",
        });
        return;
      }
    }
    setAiSuggestion(null);
  };

  const handleReasonChange = (value: string) => {
    setReason(value);
    if (error) setError(null);
    analyzeReasonWithAi(value, documentType);
  };

  const applyAiSuggestion = (targetType: string) => {
    setDocumentType(targetType);
    setAiSuggestion(null);
  };

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map((f) => f.name);
      setAttachedFiles((prev) => Array.from(new Set([...prev, ...newFiles])));
    }
  };

  const removeFile = (fileName: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f !== fileName));
  };

  const handleProceedToPreview = (e: FormEvent) => {
    e.preventDefault();
    const finalReason = reason.trim();
    if (!finalReason) {
      setError("Vui lòng nhập mục đích xin cấp giấy tờ.");
      return;
    }
    setError(null);
    setStep("preview");
  };

  const handleConfirmSubmit = () => {
    onSubmit?.({
      documentType,
      deliveryMethod,
      quantity: Number(quantity),
      reason: reason.trim(),
      attachedFiles: attachedFiles.length > 0 ? attachedFiles : undefined,
    });
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      setStep("editing");
      setReason("");
      setAttachedFiles([]);
      setError(null);
    }
  };

  const guidance = docPreparationGuidance[documentType] || docPreparationGuidance.xac_nhan_sinh_vien;

  if (step === "preview") {
    return (
      <section
        aria-labelledby="preview-heading"
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
        <div style={{ borderBottom: "1px solid var(--color-slate-100, #f1f5f9)", paddingBottom: "16px" }}>
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
              <CheckCircle2Icon size={20} />
            </div>
            <h2
              id="preview-heading"
              style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}
            >
              Xác nhận thông tin yêu cầu cấp giấy tờ
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)" }}>
            Vui lòng kiểm tra kỹ các thông tin dưới đây trước khi gửi yêu cầu chính thức.
          </p>
        </div>

        {/* Structured Preview List */}
        <dl
          style={{
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: "16px",
            backgroundColor: "var(--color-slate-50, #f8fafc)",
            padding: "20px",
            borderRadius: "var(--radius-lg, 14px)",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            margin: 0,
          }}
        >
          <div>
            <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Loại giấy tờ
            </dt>
            <dd style={{ margin: "4px 0 0 0", fontSize: "15px", fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>
              {docTypeLabels[documentType] || documentType}
            </dd>
          </div>

          <div>
            <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Phương thức nhận
            </dt>
            <dd style={{ margin: "4px 0 0 0", fontSize: "14px", color: "var(--color-slate-800, #1e293b)" }}>
              {deliveryLabels[deliveryMethod] || deliveryMethod}
            </dd>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "16px" }}>
            <div>
              <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
                Số lượng
              </dt>
              <dd style={{ margin: "4px 0 0 0", fontSize: "14px", fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>
                {quantity} bản
              </dd>
            </div>

            <div>
              <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
                Lệ phí
              </dt>
              <dd style={{ margin: "4px 0 0 0", fontSize: "14px", fontWeight: 600, color: "var(--color-emerald-700, #047857)" }}>
                Miễn phí
              </dd>
            </div>

            <div>
              <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
                Thời gian xử lý dự kiến
              </dt>
              <dd style={{ margin: "4px 0 0 0", fontSize: "14px", color: "var(--color-slate-800, #1e293b)" }}>
                1 - 2 ngày làm việc
              </dd>
            </div>
          </div>

          <div>
            <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Mục đích xin cấp
            </dt>
            <dd style={{ margin: "4px 0 0 0", fontSize: "14px", color: "var(--color-slate-800, #1e293b)", lineHeight: 1.5 }}>
              {reason}
            </dd>
          </div>

          {attachedFiles.length > 0 && (
            <div>
              <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
                Tệp đính kèm ({attachedFiles.length})
              </dt>
              <dd style={{ margin: "4px 0 0 0", display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {attachedFiles.map((fn, idx) => (
                  <span
                    key={idx}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      backgroundColor: "#ffffff",
                      border: "1px solid var(--color-slate-300, #cbd5e1)",
                      borderRadius: "6px",
                      padding: "4px 10px",
                      fontSize: "13px",
                      color: "var(--color-slate-800, #1e293b)",
                    }}
                  >
                    <span aria-hidden="true">📎</span>
                    <span>{fn}</span>
                  </span>
                ))}
              </dd>
            </div>
          )}
        </dl>

        {/* Transparency Intake Checklist Preview */}
        <div
          style={{
            backgroundColor: "#f0fdf4",
            border: "1px solid #bbf7d0",
            borderRadius: "var(--radius-lg, 14px)",
            padding: "18px 20px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "16px" }}>📋</span>
              <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "#166534" }}>
                Tiêu chuẩn thẩm định của Cán bộ Một cửa (Bộ 6 Cổng tiếp nhận)
              </h3>
            </div>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: "9999px",
                backgroundColor: "#dcfce7",
                color: "#15803d",
                border: "1px solid #86efac",
              }}
            >
              ✓ Sẵn sàng 6/6 cổng
            </span>
          </div>

          <p style={{ margin: 0, fontSize: "13px", color: "#14532d", lineHeight: 1.5 }}>
            Sau khi bạn gửi, hệ thống Một cửa số và Cán bộ chuyên môn sẽ tự động đối chiếu hồ sơ theo 6 tiêu chuẩn nghiệp vụ:
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "8px",
              marginTop: "4px",
            }}
          >
            {[
              { title: "Xác minh danh tính & MSSV", badge: "VNeID", desc: "Khớp hồ sơ đào tạo chính quy" },
              { title: "Thẩm quyền giải quyết", badge: "Quy chế", desc: "Đúng thẩm quyền Một cửa số HUCE" },
              { title: "Kiểm tra đơn trùng lặp", badge: "30 ngày", desc: "Không có đơn trùng đang thụ lý" },
              { title: "Tính hợp lệ minh chứng", badge: "OCR", desc: attachedFiles.length > 0 ? "Đã đính kèm tệp minh chứng" : "Áp dụng theo thủ tục trực tuyến" },
              { title: "Cam kết SLA tiếp nhận", badge: "24h", desc: "Phản hồi trong vòng 24h làm việc" },
              { title: "Bảo vệ thông tin cá nhân", badge: "NĐ 13", desc: "Bảo mật & mã hóa thông tin nhạy cảm" },
            ].map((gate, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  backgroundColor: "#ffffff",
                  padding: "8px 12px",
                  borderRadius: "8px",
                  border: "1px solid #dcfce7",
                  fontSize: "12px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span style={{ color: "#16a34a", fontWeight: 700 }}>✓</span>
                  <span style={{ fontWeight: 600, color: "#1e293b" }}>{gate.title}</span>
                </div>
                <span
                  style={{
                    fontSize: "10px",
                    fontWeight: 700,
                    padding: "1px 6px",
                    borderRadius: "4px",
                    backgroundColor: "#f1f5f9",
                    color: "#475569",
                  }}
                >
                  {gate.badge}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "12px", marginTop: "8px" }}>
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              type="button"
              onClick={() => setStep("editing")}
              style={{
                padding: "10px 18px",
                minHeight: "44px",
                borderRadius: "var(--radius-md, 10px)",
                border: "1px solid var(--color-slate-300, #cbd5e1)",
                backgroundColor: "#ffffff",
                color: "var(--color-slate-700, #334155)",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
              }}
            >
              Quay lại chỉnh sửa
            </button>
            <button
              type="button"
              onClick={handleCancel}
              style={{
                padding: "10px 18px",
                minHeight: "44px",
                borderRadius: "var(--radius-md, 10px)",
                border: "none",
                backgroundColor: "transparent",
                color: "var(--color-slate-500, #64748b)",
                fontSize: "14px",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Hủy
            </button>
          </div>

          <button
            type="button"
            onClick={handleConfirmSubmit}
            style={{
              padding: "12px 28px",
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
            <span>Gửi yêu cầu</span>
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </section>
    );
  }

  return (
    <form
      onSubmit={handleProceedToPreview}
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
          id="reason-error"
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
          onChange={(e) => {
            setDocumentType(e.target.value);
            setAiSuggestion(null);
          }}
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

      {/* Document Preparation Guidance Card */}
      <div
        style={{
          padding: "14px 18px",
          borderRadius: "var(--radius-md, 10px)",
          backgroundColor: "var(--color-primary-light, #eff6ff)",
          border: "1px solid var(--color-blue-200, #bfdbfe)",
          fontSize: "13px",
          color: "var(--color-primary, #1e3a8a)",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
          <span>ℹ️</span> Hồ sơ & giấy tờ cần chuẩn bị:
        </div>
        <p style={{ margin: "0 0 6px 0", color: "var(--color-slate-700, #334155)" }}>{guidance.guide}</p>
        <ul style={{ margin: 0, paddingLeft: "20px", color: "var(--color-slate-800, #1e293b)", lineHeight: 1.5 }}>
          {guidance.documents.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </div>

      {/* Delivery Method */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <label htmlFor="delivery-method" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
          Phương thức nhận kết quả <span style={{ color: "#dc2626" }}>*</span>
        </label>
        <select
          id="delivery-method"
          value={deliveryMethod}
          onChange={(e) => setDeliveryMethod(e.target.value)}
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
          <option value="pickup">Nhận trực tiếp tại bộ phận Một cửa (Phòng 102 - Tòa H1)</option>
          <option value="email">Bản điện tử (PDF gửi qua email sinh viên)</option>
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
          onChange={(e) => handleReasonChange(e.target.value)}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={error ? "reason-error" : undefined}
          placeholder="Ví dụ: Vay vốn sinh viên chính sách tại địa phương, bổ sung hồ sơ xin thực tập..."
          style={{
            padding: "12px 14px",
            borderRadius: "var(--radius-md, 10px)",
            border: error ? "1.5px solid #dc2626" : "1.5px solid var(--color-slate-300, #cbd5e1)",
            fontSize: "14px",
            color: "var(--color-slate-900, #0f172a)",
            fontFamily: "inherit",
            lineHeight: 1.5,
            resize: "vertical",
            boxShadow: "inset 0 1px 2px rgba(0,0,0,0.03)",
          }}
        />

        {/* AI Assistant Suggestion Banner */}
        {aiSuggestion && (
          <div
            role="status"
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              backgroundColor: "#fdf4ff",
              border: "1px solid #f0abfc",
              color: "#86198f",
              fontSize: "13px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
              animation: "fadeIn 200ms ease",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span>✨</span>
              <span>
                <strong>Gợi ý AI phân loại ({aiSuggestion.confidence}%):</strong> Bạn có muốn đổi sang{" "}
                <strong>{aiSuggestion.label}</strong>?
              </span>
            </div>
            <div style={{ display: "flex", gap: "6px" }}>
              <button
                type="button"
                onClick={() => applyAiSuggestion(aiSuggestion.targetType)}
                style={{
                  padding: "4px 10px",
                  borderRadius: "6px",
                  border: "none",
                  backgroundColor: "#a21caf",
                  color: "#ffffff",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Áp dụng gợi ý
              </button>
              <button
                type="button"
                onClick={() => setAiSuggestion(null)}
                aria-label="Bỏ qua gợi ý"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#86198f",
                  cursor: "pointer",
                  fontSize: "12px",
                }}
              >
                Bỏ qua
              </button>
            </div>
          </div>
        )}
      </div>

      {/* File Attachment Simulation */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <label htmlFor="file-attachments" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
          Tệp minh chứng đính kèm (nếu có)
        </label>
        <p style={{ margin: 0, fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
          Đính kèm bản chụp CCCD, giấy gọi NVQS, hoặc văn bản liên quan (PDF, JPG, PNG tối đa 5MB).
        </p>

        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          <label
            htmlFor="file-attachments"
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius-md, 8px)",
              backgroundColor: "var(--color-slate-100, #f1f5f9)",
              border: "1px dashed var(--color-slate-300, #cbd5e1)",
              color: "var(--color-slate-700, #334155)",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span>📎</span> Chọn tệp tải lên
            <input
              id="file-attachments"
              type="file"
              multiple
              onChange={handleFileUpload}
              style={{ display: "none" }}
            />
          </label>

          {attachedFiles.map((fn, idx) => (
            <span
              key={idx}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 10px",
                borderRadius: "6px",
                backgroundColor: "var(--color-slate-100, #f1f5f9)",
                fontSize: "12px",
                color: "var(--color-slate-800, #1e293b)",
              }}
            >
              <span>{fn}</span>
              <button
                type="button"
                onClick={() => removeFile(fn)}
                aria-label={`Xóa tệp ${fn}`}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "#dc2626",
                  padding: "0 2px",
                  fontWeight: 700,
                }}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Turnaround expectation & Action Button */}
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
          <span>Xem trước yêu cầu</span>
          <ArrowRightIcon size={16} />
        </button>
      </div>
    </form>
  );
}
