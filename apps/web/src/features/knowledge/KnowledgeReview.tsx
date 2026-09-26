import React from "react";
import { AlertTriangleIcon } from "../../components/Icons";

export interface KnowledgeDocItem {
  id: string;
  documentRef: string;
  title: string;
  status: "draft" | "pending_review" | "published" | "archived";
  authorId: string;
  department: string;
  version: string;
}

export interface KnowledgeReviewProps {
  document: KnowledgeDocItem;
  currentUserId: string;
  onApprove?: (docId: string) => void;
  onReject?: (docId: string) => void;
}

export function KnowledgeReview({
  document,
  currentUserId,
  onApprove,
  onReject,
}: KnowledgeReviewProps) {
  const isAuthor = document.authorId === currentUserId;
  const canPublish = document.status === "pending_review" && !isAuthor;

  return (
    <div
      role="region"
      aria-label="Phê duyệt văn bản tri thức"
      style={{
        border: "1px solid var(--color-slate-200, #e2e8f0)",
        borderRadius: "var(--radius-lg, 14px)",
        padding: "28px",
        backgroundColor: "#ffffff",
        maxWidth: "760px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.04))",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <span
              style={{
                fontSize: "12px",
                color: "var(--color-primary, #1e3a8a)",
                fontWeight: 700,
                backgroundColor: "var(--color-primary-light, #eff6ff)",
                padding: "2px 8px",
                borderRadius: "4px",
              }}
            >
              {document.documentRef}
            </span>
            <span style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
              Phiên bản: v{document.version}
            </span>
          </div>

          <h2 style={{ margin: "0 0 6px 0", fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
            {document.title}
          </h2>

          <div style={{ fontSize: "13px", color: "var(--color-slate-500, #64748b)" }}>
            Đơn vị ban hành: <strong>{document.department}</strong> • Người soạn thảo: <code>{document.authorId}</code>
          </div>
        </div>

        <span
          style={{
            padding: "4px 10px",
            borderRadius: "9999px",
            fontSize: "12px",
            fontWeight: 600,
            backgroundColor: "#fffbeb",
            color: "#b45309",
            border: "1px solid #fde68a",
            whiteSpace: "nowrap",
          }}
        >
          Chờ duyệt 4 mắt
        </span>
      </div>

      {isAuthor && (
        <div
          role="alert"
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-md, 8px)",
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#991b1b",
            fontSize: "13px",
            lineHeight: 1.5,
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <div style={{ flexShrink: 0 }}>
            <AlertTriangleIcon size={18} />
          </div>
          <span>Quy tắc 4 mắt: Tác giả không thể tự phê duyệt tài liệu do chính mình soạn thảo. Cần một cán bộ khác thẩm định và ban hành.</span>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "8px" }}>
        <button
          type="button"
          onClick={() => onReject?.(document.id)}
          style={{
            padding: "9px 18px",
            borderRadius: "var(--radius-sm, 6px)",
            border: "1px solid var(--color-slate-300, #cbd5e1)",
            backgroundColor: "#ffffff",
            fontWeight: 600,
            fontSize: "13px",
            color: "var(--color-slate-700, #334155)",
            cursor: "pointer",
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          Yêu cầu sửa đổi
        </button>

        <button
          type="button"
          onClick={() => onApprove?.(document.id)}
          disabled={!canPublish}
          style={{
            padding: "9px 22px",
            borderRadius: "var(--radius-sm, 6px)",
            border: "none",
            backgroundColor: canPublish ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-200, #e2e8f0)",
            color: canPublish ? "#ffffff" : "var(--color-slate-500, #64748b)",
            fontWeight: 600,
            fontSize: "13px",
            cursor: canPublish ? "pointer" : "not-allowed",
            boxShadow: canPublish ? "var(--shadow-xs)" : "none",
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          Phê duyệt ban hành
        </button>
      </div>
    </div>
  );
}
