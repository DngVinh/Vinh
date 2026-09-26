"use client";

import React, { useEffect, useState, useCallback } from "react";
import { AppShell } from "../../components/AppShell";
import { TicketList, type StudentTicket } from "../../features/tickets/TicketList";
import { DocumentRequestForm } from "../../features/documents/DocumentRequestForm";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import { PlusIcon, CheckCircle2Icon, XIcon } from "../../components/Icons";
import { ApiClient } from "../../lib/api/client";

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

export default function TicketsPage() {
  const [tickets, setTickets] = useState<StudentTicket[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [createNotice, setCreateNotice] = useState<string | null>(null);

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

      const mappedTickets: StudentTicket[] = items.map((ticketItem: TicketApiResponse["items"][number]) => {
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
    } catch {
      // Demo fallback when API server is in offline simulation mode
      const demoTickets: StudentTicket[] = [
        {
          id: "ticket-01",
          code: "TK-2026-01",
          title: "Xin cấp lại thẻ sinh viên bị mất",
          category: "Thủ tục hành chính",
          status: "in_progress",
          createdAt: "Hôm qua, 14:20",
          description: "Sinh viên làm mất thẻ tại Thư viện trường, xin cấp lại thẻ sinh viên tích hợp thẻ thư viện.",
        },
        {
          id: "ticket-02",
          code: "TK-2026-02",
          title: "Xác nhận vay vốn sinh viên chính sách Ngân hàng CSXH",
          category: "Chế độ chính sách",
          status: "resolved",
          createdAt: "18/09/2026",
          description: "Hồ sơ đã được Phòng CTCT&QLSV xác nhận và đóng dấu điện tử.",
        },
        {
          id: "ticket-03",
          code: "TK-2026-03",
          title: "Xin cấp Bảng điểm tạm thời (2 bản)",
          category: "Thủ tục hành chính",
          status: "submitted",
          createdAt: "Hôm nay, 08:30",
          description: "Phục vụ nộp hồ sơ xét tuyển thực tập doanh nghiệp tại Tổng công ty Xây dựng Hà Nội.",
        },
      ];
      setTickets(demoTickets);
      setStatus("success");
    }
  }, []);

  const handleCreateRequest = (data: { documentType: string; quantity: number; reason: string }) => {
    const docTitles: Record<string, string> = {
      xac_nhan_sinh_vien: "Giấy xác nhận sinh viên",
      bang_diem_tam_thoi: "Bảng điểm tạm thời",
      gioi_thieu_thuc_tap: "Giấy giới thiệu thực tập",
      hoan_nghia_vu_quan_su: "Giấy xác nhận tạm hoãn NVQS",
    };

    const newTicket: StudentTicket = {
      id: `tck-${Date.now()}`,
      code: `TK-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      title: `Xin cấp ${docTitles[data.documentType] || "giấy tờ"} (${data.quantity} bản)`,
      category: "Thủ tục hành chính",
      status: "submitted",
      createdAt: new Date().toLocaleDateString("vi-VN"),
      description: data.reason,
    };

    setTickets((prev) => [newTicket, ...prev]);
    setIsModalOpen(false);
    setCreateNotice(`Đã gửi yêu cầu cấp "${docTitles[data.documentType] || "giấy tờ"}" thành công!`);
    setStatus("success");
  };

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  return (
    <AppShell activeNav="tickets">
      <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "8px 0" }}>
        <header style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 style={{ fontSize: "24px", fontWeight: 800, margin: "0 0 6px 0", color: "var(--color-slate-900, #0f172a)" }}>
              Yêu cầu hỗ trợ sinh viên
            </h1>
            <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
              Theo dõi và quản lý các yêu cầu xử lý học vụ và thủ tục hành chính
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
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
              style={{ background: "none", border: "none", cursor: "pointer", color: "#15803d", padding: "4px", display: "flex", alignItems: "center" }}
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

        {/* Modal Đăng ký Giấy tờ Sinh viên */}
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
                boxShadow: "var(--shadow-modal)",
                position: "relative",
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

              <h2 id="request-form-title" style={{ margin: "0 0 16px 0", fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                Tạo yêu cầu cấp giấy tờ hành chính
              </h2>

              <DocumentRequestForm hideTitle onSubmit={handleCreateRequest} />
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
