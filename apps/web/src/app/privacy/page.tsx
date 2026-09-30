"use client";

import React, { useEffect, useState, useCallback } from "react";
import { AppShell } from "../../components/AppShell";
import {
  PrivacyCenter,
  type PrivacyNoticeData,
  type PrivacyRequestStatus,
} from "../../features/privacy/PrivacyCenter";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import { ApiClient } from "../../lib/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PrivacyNoticeResponse {
  notice_id: string;
  version: string;
  effective_at: string;
  status: string;
  purposes?: string[];
}

export default function PrivacyPage() {
  const [notice, setNotice] = useState<PrivacyNoticeData>({
    version: "1.0.0",
    effectiveDate: "01/10/2026",
    purpose: "Xử lý dữ liệu sinh viên phục vụ hỗ trợ đào tạo và dịch vụ Campus 24/7",
    hasConsented: false,
  });
  const [requests, setRequests] = useState<PrivacyRequestStatus[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const fetchPrivacyData = useCallback(async () => {
    setStatus("loading");
    setErrorMessage("");

    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      const response = await client.get<PrivacyNoticeResponse>("/v1/privacy/notice");

      if (response) {
        const d = response;
        setNotice((prev) => ({
          ...prev,
          version: d.version || "1.0.0",
          effectiveDate: d.effective_at
            ? new Date(d.effective_at).toLocaleDateString("vi-VN")
            : "01/10/2026",
          purpose:
            d.purposes?.join(", ") ||
            "Xử lý dữ liệu sinh viên phục vụ hỗ trợ đào tạo và dịch vụ Campus 24/7",
        }));
      }

      // Sample privacy requests for synthetic demo
      setRequests([
        {
          requestId: "req-001",
          requestType: "EXPORT_DATA",
          status: "completed",
          submittedAt: "20/09/2026",
        },
      ]);

      setStatus("success");
    } catch {
      // Demo fallback when API server is in offline simulation mode
      setNotice({
        version: "v2.1-2026",
        effectiveDate: "01/09/2026",
        purpose: "Xử lý dữ liệu sinh viên phục vụ hỗ trợ đào tạo, thủ tục một cửa số và nâng cao chất lượng dịch vụ Campus 24/7 theo Nghị định 13/2023/NĐ-CP",
        hasConsented: false,
      });
      setRequests([
        {
          requestId: "REQ-DATA-0192",
          requestType: "EXPORT_DATA",
          status: "completed",
          submittedAt: "20/09/2026",
        },
      ]);
      setStatus("success");
    }
  }, []);

  const handleConsentChange = useCallback(
    async (consented: boolean) => {
      setNotice((prev) => ({ ...prev, hasConsented: consented }));

      try {
        const client = new ApiClient({ baseUrl: API_BASE_URL });
        await client.post("/v1/privacy/consents", {
          purpose: "QUALITY_FEEDBACK",
          decision: consented ? "GRANTED" : "WITHDRAWN",
          notice_version: notice.version,
        });
      } catch {
        // Optimistic UI state maintained for demo mode
      }
    },
    [notice.version]
  );

  const handleRequestErasure = useCallback(async () => {
    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      await client.post("/v1/privacy/requests", { request_type: "DELETE_DATA" });
    } catch {
      // In demo mode, append a new request locally
    }
    setRequests((prev) => [
      {
        requestId: `REQ-DEL-${Date.now().toString().slice(-4)}`,
        requestType: "DELETE_DATA",
        status: "processing",
        submittedAt: new Date().toLocaleDateString("vi-VN"),
      },
      ...prev,
    ]);
  }, []);

  useEffect(() => {
    fetchPrivacyData();
  }, [fetchPrivacyData]);

  return (
    <AppShell activeNav="privacy">
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "8px 0" }}>
        <header style={{ marginBottom: "24px" }}>
          <h1 style={{ fontSize: "24px", fontWeight: 800, margin: "0 0 6px 0", color: "var(--color-slate-900, #0f172a)" }}>
            Trung tâm quyền riêng tư & Dữ liệu
          </h1>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
            Minh bạch về mục đích thu thập, chính sách lưu trữ và quyền quản lý dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP
          </p>
        </header>

        <AsyncState
          status={status}
          loadingMessage="Đang tải chính sách quyền riêng tư..."
          errorMessage={errorMessage}
          onRetry={fetchPrivacyData}
        >
          <PrivacyCenter
            notice={notice}
            requests={requests}
            onConsentChange={handleConsentChange}
            onRequestErasure={handleRequestErasure}
          />
        </AsyncState>
      </div>
    </AppShell>
  );
}
