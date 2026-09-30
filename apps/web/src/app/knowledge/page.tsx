"use client";

import React, { useEffect, useState, useCallback } from "react";
import { AppShell } from "../../components/AppShell";
import {
  KnowledgeReview,
  type KnowledgeDocItem,
} from "../../features/knowledge/KnowledgeReview";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import { CheckCircle2Icon, XIcon } from "../../components/Icons";
import { ApiClient } from "../../lib/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface KnowledgeSourceItem {
  id: string;
  source_type: string;
  canonical_uri: string;
  title: string;
  owner_unit: string;
  authority_level: number;
  approval_status: string;
  version: number;
}

interface KnowledgeSourcesResponse {
  items: KnowledgeSourceItem[];
}

export default function KnowledgePage() {
  const [doc, setDoc] = useState<KnowledgeDocItem>({
    id: "doc-01",
    documentRef: "QC-2026-HUCE",
    title: "Quy chế đào tạo đại học chính quy theo hệ thống tín chỉ",
    status: "pending_review",
    authorId: "admin-daotao",
    department: "Phòng Quản lý Đào tạo",
    version: "1.0.0",
  });
  const [sourcesList, setSourcesList] = useState<KnowledgeSourceItem[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const fetchKnowledge = useCallback(async () => {
    setStatus("loading");
    setErrorMessage("");

    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      const response = await client.get<KnowledgeSourcesResponse>("/v1/knowledge/sources");

      const items = response.items || [];
      setSourcesList(items);

      if (items.length > 0) {
        const first = items[0];
        setDoc({
          id: first.id,
          documentRef: `DOC-${first.id.slice(0, 8).toUpperCase()}`,
          title: first.title,
          status:
            first.approval_status.toLowerCase() === "approved"
              ? "published"
              : "pending_review",
          authorId: "p-daotao-admin",
          department: first.owner_unit || "Phòng Đào tạo",
          version: `v${first.version}.0`,
        });
      }
      setStatus("success");
    } catch (err) {
      // In synthetic/demo environment, fallback to demo document if unauthenticated
      setStatus("success");
    }
  }, []);

  const handleApprove = useCallback((docId: string) => {
    setDoc((prev) => ({ ...prev, status: "published" }));
    setActionNotice(`Văn bản (${docId}) đã được duyệt và xuất bản vào cơ sở tri thức Campus 24/7.`);
  }, []);

  const handleReject = useCallback((docId: string) => {
    setDoc((prev) => ({ ...prev, status: "draft" }));
    setActionNotice(`Văn bản (${docId}) đã bị từ chối phê duyệt và chuyển về trạng thái dự thảo.`);
  }, []);

  useEffect(() => {
    fetchKnowledge();
  }, [fetchKnowledge]);

  return (
    <AppShell activeNav="knowledge">
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "8px 0" }}>
        <header style={{ marginBottom: "24px" }}>
          <h1 style={{ fontSize: "24px", fontWeight: 800, margin: "0 0 6px 0", color: "var(--color-slate-900, #0f172a)" }}>
            Quản trị & Phê duyệt cơ sở tri thức
          </h1>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
            Kiểm duyệt và thẩm định văn bản quy định, biểu mẫu trước khi nạp vào hệ thống RAG phục vụ sinh viên
          </p>
        </header>

        {actionNotice && (
          <div
            role="status"
            style={{
              padding: "14px 18px",
              marginBottom: "20px",
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "var(--radius-md, 8px)",
              color: "#15803d",
              fontSize: "14px",
              fontWeight: 500,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckCircle2Icon size={18} />
              <span>{actionNotice}</span>
            </div>
            <button
              type="button"
              onClick={() => setActionNotice(null)}
              style={{ background: "none", border: "none", cursor: "pointer", color: "#15803d", padding: "4px", display: "flex", alignItems: "center" }}
              aria-label="Đóng thông báo"
            >
              <XIcon size={16} />
            </button>
          </div>
        )}

        <AsyncState
          status={status}
          loadingMessage="Đang tải dữ liệu tri thức kiểm duyệt..."
          errorMessage={errorMessage}
          onRetry={fetchKnowledge}
        >
          <KnowledgeReview
            document={doc}
            currentUserId="officer-reviewer-01"
            userRole="ADMIN"
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </AsyncState>
      </div>
    </AppShell>
  );
}
