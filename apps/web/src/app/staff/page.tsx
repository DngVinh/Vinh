"use client";

import React, { useEffect, useState, useCallback } from "react";
import { AppShell } from "../../components/AppShell";
import {
  StaffTicketQueue,
  type StaffQueueItem,
} from "../../features/staff/StaffTicketQueue";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import { ApiClient, ApiClientError } from "../../lib/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface HandoverItemResponse {
  handover_id: string;
  conversation_id: string;
  requester_user_id: string;
  queue_key: string;
  reason_code: string;
  risk_level: string;
  status: string;
  summary_redacted?: string;
  created_at: string;
  assigned_user_id?: string;
}

interface HandoverListResponse {
  items: HandoverItemResponse[];
}

const DEFAULT_DEMO_QUEUE: StaffQueueItem[] = [
  {
    id: "ho-01",
    ticketCode: "HO-019234",
    studentName: "Nguyễn Văn An",
    studentId: "SV240001",
    title: "Tư vấn thủ tục bảo lưu kết quả học tập kỳ 1",
    publicContent: "Em cần làm đơn bảo lưu kết quả học tập học kỳ 1 năm học 2026-2027 do hoàn cảnh gia đình. Em đã có bản scan đơn viết tay và xác nhận của chính quyền địa phương đính kèm.",
    internalNotes: "AI Triage: Đã đối chiếu Quy chế Đào tạo ĐHXDHN Điều 15. Sinh viên năm thứ 2, điểm TB tích lũy 2.85, đủ điều kiện xem xét bảo lưu không quá 2 học kỳ liên tiếp. Cần kiểm tra dấu đỏ xác nhận địa phương.",
    status: "unassigned",
    priority: "urgent",
    createdAt: "Hôm nay, 08:30",
    age: "25 phút",
    targetDepartment: "Phòng Quản lý Đào tạo",
    attachments: [
      { name: "don_xin_bao_luu_hoc_tap.pdf", ocrBadge: "Dấu đỏ tròn hợp lệ", confidence: "98.5%", type: "pdf" },
      { name: "xac_nhan_chinh_quyen_dia_phuong.jpg", ocrBadge: "Chữ ký chủ tịch phường", confidence: "97.0%", type: "image" },
    ],
  },
  {
    id: "ho-02",
    ticketCode: "HO-019235",
    studentName: "Trần Thị Bình",
    studentId: "SV240002",
    title: "Khiếu nại sai lệch điểm thi học kỳ 2 môn Sức bền vật liệu",
    publicContent: "Điểm thi trên hệ thống portal hiển thị 4.5 trong khi bài thi đã được thầy trưởng bộ môn công bố là 7.0. Nhờ các thầy cô phòng đào tạo kiểm tra lại bài thi túi số 14.",
    internalNotes: "AI Triage: Mức độ ưu tiên cao. Cần liên hệ Bộ môn Cơ học kết cấu đối chiếu bảng điểm gốc chữ ký giảng viên trước khi cập nhật trên cơ sở dữ liệu đào tạo.",
    status: "in_progress",
    assignedStaffId: "staff-support-huce-01",
    priority: "high",
    createdAt: "Hôm nay, 09:15",
    age: "1 giờ",
    targetDepartment: "Phòng Quản lý Đào tạo",
    attachments: [
      { name: "anh_chup_bang_diem_lop_hoc_phan.jpg", ocrBadge: "Khớp chữ ký giảng viên", confidence: "96.4%", type: "image" },
    ],
  },
  {
    id: "ho-03",
    ticketCode: "HO-019236",
    studentName: "Lê Hoàng Nam",
    studentId: "SV240003",
    title: "Cấp giấy xác nhận tạm hoãn nghĩa vụ quân sự đợt 2",
    publicContent: "Địa phương BCH Quân sự quận Đống Đa yêu cầu nộp giấy xác nhận còn đang học tập trước ngày 30/09 để hoàn thiện hồ sơ tạm hoãn nghĩa vụ quân sự năm 2026.",
    internalNotes: "AI Triage: Hồ sơ Một cửa trực tuyến chuẩn. Đã tự động đối chiếu cơ sở dữ liệu VNeID và trạng thái sinh viên chính quy chưa tốt nghiệp. Có thể cấp ngay.",
    status: "unassigned",
    priority: "normal",
    createdAt: "Hôm nay, 10:05",
    age: "10 phút",
    targetDepartment: "Phòng Công tác sinh viên",
    attachments: [
      { name: "lenh_goi_kham_nvqs_dong_da.pdf", ocrBadge: "Dấu đỏ BCH Quân sự", confidence: "99.1%", type: "pdf" },
      { name: "ban_chup_cccd_2_mat.jpg", ocrBadge: "VNeID Mức 2 khớp MSSV", confidence: "99.8%", type: "image" },
    ],
  },
  {
    id: "ho-04",
    ticketCode: "HO-019237",
    studentName: "Phạm Minh Đức",
    studentId: "SV240004",
    title: "Xin miễn giảm học phí diện con thương binh bệnh binh",
    publicContent: "Em xin nộp bản sao chứng thực thẻ thương binh của phụ huynh và giấy đề nghị miễn giảm học phí theo Nghị định 81/2021/NĐ-CP.",
    internalNotes: "AI Triage: Đã rà soát bảo vệ dữ liệu cá nhân theo Nghị định 13/2023. Hồ sơ hợp lệ, đề xuất chuyển Phòng Kế hoạch - Tài chính sau khi Một cửa nghiệm thu checklist.",
    status: "unassigned",
    priority: "high",
    createdAt: "Hôm nay, 10:45",
    age: "5 phút",
    targetDepartment: "Phòng CTSV & KHTC",
    attachments: [
      { name: "ban_sao_the_thuong_binh_hang_2.pdf", ocrBadge: "Chứng thực UBND phường", confidence: "97.8%", type: "pdf" },
    ],
  },
];

export default function StaffPage() {
  const [items, setItems] = useState<StaffQueueItem[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [notification, setNotification] = useState<string | null>(null);
  const currentStaffId = "staff-support-huce-01";

  const showToast = (message: string) => {
    setNotification(message);
    setTimeout(() => {
      setNotification((curr) => (curr === message ? null : curr));
    }, 4000);
  };

  const fetchStaffQueue = useCallback(async () => {
    setStatus("loading");
    setErrorMessage("");

    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      const response = await client.get<HandoverListResponse>("/v1/staff/handovers");

      const rawItems = response.items || [];
      if (rawItems.length === 0) {
        setItems([]);
        setStatus("empty");
        return;
      }

      const mapped: StaffQueueItem[] = rawItems.map((h: HandoverItemResponse) => {
        let st: StaffQueueItem["status"] = "unassigned";
        if (h.assigned_user_id) st = "assigned";
        if (h.status.toLowerCase() === "resolved") st = "resolved";

        let pri: StaffQueueItem["priority"] = "normal";
        if (h.risk_level === "CRITICAL") pri = "urgent";
        else if (h.risk_level === "HIGH") pri = "high";

        return {
          id: h.handover_id,
          ticketCode: `HO-${h.handover_id.slice(0, 6).toUpperCase()}`,
          studentName: "Sinh viên HUCE",
          studentId: h.requester_user_id.slice(0, 8),
          title: h.summary_redacted || h.reason_code,
          publicContent: h.summary_redacted || `Yêu cầu hỗ trợ sinh viên: ${h.reason_code}`,
          internalNotes: `Chuyển giao từ hệ thống tư vấn AI. Mã hàng đợi: ${h.queue_key}`,
          status: st,
          assignedStaffId: h.assigned_user_id,
          priority: pri,
          createdAt: new Date(h.created_at).toLocaleDateString("vi-VN"),
        };
      });

      setItems(mapped);
      setStatus("success");
    } catch (err: unknown) {
      // Fail honestly: NEVER fabricate demo tickets!
      const detail =
        err instanceof ApiClientError
          ? err.problem.detail || err.problem.title
          : "Không thể tải danh sách hàng đợi. Vui lòng thử lại.";
      
      setErrorMessage(detail);
      setItems((prev) => {
        if (prev.length > 0) {
          setStatus("stale");
          return prev;
        }
        setStatus("error");
        return [];
      });
    }
  }, []);

  const handleClaimTicket = useCallback((ticketId: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === ticketId
          ? { ...item, status: "assigned", assignedStaffId: currentStaffId }
          : item
      )
    );
    showToast(`Đã nhận xử lý hồ sơ ${ticketId} thành công.`);
  }, []);

  const handleTransferTicket = useCallback((ticketId: string, payload: { targetDepartment: string; transferReason?: string }) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === ticketId
          ? {
              ...item,
              targetDepartment: payload.targetDepartment,
              internalNotes: `${item.internalNotes || ""}\n[Chuyển đơn vị]: Chuyển sang ${payload.targetDepartment}. Lý do: ${payload.transferReason || "Theo thẩm quyền nghiệp vụ"}`,
            }
          : item
      )
    );
    showToast(`Đã chuyển ca ${ticketId} sang ${payload.targetDepartment}.`);
  }, []);

  const handleRequestSupplement = useCallback((ticketId: string, payload: { requestMessage: string }) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === ticketId
          ? {
              ...item,
              internalNotes: `${item.internalNotes || ""}\n[Yêu cầu bổ sung]: ${payload.requestMessage}`,
            }
          : item
      )
    );
    showToast(`Đã gửi thông báo yêu cầu sinh viên bổ sung hồ sơ cho ca ${ticketId}.`);
  }, []);

  const handleFinalizeIntake = useCallback((ticketId: string, payload: { checklistPassed: boolean; exceptionReason?: string }) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === ticketId
          ? {
              ...item,
              status: "in_progress",
              internalNotes: `${item.internalNotes || ""}\n[Checklist đã thẩm định]: Đã nghiệm thu tiếp nhận một cửa lúc ${new Date().toLocaleTimeString("vi-VN")}.${payload.exceptionReason ? ` Ngoại lệ: ${payload.exceptionReason}` : ""}`,
            }
          : item
      )
    );
    showToast(`Đã hoàn tất quy trình tiếp nhận và thẩm định checklist cho hồ sơ ${ticketId}!`);
  }, []);

  useEffect(() => {
    fetchStaffQueue();
  }, [fetchStaffQueue]);

  const unassignedCount = items.filter((i) => i.status === "unassigned").length;
  const urgentCount = items.filter((i) => i.priority === "urgent").length;

  return (
    <AppShell activeNav="staff">
      <div style={{ maxWidth: "1150px", margin: "0 auto", padding: "8px 0" }}>
        {/* Dynamic Toast Feedback */}
        {notification && (
          <div
            role="status"
            aria-live="polite"
            style={{
              marginBottom: "16px",
              padding: "12px 18px",
              borderRadius: "8px",
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
              color: "#166534",
              fontSize: "14px",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
            }}
          >
            <span>✓</span>
            <span>{notification}</span>
          </div>
        )}

        <header style={{ marginBottom: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <h1 style={{ fontSize: "24px", fontWeight: 800, margin: "0 0 6px 0", color: "var(--color-slate-900, #0f172a)" }}>
                Hàng đợi tiếp nhận hỗ trợ cán bộ (HITL)
              </h1>
              <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
                Cơ chế Một cửa số kết hợp Trí tuệ nhân tạo (AI Copilot) & Bộ thẩm định Checklist 6 cổng ISO
              </p>
            </div>

            {/* Quick KPI Counters */}
            <div style={{ display: "flex", gap: "10px" }}>
              <div
                style={{
                  backgroundColor: "#ffffff",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  borderRadius: "8px",
                  padding: "8px 14px",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "11px", color: "var(--color-slate-500, #64748b)", textTransform: "uppercase", fontWeight: 700 }}>
                  Chờ tiếp nhận
                </div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: unassignedCount > 0 ? "#2563eb" : "#16a34a" }}>
                  {unassignedCount}
                </div>
              </div>

              <div
                style={{
                  backgroundColor: "#ffffff",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  borderRadius: "8px",
                  padding: "8px 14px",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "11px", color: "var(--color-slate-500, #64748b)", textTransform: "uppercase", fontWeight: 700 }}>
                  Khẩn cấp (SLA &lt; 24h)
                </div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: urgentCount > 0 ? "#dc2626" : "#64748b" }}>
                  {urgentCount}
                </div>
              </div>
            </div>
          </div>
        </header>

        <AsyncState
          status={status}
          loadingMessage="Đang tải hàng đợi chuyển giao..."
          emptyMessage="Không có yêu cầu hỗ trợ nào đang chờ tiếp nhận."
          errorMessage={errorMessage}
          onRetry={fetchStaffQueue}
        >
          <StaffTicketQueue
            items={items}
            currentStaffId={currentStaffId}
            userRole="STAFF"
            onClaimTicket={handleClaimTicket}
            onTransferTicket={handleTransferTicket}
            onRequestSupplement={handleRequestSupplement}
            onFinalizeIntake={handleFinalizeIntake}
            onRefresh={fetchStaffQueue}
          />
        </AsyncState>
      </div>
    </AppShell>
  );
}
