import React, { useEffect, useRef } from "react";
import { FileTextIcon, XIcon, ShieldCheckIcon, AlertTriangleIcon, ArrowRightIcon } from "../../components/Icons";

export interface CitationItem {
  id: string;
  title: string;
  documentRef: string;
  quote: string;
  authority?: string;
  locator?: string;
  effectiveDate?: string;
  validityStatus?: "active" | "stale" | "conflicting";
  isSimulation?: boolean;
  canonicalUrl?: string;
  confidence?: number;
  isAuthorized?: boolean;
}

export interface CitationDrawerProps {
  isOpen: boolean;
  citations: CitationItem[];
  onClose: () => void;
  onReportIssue?: (citationId: string) => void;
}

export function CitationDrawer({
  isOpen,
  citations,
  onClose,
  onReportIssue,
}: CitationDrawerProps) {
  const previouslyFocusedElementRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previouslyFocusedElementRef.current = document.activeElement as HTMLElement | null;
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          onClose();
        }
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => {
        window.removeEventListener("keydown", handleKeyDown);
      };
    } else {
      if (previouslyFocusedElementRef.current && typeof previouslyFocusedElementRef.current.focus === "function") {
        previouslyFocusedElementRef.current.focus();
        previouslyFocusedElementRef.current = null;
      }
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const getValidityBadge = (status?: string) => {
    switch (status) {
      case "stale":
        return {
          text: "Văn bản cần đối chiếu",
          bg: "#fffbeb",
          color: "#92400e",
          border: "#fef3c7",
        };
      case "conflicting":
        return {
          text: "Có nội dung mâu thuẫn",
          bg: "#fff1f2",
          color: "#9f1239",
          border: "#fecdd3",
        };
      case "active":
      default:
        return {
          text: "Văn bản đang hiệu lực",
          bg: "#ecfdf5",
          color: "#065f46",
          border: "#a7f3d0",
        };
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          backgroundColor: "rgba(15, 23, 42, 0.45)",
          backdropFilter: "blur(4px)",
          zIndex: 999,
        }}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="citation-drawer-title"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "460px",
          maxWidth: "92vw",
          backgroundColor: "#ffffff",
          boxShadow: "-8px 0 32px rgba(15, 23, 42, 0.16)",
          zIndex: 1000,
          display: "flex",
          flexDirection: "column",
          padding: "24px",
          boxSizing: "border-box",
        }}
      >
        {/* Drawer Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid var(--color-slate-200, #e2e8f0)",
            paddingBottom: "16px",
            marginBottom: "16px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "var(--radius-md, 8px)",
                backgroundColor: "var(--color-primary-light, #eff6ff)",
                color: "var(--color-primary, #1e3a8a)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <FileTextIcon size={20} />
            </div>
            <div>
              <h2 id="citation-drawer-title" style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                Nguồn trích dẫn & Bằng chứng
              </h2>
              <span style={{ fontSize: "11px", color: "var(--color-slate-500, #64748b)" }}>
                Kiểm chứng căn cứ văn bản và thời hiệu
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng"
            style={{
              minHeight: "44px",
              minWidth: "44px",
              border: "none",
              backgroundColor: "var(--color-slate-100, #f1f5f9)",
              fontSize: "14px",
              color: "var(--color-slate-600, #475569)",
              cursor: "pointer",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <XIcon size={16} />
          </button>
        </div>

        {/* Citations List */}
        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
          {citations.length === 0 ? (
            <div style={{ textAlign: "center", padding: "36px 16px", color: "var(--color-slate-500, #64748b)", fontSize: "13px" }}>
              Không có nguồn trích dẫn nào cho câu trả lời này.
            </div>
          ) : (
            citations.map((cite) => {
              if (cite.isAuthorized === false) {
                return (
                  <article
                    key={cite.id}
                    style={{
                      border: "1px solid var(--color-slate-200, #e2e8f0)",
                      borderRadius: "var(--radius-lg, 12px)",
                      padding: "16px",
                      backgroundColor: "var(--color-slate-50, #f8fafc)",
                      boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04))",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                      <ShieldCheckIcon size={16} />
                      <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--color-slate-500, #64748b)" }}>
                        Tài liệu hạn chế truy cập
                      </h3>
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
                      Bạn không có quyền truy cập xem chi tiết tài liệu này.
                    </div>
                  </article>
                );
              }

              const badge = getValidityBadge(cite.validityStatus);
              return (
                <article
                  key={cite.id}
                  style={{
                    border: "1px solid var(--color-slate-200, #e2e8f0)",
                    borderRadius: "var(--radius-lg, 12px)",
                    padding: "16px",
                    backgroundColor: "var(--color-slate-50, #f8fafc)",
                    boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04))",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px", marginBottom: "8px" }}>
                    <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--color-primary, #1e3a8a)", lineHeight: 1.4 }}>
                      {cite.title}
                    </h3>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 600,
                        padding: "2px 8px",
                        borderRadius: "var(--radius-full, 9999px)",
                        backgroundColor: badge.bg,
                        color: badge.color,
                        border: `1px solid ${badge.border}`,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {badge.text}
                    </span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "12px", color: "var(--color-slate-600, #475569)", marginBottom: "10px" }}>
                    <div>
                      Mã văn bản: <strong style={{ color: "var(--color-slate-800, #1e293b)" }}>{cite.documentRef}</strong>
                    </div>
                    {cite.authority && (
                      <div>
                        Cơ quan ban hành: <span style={{ color: "var(--color-slate-800, #1e293b)" }}>{cite.authority}</span>
                      </div>
                    )}
                    {cite.locator && (
                      <div>
                        Vị trí trích lục: <span style={{ color: "var(--color-slate-800, #1e293b)" }}>{cite.locator}</span>
                      </div>
                    )}
                    {cite.effectiveDate && (
                      <div>
                        Ngày hiệu lực: <span style={{ color: "var(--color-slate-800, #1e293b)" }}>{cite.effectiveDate}</span>
                      </div>
                    )}
                  </div>

                  <blockquote
                    style={{
                      margin: 0,
                      padding: "10px 14px",
                      borderLeft: "3px solid var(--color-primary, #1e3a8a)",
                      backgroundColor: "#ffffff",
                      borderRadius: "0 6px 6px 0",
                      fontSize: "13px",
                      color: "var(--color-slate-800, #1e293b)",
                      lineHeight: 1.5,
                      fontStyle: "italic",
                      boxShadow: "inset 0 1px 2px rgba(0,0,0,0.02)",
                    }}
                  >
                    "{cite.quote}"
                  </blockquote>

                  {/* Actions & Report Issue */}
                  <div style={{ marginTop: "12px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px", paddingTop: "8px", borderTop: "1px dashed var(--color-slate-200, #e2e8f0)" }}>
                    {cite.canonicalUrl ? (
                      <a
                        href={cite.canonicalUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "12px",
                          fontWeight: 600,
                          color: "var(--color-primary, #1e3a8a)",
                          textDecoration: "none",
                        }}
                      >
                        <span>Mở văn bản gốc</span>
                        <ArrowRightIcon size={13} />
                      </a>
                    ) : (
                      <span style={{ fontSize: "11px", color: "var(--color-slate-500, #64748b)" }}>
                        Lưu trữ nội bộ HUCE
                      </span>
                    )}

                    {onReportIssue && (
                      <button
                        type="button"
                        onClick={() => onReportIssue(cite.id)}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          padding: "4px 8px",
                          borderRadius: "4px",
                          backgroundColor: "transparent",
                          color: "var(--color-slate-600, #475569)",
                          border: "1px solid var(--color-slate-200, #e2e8f0)",
                          fontSize: "11px",
                          cursor: "pointer",
                        }}
                      >
                        <AlertTriangleIcon size={12} />
                        <span>Báo lỗi nguồn</span>
                      </button>
                    )}
                  </div>
                </article>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}
