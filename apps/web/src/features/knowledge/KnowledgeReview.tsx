import React from "react";
import { AlertTriangleIcon } from "../../components/Icons";

export interface KnowledgeChunk {
  id: string;
  locator: string;
  content: string;
  wordCount?: number;
  warnings?: string[];
}

export interface KnowledgeDocItem {
  id: string;
  documentRef: string;
  title: string;
  status: "draft" | "pending_review" | "published" | "archived";
  authorId: string;
  department: string;
  version: string;
  sourceUri?: string;
  contentHash?: string;
  quarantineStatus?: boolean;
  policyViolations?: string[];
  isStale?: boolean;
  effectiveFrom?: string;
  effectiveTo?: string;
  freshnessStatus?: "fresh" | "stale" | "expired";
  parseStatus?: "parsed" | "pending" | "failed";
  chunks?: KnowledgeChunk[];
  reviewEvidenceComplete?: boolean;
  warnings?: string[];
}

export interface KnowledgeReviewProps {
  document: KnowledgeDocItem;
  currentUserId: string;
  userRole?: string;
  onApprove?: (docId: string) => void;
  onReject?: (docId: string) => void;
}

export function KnowledgeReview({
  document,
  currentUserId,
  userRole,
  onApprove,
  onReject,
}: KnowledgeReviewProps) {
  const isAuthor = document.authorId === currentUserId;
  const isParseFailed = document.parseStatus === "failed";
  const isEvidenceIncomplete = document.reviewEvidenceComplete === false;

  const hasAuthority = !userRole || userRole === "ADMIN" || userRole === "KNOWLEDGE_MANAGER";
  const isStaleDoc = document.isStale === true || document.freshnessStatus === "stale" || document.freshnessStatus === "expired";
  const isQuarantined = !!document.quarantineStatus || (!!document.policyViolations && document.policyViolations.length > 0);

  const canPublish =
    document.status === "pending_review" &&
    !isAuthor &&
    !isParseFailed &&
    !isEvidenceIncomplete &&
    hasAuthority &&
    !isStaleDoc &&
    !isQuarantined;

  const chunks = document.chunks || [];
  const warnings = document.warnings || [];
  const policyViolations = document.policyViolations || [];

  return (
    <div
      role="region"
      aria-label="Phê duyệt văn bản tri thức"
      style={{
        border: "1px solid var(--color-slate-200, #e2e8f0)",
        borderRadius: "var(--radius-lg, 14px)",
        padding: "28px",
        backgroundColor: "#ffffff",
        maxWidth: "800px",
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.04))",
      }}
    >
      {/* Quarantine Banner (AC-TASK-WEB-KNOW-003-03) */}
      {isQuarantined && (
        <div
          role="alert"
          style={{
            padding: "16px 20px",
            borderRadius: "var(--radius-md, 8px)",
            backgroundColor: "#fff1f2",
            border: "2px solid #f43f5e",
            color: "#9f1239",
            fontSize: "14px",
            lineHeight: 1.5,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", fontWeight: 700, marginBottom: "6px" }}>
            <AlertTriangleIcon size={20} />
            <span>[CÁCH LY KIỂM DUYỆT] Văn bản đang trong trạng thái cách ly</span>
          </div>
          <p style={{ margin: "0 0 8px 0" }}>
            Văn bản đã bị cách ly do vi phạm chính sách an toàn thông tin hoặc có dấu hiệu mã độc / prompt injection. Quyền phê duyệt bị khóa toàn bộ.
          </p>
          {policyViolations.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: "20px" }}>
              {policyViolations.map((v, idx) => (
                <li key={idx} style={{ fontWeight: 600 }}>{v}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Header and Metadata */}
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
            backgroundColor:
              document.status === "published" ? "#ecfdf5" :
              document.status === "draft" ? "#fef2f2" :
              document.status === "archived" ? "#f1f5f9" :
              "#fffbeb",
            color:
              document.status === "published" ? "#065f46" :
              document.status === "draft" ? "#991b1b" :
              document.status === "archived" ? "#475569" :
              "#b45309",
            border: `1px solid ${
              document.status === "published" ? "#a7f3d0" :
              document.status === "draft" ? "#fecaca" :
              document.status === "archived" ? "#e2e8f0" :
              "#fde68a"
            }`,
            whiteSpace: "nowrap",
          }}
        >
          {document.status === "published" ? "✓ Đã duyệt & Ban hành" :
           document.status === "draft" ? "Yêu cầu sửa đổi" :
           document.status === "archived" ? "Lưu trữ" :
           "Chờ duyệt 4 mắt"}
        </span>
      </div>

      {/* Immutable Provenance Information (AC-TASK-WEB-KNOW-003-03) */}
      {(document.sourceUri || document.contentHash) && (
        <div
          style={{
            padding: "12px 16px",
            backgroundColor: "#f8fafc",
            borderRadius: "8px",
            border: "1px solid #cbd5e1",
            fontSize: "12px",
            color: "#334155",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          <div style={{ fontWeight: 700, color: "#0f172a" }}>Nguồn gốc xuất xứ (Provenance):</div>
          {document.sourceUri && (
            <div>Nguồn gốc: <code style={{ wordBreak: "break-all" }}>{document.sourceUri}</code></div>
          )}
          {document.contentHash && (
            <div>Mã băm nội dung: <code>{document.contentHash}</code></div>
          )}
        </div>
      )}

      {/* Parse and Freshness Status Banner */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "12px",
          padding: "12px 16px",
          backgroundColor: "var(--color-slate-50, #f8fafc)",
          borderRadius: "8px",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          fontSize: "13px",
        }}
      >
        <div>
          <span style={{ color: "var(--color-slate-500, #64748b)", fontWeight: 500 }}>Trạng thái trích xuất: </span>
          <strong>
            {document.parseStatus === "failed"
              ? "Lỗi trích xuất cú pháp"
              : document.parseStatus === "parsed"
              ? "Đã phân tích cú pháp"
              : "Chờ phân tích"}
          </strong>{" "}
          <span>({chunks.length} đoạn)</span>
        </div>

        <div>
          <span style={{ color: "var(--color-slate-500, #64748b)", fontWeight: 500 }}>Thời hạn & Độ tươi: </span>
          <strong>
            {document.effectiveFrom && document.effectiveTo
              ? `Hiệu lực: ${document.effectiveFrom} - ${document.effectiveTo}`
              : document.freshnessStatus === "fresh"
              ? "Dữ liệu mới cập nhật"
              : "Chưa xác định thời hạn"}
          </strong>
        </div>
      </div>

      {/* Stale / Changed Document Warning (AC-TASK-WEB-KNOW-003-01) */}
      {isStaleDoc && (
        <div
          role="alert"
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-md, 8px)",
            backgroundColor: "#fffbeb",
            border: "1px solid #fde68a",
            color: "#92400e",
            fontSize: "13px",
            lineHeight: 1.5,
          }}
        >
          <strong>[XUNG ĐỘT PHIÊN BẢN]</strong> Văn bản đã bị thay đổi hoặc hết hạn (Stale). Cần cập nhật phiên bản mới trước khi thẩm định.
        </div>
      )}

      {/* Authority Warning (AC-TASK-WEB-KNOW-003-02) */}
      {!hasAuthority && (
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
          }}
        >
          <strong>[KHÔNG ĐỦ THẨM QUYỀN]</strong> Không có thẩm quyền ban hành: Vai trò hiện tại của bạn không được phép phê duyệt hoặc ban hành văn bản tri thức.
        </div>
      )}

      {/* Warnings & Incomplete Review Alerts */}
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

      {isEvidenceIncomplete && (
        <div
          role="alert"
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-md, 8px)",
            backgroundColor: "#fffbeb",
            border: "1px solid #fde68a",
            color: "#92400e",
            fontSize: "13px",
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: "4px" }}>
            [CẢNH BÁO] Chưa đủ bằng chứng thẩm định
          </div>
          <p style={{ margin: "0 0 6px 0" }}>
            Tài liệu này chưa có đầy đủ bằng chứng đối chiếu hoặc kiểm định chất lượng (eval). Nút xuất bản bị khóa để bảo đảm an toàn dữ liệu.
          </p>
          {warnings.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: "20px" }}>
              {warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {isParseFailed && (
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
          }}
        >
          <div style={{ fontWeight: 700 }}>[NGHIÊM TRỌNG] Lỗi trích xuất cú pháp</div>
          <div>Không thể thẩm định hoặc xuất bản tài liệu do tệp nguồn gặp lỗi bóc tách văn bản. Vui lòng tải lên lại hoặc chỉnh sửa tệp nguồn.</div>
        </div>
      )}

      {/* Source to Chunks Hierarchy */}
      <div>
        <h3
          style={{
            margin: "0 0 12px 0",
            fontSize: "14px",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            color: "var(--color-slate-700, #334155)",
          }}
        >
          Phân đoạn văn bản & Định vị trích dẫn (Chunks & Locators)
        </h3>

        {chunks.length === 0 ? (
          <div
            style={{
              padding: "20px",
              textAlign: "center",
              backgroundColor: "var(--color-slate-50, #f8fafc)",
              borderRadius: "8px",
              border: "1px dashed var(--color-slate-300, #cbd5e1)",
              color: "var(--color-slate-500, #64748b)",
              fontSize: "13px",
            }}
          >
            Chưa có đoạn trích xuất nào được ghi nhận.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {chunks.map((chunk) => (
              <div
                key={chunk.id}
                tabIndex={0}
                style={{
                  padding: "14px 16px",
                  borderRadius: "8px",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  backgroundColor: "#ffffff",
                  fontSize: "13px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "8px",
                    flexWrap: "wrap",
                    gap: "8px",
                  }}
                >
                  <span
                    style={{
                      fontWeight: 700,
                      color: "var(--color-primary, #1e3a8a)",
                      backgroundColor: "var(--color-slate-100, #f1f5f9)",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "12px",
                    }}
                  >
                    {chunk.locator}
                  </span>
                  {chunk.wordCount !== undefined && (
                    <span style={{ fontSize: "11px", color: "var(--color-slate-400, #94a3b8)" }}>
                      {chunk.wordCount} từ
                    </span>
                  )}
                </div>

                <p
                  style={{
                    margin: 0,
                    color: "var(--color-slate-800, #1e293b)",
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {chunk.content}
                </p>

                {chunk.warnings && chunk.warnings.length > 0 && (
                  <div
                    style={{
                      marginTop: "10px",
                      padding: "6px 10px",
                      borderRadius: "4px",
                      backgroundColor: "#fffbeb",
                      border: "1px solid #fde68a",
                      fontSize: "12px",
                      color: "#92400e",
                    }}
                  >
                    <strong>[CẢNH BÁO]:</strong> {chunk.warnings.join(", ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action footer */}
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
            minHeight: "40px",
          }}
        >
          Yêu cầu sửa đổi
        </button>

        <button
          type="button"
          onClick={() => onApprove?.(document.id)}
          disabled={!canPublish}
          aria-label="Phê duyệt ban hành"
          title={
            canPublish
              ? "Phê duyệt ban hành"
              : isQuarantined
              ? "Văn bản đang trong trạng thái cách ly"
              : isStaleDoc
              ? "Văn bản đã bị thay đổi hoặc hết hạn"
              : !hasAuthority
              ? "Không có thẩm quyền ban hành"
              : isAuthor
              ? "Tác giả không thể tự phê duyệt (Quy tắc 4 mắt)"
              : isEvidenceIncomplete
              ? "Chưa đủ bằng chứng thẩm định"
              : isParseFailed
              ? "Lỗi trích xuất cú pháp"
              : "Chưa đủ điều kiện ban hành"
          }
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
            minHeight: "40px",
          }}
        >
          Phê duyệt ban hành
        </button>
      </div>
    </div>
  );
}
