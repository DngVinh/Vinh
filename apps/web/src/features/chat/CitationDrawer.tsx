import React, { useEffect } from "react";
import { FileTextIcon, XIcon } from "../../components/Icons";

export interface CitationItem {
  id: string;
  title: string;
  documentRef: string;
  quote: string;
  confidence: number; // 0.0 - 1.0
}

export interface CitationDrawerProps {
  isOpen: boolean;
  citations: CitationItem[];
  onClose: () => void;
}

export function CitationDrawer({ isOpen, citations, onClose }: CitationDrawerProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          backgroundColor: "rgba(15, 23, 42, 0.5)",
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
          width: "440px",
          maxWidth: "92vw",
          backgroundColor: "#ffffff",
          boxShadow: "-8px 0 32px rgba(15, 23, 42, 0.16)",
          zIndex: 1000,
          display: "flex",
          flexDirection: "column",
          padding: "28px",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid var(--color-slate-200, #e2e8f0)",
            paddingBottom: "18px",
            marginBottom: "20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
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
            <h2 id="citation-drawer-title" style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}>
              Nguồn trích dẫn & Bằng chứng
            </h2>
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
              fontSize: "15px",
              color: "var(--color-slate-600, #475569)",
              cursor: "pointer",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "var(--transition-fast, 150ms ease)",
            }}
          >
            <XIcon size={16} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
          {citations.length === 0 ? (
            <div style={{ textAlign: "center", padding: "36px 16px", color: "var(--color-slate-600, #475569)", fontSize: "14px" }}>
              Không có trích dẫn nào cho câu trả lời này.
            </div>
          ) : (
            citations.map((cite) => (
              <article
                key={cite.id}
                style={{
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  borderRadius: "var(--radius-lg, 14px)",
                  padding: "18px 20px",
                  backgroundColor: "var(--color-slate-50, #f8fafc)",
                  boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px", marginBottom: "8px" }}>
                  <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--color-primary, #1e3a8a)", lineHeight: 1.4 }}>
                    {cite.title}
                  </h3>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 600,
                      padding: "2px 8px",
                      borderRadius: "var(--radius-full, 9999px)",
                      backgroundColor: "#ecfdf5",
                      color: "#065f46",
                      border: "1px solid #a7f3d0",
                      whiteSpace: "nowrap",
                    }}
                  >
                    Độ tin cậy: {cite.confidence != null ? `${Math.round(cite.confidence * 100)}%` : "100%"}
                  </span>
                </div>

                <div style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)", marginBottom: "10px" }}>
                  Mã văn bản: <strong style={{ color: "var(--color-slate-800, #1e293b)" }}>{cite.documentRef}</strong>
                </div>

                <blockquote
                  style={{
                    margin: 0,
                    padding: "12px 16px",
                    borderLeft: "3px solid var(--color-primary, #1e3a8a)",
                    backgroundColor: "#ffffff",
                    borderRadius: "0 8px 8px 0",
                    fontSize: "13px",
                    color: "var(--color-slate-800, #1e293b)",
                    lineHeight: 1.6,
                    fontStyle: "italic",
                    boxShadow: "inset 0 1px 2px rgba(0,0,0,0.02)",
                  }}
                >
                  "{cite.quote}"
                </blockquote>
              </article>
            ))
          )}
        </div>
      </div>
    </>
  );
}
