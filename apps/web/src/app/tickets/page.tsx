"use client";

import React, { useEffect, useState, useCallback, type FormEvent } from "react";
import { AppShell } from "../../components/AppShell";
import { TicketList, type StudentTicket } from "../../features/tickets/TicketList";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import {
  PlusIcon,
  CheckCircle2Icon,
  XIcon,
  ArrowRightIcon,
  FileTextIcon,
  ClockIcon,
  AlertTriangleIcon,
} from "../../components/Icons";
import { ApiClient, ApiClientError } from "../../lib/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TicketApiResponse {
  items: Array<{
    id: string;
    category: string;
    priority: string;
    status: string;
    subject: string;
    description_redacted?: string;
    created_at: string;
    updated_at: string;
  }>;
}

interface TicketCreateResponse {
  id: string;
  category: string;
  priority: string;
  status: string;
  subject: string;
  description_redacted?: string;
  created_at: string;
  updated_at: string;
}

const docTitles: Record<string, string> = {
  xac_nhan_sinh_vien: "Giấy xác nhận sinh viên (mục đích chung)",
  bang_diem_tam_thoi: "Bảng điểm tạm thời (xác nhận học phần đã hoàn thành)",
  gioi_thieu_thuc_tap: "Giấy giới thiệu thực tập doanh nghiệp",
  hoan_nghia_vu_quan_su: "Giấy xác nhận tạm hoãn NVQS",
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<StudentTicket[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [createNotice, setCreateNotice] = useState<string | null>(null);

  // Form draft state (retained across errors)
  const [step, setStep] = useState<"editing" | "preview">("editing");
  const [documentType, setDocumentType] = useState("xac_nhan_sinh_vien");
  const [deliveryMethod, setDeliveryMethod] = useState("pickup");
  const [quantity, setQuantity] = useState(1);
  const [reason, setReason] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<{
    type: "no_effect" | "result_unknown";
    message: string;
  } | null>(null);

  useEffect(() => {
    if (!isModalOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isModalOpen]);

  const fetchTickets = useCallback(async () => {
    setStatus("loading");
    setErrorMessage("");

    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      const response = await client.get<TicketApiResponse>("/v1/tickets");

      const items = response.items || [];
      if (items.length === 0) {
        setTickets([]);
        setStatus("empty");
        return;
      }

      const mappedTickets: StudentTicket[] = items.map((ticketItem) => {
        let normalizedStatus: StudentTicket["status"] = "submitted";
        const statusRaw = ticketItem.status.toLowerCase();
        if (statusRaw === "in_progress") normalizedStatus = "in_progress";
        else if (statusRaw === "waiting_student") normalizedStatus = "waiting_student";
        else if (statusRaw === "resolved") normalizedStatus = "resolved";
        else if (statusRaw === "closed") normalizedStatus = "closed";

        return {
          id: ticketItem.id,
          code: `TK-${ticketItem.id.slice(0, 6).toUpperCase()}`,
          title: ticketItem.subject,
          category: ticketItem.category,
          status: normalizedStatus,
          createdAt: new Date(ticketItem.created_at).toLocaleDateString("vi-VN"),
          description: ticketItem.description_redacted || ticketItem.subject,
        };
      });

      setTickets(mappedTickets);
      setStatus("success");
    } catch (err: unknown) {
      // Fail honestly: NEVER fabricate success or fake demo tickets!
      const detail =
        err instanceof ApiClientError
          ? err.problem.detail || err.problem.title
          : "Không thể kết nối cơ sở dữ liệu phiếu hỗ trợ. Vui lòng thử lại.";
      
      setErrorMessage(detail);
      
      setTickets((prev) => {
        if (prev.length > 0) {
          setStatus("stale");
          return prev;
        } else {
          setStatus("error");
          return [];
        }
      });
    }
  }, []);

  const handleProceedToPreview = (e: FormEvent) => {
    e.preventDefault();
    const finalReason = reason.trim();
    if (!finalReason) {
      setValidationError("Vui lòng nhập mục đích xin cấp giấy tờ.");
      return;
    }
    setValidationError(null);
    setSubmitError(null);
    setStep("preview");
  };

  const handleConfirmSubmit = async () => {
    // Prevent duplicate submission during flight or when result is pending unknown reconciliation
    if (isSubmitting || submitError?.type === "result_unknown") {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    const docName = docTitles[documentType] || "giấy tờ";
    const subject = `Xin cấp ${docName} (${quantity} bản)`;

    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      
      const ticketPayload = {
        category: "DOCUMENT_REQUEST",
        subject,
        description: reason.trim(),
        priority: "normal",
      };

      const previewResponse = await client.post<any>("/v1/tickets/preview", ticketPayload);

      let response: TicketCreateResponse;
      if (previewResponse?.id) {
        response = previewResponse;
      } else {
        const confirmRes = await client.post<any>(`/v1/tickets/${previewResponse.preview_id}/confirm`, {
          confirmation_token: previewResponse.confirmation_token,
          idempotency_key: `idem-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          payload: ticketPayload,
        });
        response = {
          id: confirmRes.ticket_id || confirmRes.id || previewResponse.preview_id,
          category: "DOCUMENT_REQUEST",
          priority: "normal",
          status: confirmRes.status || "submitted",
          subject,
          description_redacted: reason.trim(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
      }

      // Authoritative response handling
      const createdTicket: StudentTicket = {
        id: response.id,
        code: `TK-${response.id.slice(0, 6).toUpperCase()}`,
        title: response.subject || subject,
        category: response.category || "Thủ tục hành chính",
        status: "submitted",
        createdAt: new Date(response.created_at || Date.now()).toLocaleDateString("vi-VN"),
        description: response.description_redacted || reason.trim(),
      };

      setTickets((prev) => [createdTicket, ...prev]);
      setIsModalOpen(false);
      setStep("editing");
      setReason("");
      setCreateNotice(`Đã gửi yêu cầu thành công! Mã yêu cầu: ${createdTicket.code}`);
      setStatus("success");
    } catch (err: unknown) {
      // Fail honestly: Never fabricate receipt! Retain form draft!
      if (err instanceof ApiClientError) {
        const isTimeoutOrNetwork =
          err.problem.code === "TIMEOUT" ||
          err.problem.status === 504 ||
          err.problem.status === 0;

        if (isTimeoutOrNetwork) {
          setSubmitError({
            type: "result_unknown",
            message:
              "Kết quả chưa xác định do mất kết nối hoặc hết thời gian chờ phản hồi. Hệ thống đang kiểm tra trạng thái yêu cầu, vui lòng không gửi lại để tránh trùng lặp.",
          });
        } else {
          setSubmitError({
            type: "no_effect",
            message:
              err.problem.detail ||
              "Gửi yêu cầu thất bại. Dữ liệu chưa được ghi nhận trên máy chủ.",
          });
        }
      } else {
        setSubmitError({
          type: "no_effect",
          message: "Gửi yêu cầu thất bại do lỗi không xác định.",
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  return (
    <AppShell activeNav="tickets">
      <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "8px 0" }}>
        <header
          style={{
            marginBottom: "24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div>
            <h1
              style={{
                fontSize: "24px",
                fontWeight: 800,
                margin: "0 0 6px 0",
                color: "var(--color-slate-900, #0f172a)",
              }}
            >
              Yêu cầu hỗ trợ sinh viên
            </h1>
            <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
              Theo dõi và quản lý các yêu cầu xử lý học vụ và thủ tục hành chính
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              setIsModalOpen(true);
              setSubmitError(null);
            }}
            style={{
              padding: "10px 20px",
              borderRadius: "var(--radius-md, 8px)",
              border: "none",
              backgroundColor: "var(--color-primary, #1e3a8a)",
              color: "#ffffff",
              fontSize: "14px",
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "var(--shadow-sm)",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "var(--transition-fast, 150ms ease)",
            }}
          >
            <PlusIcon size={16} />
            <span>Tạo yêu cầu mới</span>
          </button>
        </header>

        {createNotice && (
          <div
            role="status"
            style={{
              padding: "12px 18px",
              borderRadius: "var(--radius-md, 8px)",
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
              color: "#15803d",
              marginBottom: "20px",
              fontSize: "13px",
              fontWeight: 600,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckCircle2Icon size={18} />
              <span>{createNotice}</span>
            </div>
            <button
              type="button"
              onClick={() => setCreateNotice(null)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "#15803d",
                padding: "4px",
                display: "flex",
                alignItems: "center",
              }}
              aria-label="Đóng thông báo"
            >
              <XIcon size={14} />
            </button>
          </div>
        )}

        <AsyncState
          status={status}
          loadingMessage="Đang tải danh sách phiếu hỗ trợ..."
          emptyMessage="Bạn chưa tạo phiếu hỗ trợ nào."
          errorMessage={errorMessage}
          onRetry={fetchTickets}
        >
          <TicketList tickets={tickets} />
        </AsyncState>

        {/* Modal Đăng ký Giấy tờ Sinh viên với Fail Honestly Architecture */}
        {isModalOpen && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="request-form-title"
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
                maxWidth: "600px",
                width: "100%",
                padding: "24px",
                boxShadow: "var(--shadow-modal, 0 20px 25px -5px rgba(0, 0, 0, 0.1))",
                position: "relative",
                maxHeight: "90vh",
                overflowY: "auto",
              }}
            >
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                aria-label="Đóng"
                style={{
                  position: "absolute",
                  top: "16px",
                  right: "16px",
                  border: "none",
                  backgroundColor: "var(--color-slate-100, #f1f5f9)",
                  borderRadius: "50%",
                  width: "36px",
                  height: "36px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--color-slate-600, #475569)",
                }}
              >
                <XIcon size={18} />
              </button>

              <h2
                id="request-form-title"
                style={{
                  margin: "0 0 16px 0",
                  fontSize: "18px",
                  fontWeight: 700,
                  color: "var(--color-slate-900, #0f172a)",
                }}
              >
                Tạo yêu cầu cấp giấy tờ hành chính
              </h2>

              {/* Submit Error Presentation: Distinguish No-Effect from Result-Unknown */}
              {submitError && (
                <div
                  role="alert"
                  style={{
                    padding: "12px 16px",
                    borderRadius: "8px",
                    backgroundColor: submitError.type === "result_unknown" ? "#fffbeb" : "#fef2f2",
                    border: `1px solid ${submitError.type === "result_unknown" ? "#fde68a" : "#fecaca"}`,
                    color: submitError.type === "result_unknown" ? "#92400e" : "#991b1b",
                    marginBottom: "16px",
                    fontSize: "13px",
                    lineHeight: 1.5,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: 700, marginBottom: "4px" }}>
                    <AlertTriangleIcon size={16} />
                    <span>
                      {submitError.type === "result_unknown"
                        ? "[?] Kết quả chưa xác định"
                        : "[!] Gửi yêu cầu thất bại (Chưa ghi nhận)"}
                    </span>
                  </div>
                  <div>{submitError.message}</div>
                </div>
              )}

              {/* Form Step: Editing vs Preview */}
              {step === "editing" ? (
                <form onSubmit={handleProceedToPreview} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                  {validationError && (
                    <div
                      role="alert"
                      style={{
                        padding: "10px 14px",
                        borderRadius: "8px",
                        backgroundColor: "#fef2f2",
                        border: "1px solid #fecaca",
                        color: "#991b1b",
                        fontSize: "13px",
                      }}
                    >
                      {validationError}
                    </div>
                  )}

                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label htmlFor="doc-type" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                      Loại giấy tờ <span style={{ color: "#dc2626" }}>*</span>
                    </label>
                    <select
                      id="doc-type"
                      value={documentType}
                      onChange={(e) => setDocumentType(e.target.value)}
                      style={{
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1.5px solid var(--color-slate-300, #cbd5e1)",
                        fontSize: "14px",
                        minHeight: "44px",
                      }}
                    >
                      <option value="xac_nhan_sinh_vien">Giấy xác nhận sinh viên (mục đích chung)</option>
                      <option value="bang_diem_tam_thoi">Bảng điểm tạm thời (xác nhận học phần đã hoàn thành)</option>
                      <option value="gioi_thieu_thuc_tap">Giấy giới thiệu thực tập doanh nghiệp</option>
                      <option value="hoan_nghia_vu_quan_su">Giấy xác nhận tạm hoãn NVQS</option>
                    </select>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label htmlFor="delivery-method" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                      Phương thức nhận kết quả <span style={{ color: "#dc2626" }}>*</span>
                    </label>
                    <select
                      id="delivery-method"
                      value={deliveryMethod}
                      onChange={(e) => setDeliveryMethod(e.target.value)}
                      style={{
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1.5px solid var(--color-slate-300, #cbd5e1)",
                        fontSize: "14px",
                        minHeight: "44px",
                      }}
                    >
                      <option value="pickup">Nhận trực tiếp tại bộ phận Một cửa (Phòng 102 - Tòa H1)</option>
                      <option value="email">Bản điện tử (PDF gửi qua email sinh viên)</option>
                    </select>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label htmlFor="quantity" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                      Số lượng bản <span style={{ color: "#dc2626" }}>*</span>
                    </label>
                    <input
                      id="quantity"
                      type="number"
                      min={1}
                      max={5}
                      value={quantity}
                      onChange={(e) => setQuantity(Math.max(1, Math.min(5, Number(e.target.value))))}
                      style={{
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1.5px solid var(--color-slate-300, #cbd5e1)",
                        fontSize: "14px",
                        width: "100px",
                        minHeight: "44px",
                      }}
                    />
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label htmlFor="reason" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                      Mục đích xin cấp <span style={{ color: "#dc2626" }}>*</span>
                    </label>
                    <textarea
                      id="reason"
                      rows={3}
                      value={reason}
                      onChange={(e) => {
                        setReason(e.target.value);
                        if (validationError) setValidationError(null);
                        if (submitError) setSubmitError(null);
                      }}
                      placeholder="Ví dụ: Vay vốn sinh viên, hồ sơ xin thực tập..."
                      style={{
                        padding: "10px 14px",
                        borderRadius: "8px",
                        border: "1.5px solid var(--color-slate-300, #cbd5e1)",
                        fontSize: "14px",
                        fontFamily: "inherit",
                        lineHeight: 1.5,
                      }}
                    />
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "var(--color-slate-500, #64748b)" }}>
                      <ClockIcon size={16} />
                      <span>Xử lý: 1 - 2 ngày làm việc</span>
                    </div>

                    <button
                      type="submit"
                      style={{
                        padding: "10px 20px",
                        backgroundColor: "var(--color-primary, #1e3a8a)",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "8px",
                        fontWeight: 600,
                        fontSize: "14px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        minHeight: "44px",
                      }}
                    >
                      <span>Xem trước yêu cầu</span>
                      <ArrowRightIcon size={16} />
                    </button>
                  </div>
                </form>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                  <dl
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "12px",
                      backgroundColor: "var(--color-slate-50, #f8fafc)",
                      padding: "16px",
                      borderRadius: "8px",
                      border: "1px solid var(--color-slate-200, #e2e8f0)",
                      margin: 0,
                      fontSize: "13px",
                    }}
                  >
                    <div>
                      <dt style={{ color: "var(--color-slate-500, #64748b)", fontWeight: 600, textTransform: "uppercase", fontSize: "11px" }}>Loại giấy tờ</dt>
                      <dd style={{ margin: "2px 0 0 0", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>{docTitles[documentType] || documentType}</dd>
                    </div>

                    <div>
                      <dt style={{ color: "var(--color-slate-500, #64748b)", fontWeight: 600, textTransform: "uppercase", fontSize: "11px" }}>Phương thức nhận</dt>
                      <dd style={{ margin: "2px 0 0 0" }}>{deliveryMethod === "pickup" ? "Nhận trực tiếp tại Một cửa (Phòng 102 - Tòa H1)" : "Bản điện tử (PDF)"}</dd>
                    </div>

                    <div>
                      <dt style={{ color: "var(--color-slate-500, #64748b)", fontWeight: 600, textTransform: "uppercase", fontSize: "11px" }}>Số lượng</dt>
                      <dd style={{ margin: "2px 0 0 0" }}>{quantity} bản</dd>
                    </div>

                    <div>
                      <dt style={{ color: "var(--color-slate-500, #64748b)", fontWeight: 600, textTransform: "uppercase", fontSize: "11px" }}>Mục đích xin cấp</dt>
                      <dd style={{ margin: "2px 0 0 0", fontWeight: 500, color: "var(--color-slate-800, #1e293b)" }}>{reason}</dd>
                    </div>
                  </dl>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={() => {
                        setStep("editing");
                        setSubmitError(null);
                      }}
                      disabled={isSubmitting}
                      style={{
                        padding: "10px 18px",
                        backgroundColor: "#ffffff",
                        border: "1px solid var(--color-slate-300, #cbd5e1)",
                        borderRadius: "8px",
                        color: "var(--color-slate-700, #334155)",
                        fontWeight: 600,
                        fontSize: "13px",
                        cursor: isSubmitting ? "not-allowed" : "pointer",
                        minHeight: "44px",
                      }}
                    >
                      Quay lại chỉnh sửa
                    </button>

                    <button
                      type="button"
                      onClick={handleConfirmSubmit}
                      disabled={isSubmitting || submitError?.type === "result_unknown"}
                      style={{
                        padding: "10px 24px",
                        backgroundColor:
                          isSubmitting || submitError?.type === "result_unknown"
                            ? "var(--color-slate-300, #cbd5e1)"
                            : "var(--color-primary, #1e3a8a)",
                        color:
                          isSubmitting || submitError?.type === "result_unknown"
                            ? "var(--color-slate-500, #64748b)"
                            : "#ffffff",
                        border: "none",
                        borderRadius: "8px",
                        fontWeight: 600,
                        fontSize: "14px",
                        cursor:
                          isSubmitting || submitError?.type === "result_unknown"
                            ? "not-allowed"
                            : "pointer",
                        minHeight: "44px",
                      }}
                    >
                      {isSubmitting ? "Đang gửi..." : "Gửi yêu cầu"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
