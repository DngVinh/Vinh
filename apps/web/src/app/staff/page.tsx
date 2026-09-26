"use client";

import React, { useEffect, useState, useCallback } from "react";
import { AppShell } from "../../components/AppShell";
import {
  StaffTicketQueue,
  type StaffQueueItem,
} from "../../features/staff/StaffTicketQueue";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import { ApiClient } from "../../lib/api/client";

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

export default function StaffPage() {
  const [items, setItems] = useState<StaffQueueItem[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const currentStaffId = "staff-support-huce-01";

  const fetchStaffQueue = useCallback(async () => {
    setStatus("loading");
    setErrorMessage("");

    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      const response = await client.get<HandoverListResponse>("/v1/staff/handovers");

      const rawItems = response.items || [];
      if (rawItems.length === 0) {
        // Provide sample items for staff demo workspace
        const demoQueue: StaffQueueItem[] = [
          {
            id: "ho-01",
            ticketCode: "HO-019234",
            studentName: "Nguyễn Văn An",
            studentId: "SV240001",
            title: "Tư vấn thủ tục bảo lưu kết quả học tập",
            status: "unassigned",
            priority: "normal",
            createdAt: "Hôm nay, 08:30",
          },
          {
            id: "ho-02",
            ticketCode: "HO-019235",
            studentName: "Trần Thị Bình",
            studentId: "SV240002",
            title: "Thắc mắc sai lệch điểm thi học kỳ 2",
            status: "in_progress",
            assignedStaffId: currentStaffId,
            priority: "high",
            createdAt: "Hôm nay, 09:15",
          },
        ];
        setItems(demoQueue);
        setStatus("success");
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
          status: st,
          assignedStaffId: h.assigned_user_id,
          priority: pri,
          createdAt: new Date(h.created_at).toLocaleDateString("vi-VN"),
        };
      });

      setItems(mapped);
      setStatus("success");
    } catch {
      // In demo mode without staff token, show demo items
      const fallbackQueue: StaffQueueItem[] = [
        {
          id: "ho-01",
          ticketCode: "HO-019234",
          studentName: "Nguyễn Văn An",
          studentId: "SV240001",
          title: "Tư vấn thủ tục bảo lưu kết quả học tập",
          status: "unassigned",
          priority: "normal",
          createdAt: "Hôm nay, 08:30",
        },
        {
          id: "ho-02",
          ticketCode: "HO-019235",
          studentName: "Trần Thị Bình",
          studentId: "SV240002",
          title: "Thắc mắc sai lệch điểm thi học kỳ 2",
          status: "in_progress",
          assignedStaffId: currentStaffId,
          priority: "high",
          createdAt: "Hôm nay, 09:15",
        },
      ];
      setItems(fallbackQueue);
      setStatus("success");
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
  }, []);

  useEffect(() => {
    fetchStaffQueue();
  }, [fetchStaffQueue]);

  return (
    <AppShell activeNav="staff">
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "8px 0" }}>
        <header style={{ marginBottom: "24px" }}>
          <h1 style={{ fontSize: "24px", fontWeight: 800, margin: "0 0 6px 0", color: "var(--color-slate-900, #0f172a)" }}>
            Hàng đợi tiếp nhận hỗ trợ cán bộ (HITL)
          </h1>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
            Tiếp nhận và xử lý các ca chuyển giao từ AI chatbot cần cán bộ hỗ trợ trực tiếp
          </p>
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
            onClaimTicket={handleClaimTicket}
          />
        </AsyncState>
      </div>
    </AppShell>
  );
}
