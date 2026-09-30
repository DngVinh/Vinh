import React, { useState } from "react";
import { ClipboardListIcon, ClockIcon } from "../../components/Icons";

export interface TicketEvent {
  id: string;
  timestamp: string;
  description: string;
  actor?: string;
}

export interface StudentTicket {
  id: string;
  code: string;
  title: string;
  category: string;
  status:
    | "submitted"
    | "queued"
    | "claimed"
    | "in_progress"
    | "waiting_student"
    | "transferred"
    | "resolved"
    | "closed"
    | "escalated";
  createdAt: string;
  updatedAt?: string;
  description: string;
  nextAction?: string;
  events?: TicketEvent[];
}

export interface TicketListProps {
  tickets?: StudentTicket[];
  onSupplementInfo?: (ticketId: string, payload: { content: string }) => void;
  onFeedbackRating?: (ticketId: string, payload: { rating: number; comment?: string }) => void;
}

const statusLabels: Record<StudentTicket["status"], { label: string; bg: string; color: string; border: string }> = {
  submitted: { label: "Đã tiếp nhận", bg: "var(--color-slate-100, #f1f5f9)", color: "var(--color-slate-700, #334155)", border: "var(--color-slate-300, #cbd5e1)" },
  queued: { label: "Đã tiếp nhận", bg: "var(--color-slate-100, #f1f5f9)", color: "var(--color-slate-700, #334155)", border: "var(--color-slate-300, #cbd5e1)" },
  claimed: { label: "Đã chuyển cán bộ phụ trách", bg: "var(--color-primary-light, #eff6ff)", color: "var(--color-primary, #1e3a8a)", border: "var(--color-blue-200, #bfdbfe)" },
  in_progress: { label: "Đang xử lý", bg: "var(--color-blue-50, #eff6ff)", color: "var(--color-blue-700, #1d4ed8)", border: "var(--color-blue-200, #bfdbfe)" },
  waiting_student: { label: "Cần bạn bổ sung thông tin", bg: "var(--color-amber-50, #fffbeb)", color: "var(--color-amber-800, #92400e)", border: "var(--color-amber-200, #fde68a)" },
  transferred: { label: "Đã chuyển đơn vị phù hợp", bg: "var(--color-blue-50, #eff6ff)", color: "var(--color-blue-700, #1d4ed8)", border: "var(--color-blue-200, #bfdbfe)" },
  resolved: { label: "Đã có kết quả", bg: "var(--color-emerald-50, #ecfdf5)", color: "var(--color-emerald-800, #065f46)", border: "var(--color-emerald-200, #a7f3d0)" },
  closed: { label: "Đã đóng", bg: "var(--color-slate-100, #f8fafc)", color: "var(--color-slate-600, #475569)", border: "var(--color-slate-200, #e2e8f0)" },
  escalated: { label: "Đang được ưu tiên xem xét", bg: "var(--color-amber-50, #fffbeb)", color: "var(--color-amber-800, #92400e)", border: "var(--color-amber-200, #fde68a)" },
};

export function TicketList({ tickets = [], onSupplementInfo, onFeedbackRating }: TicketListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "resolved">("all");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Additional info state
  const [isSupplementOpen, setIsSupplementOpen] = useState<Record<string, boolean>>({});
  const [supplementTexts, setSupplementTexts] = useState<Record<string, string>>({});
  const [supplementSubmitted, setSupplementSubmitted] = useState<Record<string, boolean>>({});

  // Feedback rating state
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const [comments, setComments] = useState<Record<string, string>>({});
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<Record<string, boolean>>({});

  const toggleDetail = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleCopyCode = async (code: string) => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(code);
        setCopiedCode(code);
        setTimeout(() => setCopiedCode(null), 3000);
      }
    } catch {
      // Fallback ignore if clipboard not permitted
    }
  };

  const handleSubmitSupplement = (ticketId: string) => {
    const text = (supplementTexts[ticketId] || "").trim();
    if (!text) return;
    onSupplementInfo?.(ticketId, { content: text });
    setSupplementSubmitted((prev) => ({ ...prev, [ticketId]: true }));
    setIsSupplementOpen((prev) => ({ ...prev, [ticketId]: false }));
  };

  const handleSubmitFeedback = (ticketId: string) => {
    const star = ratings[ticketId] || 5;
    const comment = (comments[ticketId] || "").trim();
    onFeedbackRating?.(ticketId, { rating: star, comment: comment || undefined });
    setFeedbackSubmitted((prev) => ({ ...prev, [ticketId]: true }));
  };

  const filteredTickets = tickets.filter((ticket) => {
    if (filterStatus === "active") {
      return ticket.status !== "resolved" && ticket.status !== "closed";
    }
    if (filterStatus === "resolved") {
      return ticket.status === "resolved" || ticket.status === "closed";
    }
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Accessible Live Region for Copy Feedback */}
      {copiedCode && (
        <div
          role="status"
          aria-live="polite"
          style={{
            position: "fixed",
            bottom: "20px",
            right: "20px",
            backgroundColor: "var(--color-slate-900, #0f172a)",
            color: "#ffffff",
            padding: "8px 16px",
            borderRadius: "var(--radius-md, 10px)",
            fontSize: "13px",
            boxShadow: "var(--shadow-md, 0 4px 6px -1px rgba(0,0,0,0.1))",
            zIndex: 50,
          }}
        >
          Đã sao chép mã {copiedCode} vào bộ nhớ tạm
        </div>
      )}

      {/* Header & Filter Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <h2 style={{ margin: "0 0 6px 0", fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}>
            Tra cứu & Theo dõi yêu cầu hỗ trợ (Một cửa số)
          </h2>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)" }}>
            Theo dõi trạng thái và tiến độ xử lý hồ sơ hành chính, học vụ của bạn
          </p>
        </div>

        {/* Filter Pills */}
        <div
          role="group"
          aria-label="Lọc trạng thái yêu cầu"
          style={{
            display: "inline-flex",
            backgroundColor: "var(--color-slate-100, #f1f5f9)",
            padding: "4px",
            borderRadius: "var(--radius-lg, 14px)",
            gap: "4px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
          }}
        >
          <button
            type="button"
            onClick={() => setFilterStatus("all")}
            aria-pressed={filterStatus === "all"}
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius-md, 10px)",
              border: "none",
              backgroundColor: filterStatus === "all" ? "#ffffff" : "transparent",
              color: filterStatus === "all" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
              fontWeight: filterStatus === "all" ? 600 : 500,
              fontSize: "13px",
              cursor: "pointer",
              boxShadow: filterStatus === "all" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
              transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
            }}
          >
            Tất cả ({tickets.length})
          </button>
          <button
            type="button"
            onClick={() => setFilterStatus("active")}
            aria-pressed={filterStatus === "active"}
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius-md, 10px)",
              border: "none",
              backgroundColor: filterStatus === "active" ? "#ffffff" : "transparent",
              color: filterStatus === "active" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
              fontWeight: filterStatus === "active" ? 600 : 500,
              fontSize: "13px",
              cursor: "pointer",
              boxShadow: filterStatus === "active" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
              transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
            }}
          >
            Đang xử lý
          </button>
          <button
            type="button"
            onClick={() => setFilterStatus("resolved")}
            aria-pressed={filterStatus === "resolved"}
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius-md, 10px)",
              border: "none",
              backgroundColor: filterStatus === "resolved" ? "#ffffff" : "transparent",
              color: filterStatus === "resolved" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
              fontWeight: filterStatus === "resolved" ? 600 : 500,
              fontSize: "13px",
              cursor: "pointer",
              boxShadow: filterStatus === "resolved" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
              transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
            }}
          >
            Đã hoàn thành
          </button>
        </div>
      </div>

      {/* Ticket List View */}
      {tickets.length === 0 ? (
        <div
          role="status"
          style={{
            padding: "54px 24px",
            textAlign: "center",
            color: "var(--color-slate-600, #475569)",
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-xl, 20px)",
            border: "1.5px dashed var(--color-slate-300, #cbd5e1)",
            boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              backgroundColor: "var(--color-slate-100, #f1f5f9)",
              color: "var(--color-slate-500, #64748b)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <ClipboardListIcon size={28} />
          </div>
          <div>
            <p style={{ margin: "0 0 6px 0", fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
              Bạn chưa có yêu cầu hỗ trợ nào.
            </p>
            <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
              Các phiếu hỗ trợ một cửa số sau khi tạo sẽ hiển thị tại đây.
            </p>
          </div>
        </div>
      ) : filteredTickets.length === 0 ? (
        <div
          role="status"
          style={{
            padding: "40px 24px",
            textAlign: "center",
            color: "var(--color-slate-600, #475569)",
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-xl, 20px)",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
          }}
        >
          Không có kết quả phù hợp với bộ lọc đã chọn.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {filteredTickets.map((ticket) => {
            const isExpanded = expandedId === ticket.id;
            const badge = statusLabels[ticket.status] || statusLabels.submitted;
            const detailId = `ticket-detail-${ticket.id}`;
            const isWaiting = ticket.status === "waiting_student";
            const isDone = ticket.status === "resolved" || ticket.status === "closed";
            const hasSupplementForm = !!isSupplementOpen[ticket.id];
            const alreadySupplied = !!supplementSubmitted[ticket.id];
            const currentRating = ratings[ticket.id] || 5;
            const isRated = !!feedbackSubmitted[ticket.id];

            return (
              <article
                key={ticket.id}
                style={{
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  borderRadius: "var(--radius-lg, 14px)",
                  padding: "20px 24px",
                  backgroundColor: "#ffffff",
                  boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
                  transition: "var(--transition-spring, 220ms cubic-bezier(0.16, 1, 0.3, 1))",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                    gap: "14px",
                  }}
                >
                  <div style={{ flex: 1, minWidth: "260px" }}>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px", flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontSize: "12px",
                          fontWeight: 700,
                          color: "var(--color-primary, #1e3a8a)",
                          backgroundColor: "var(--color-primary-light, #eff6ff)",
                          padding: "3px 8px",
                          borderRadius: "var(--radius-sm, 6px)",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "6px",
                        }}
                      >
                        <span>{ticket.code}</span>
                        <button
                          type="button"
                          onClick={() => handleCopyCode(ticket.code)}
                          aria-label={`Sao chép mã ${ticket.code}`}
                          title={`Sao chép mã ${ticket.code}`}
                          style={{
                            background: "transparent",
                            border: "none",
                            cursor: "pointer",
                            padding: "0 2px",
                            fontSize: "11px",
                            color: "var(--color-primary, #1e3a8a)",
                          }}
                        >
                          📋
                        </button>
                      </span>
                      <span
                        style={{
                          fontSize: "12px",
                          padding: "3px 10px",
                          borderRadius: "var(--radius-full, 9999px)",
                          backgroundColor: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.border}`,
                          fontWeight: 600,
                        }}
                      >
                        {badge.label}
                      </span>
                      <span
                        style={{
                          fontSize: "12px",
                          color: "var(--color-slate-600, #475569)",
                          backgroundColor: "var(--color-slate-100, #f1f5f9)",
                          padding: "3px 10px",
                          borderRadius: "var(--radius-sm, 6px)",
                          fontWeight: 500,
                        }}
                      >
                        {ticket.category}
                      </span>
                    </div>

                    <h3 style={{ margin: "6px 0 6px 0", fontSize: "17px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                      {ticket.title}
                    </h3>

                    <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--color-slate-600, #475569)", flexWrap: "wrap" }}>
                      <ClockIcon size={13} style={{ color: "var(--color-slate-400, #94a3b8)" }} />
                      <span>Ngày gửi: {ticket.createdAt}</span>
                      {ticket.updatedAt && (
                        <span>· Cập nhật: {ticket.updatedAt}</span>
                      )}
                    </div>

                    {/* Next Action Callout for Student Ownership */}
                    {ticket.nextAction && (
                      <div
                        style={{
                          marginTop: "12px",
                          padding: "10px 14px",
                          borderRadius: "var(--radius-md, 10px)",
                          backgroundColor: "var(--color-amber-50, #fffbeb)",
                          border: "1px solid var(--color-amber-200, #fde68a)",
                          color: "var(--color-amber-900, #78350f)",
                          fontSize: "13px",
                          display: "flex",
                          alignItems: "flex-start",
                          gap: "8px",
                        }}
                      >
                        <span style={{ fontWeight: 600 }}>Cần thực hiện:</span>
                        <span>{ticket.nextAction}</span>
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleDetail(ticket.id)}
                    aria-expanded={isExpanded}
                    aria-controls={detailId}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "var(--radius-md, 10px)",
                      border: "1px solid var(--color-slate-300, #cbd5e1)",
                      backgroundColor: isExpanded ? "var(--color-slate-100, #f1f5f9)" : "#ffffff",
                      cursor: "pointer",
                      fontSize: "13px",
                      fontWeight: 600,
                      color: "var(--color-slate-800, #1e293b)",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
                      transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                    }}
                  >
                    <span>{isExpanded ? "Thu gọn" : "Chi tiết"}</span>
                    <span style={{ fontSize: "10px", transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 150ms ease" }}>
                      ▼
                    </span>
                  </button>
                </div>

                {isExpanded && (
                  <div
                    id={detailId}
                    style={{
                      marginTop: "16px",
                      paddingTop: "16px",
                      borderTop: "1px solid var(--color-slate-200, #e2e8f0)",
                      fontSize: "14px",
                      backgroundColor: "var(--color-slate-50, #f8fafc)",
                      padding: "16px 20px",
                      borderRadius: "var(--radius-md, 10px)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "16px",
                    }}
                  >
                    <div>
                      <p style={{ margin: "0 0 6px 0", fontWeight: 600, fontSize: "13px", color: "var(--color-slate-800, #1e293b)" }}>
                        Nội dung yêu cầu chi tiết:
                      </p>
                      <p style={{ margin: 0, color: "var(--color-slate-700, #334155)", lineHeight: 1.6 }}>
                        {ticket.description}
                      </p>
                    </div>

                    {/* Interactive Supplement Form for waiting_student */}
                    {isWaiting && (
                      <div
                        style={{
                          backgroundColor: "#fffbeb",
                          border: "1.5px solid #fde68a",
                          padding: "14px 16px",
                          borderRadius: "10px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                          <div>
                            <div style={{ fontWeight: 700, color: "#92400e", fontSize: "13px" }}>
                              ⚠️ Cán bộ đang chờ bạn bổ sung thông tin hồ sơ
                            </div>
                            <div style={{ fontSize: "12px", color: "#b45309", marginTop: "2px" }}>
                              {ticket.nextAction || "Vui lòng phản hồi sớm để quy trình tiếp tục xử lý."}
                            </div>
                          </div>

                          {!alreadySupplied && !hasSupplementForm && (
                            <button
                              type="button"
                              onClick={() => setIsSupplementOpen((prev) => ({ ...prev, [ticket.id]: true }))}
                              style={{
                                padding: "8px 16px",
                                borderRadius: "8px",
                                border: "none",
                                backgroundColor: "#d97706",
                                color: "#ffffff",
                                fontWeight: 600,
                                fontSize: "13px",
                                cursor: "pointer",
                              }}
                            >
                              Bổ sung thông tin theo yêu cầu
                            </button>
                          )}
                        </div>

                        {alreadySupplied && (
                          <div style={{ marginTop: "10px", fontSize: "13px", color: "#047857", fontWeight: 600 }}>
                            ✓ Bạn đã gửi bổ sung thông tin. Cán bộ Một cửa đang tiến hành thẩm định.
                          </div>
                        )}

                        {hasSupplementForm && (
                          <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "10px" }}>
                            <textarea
                              rows={3}
                              placeholder="Nhập nội dung phản hồi hoặc làm rõ thông tin theo yêu cầu cán bộ..."
                              value={supplementTexts[ticket.id] || ""}
                              onChange={(e) =>
                                setSupplementTexts((prev) => ({ ...prev, [ticket.id]: e.target.value }))
                              }
                              style={{
                                width: "100%",
                                padding: "10px 12px",
                                borderRadius: "8px",
                                border: "1px solid #cbd5e1",
                                fontSize: "13px",
                                boxSizing: "border-box",
                              }}
                            />
                            <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
                              <button
                                type="button"
                                onClick={() => setIsSupplementOpen((prev) => ({ ...prev, [ticket.id]: false }))}
                                style={{
                                  padding: "6px 14px",
                                  borderRadius: "6px",
                                  border: "1px solid #cbd5e1",
                                  backgroundColor: "#ffffff",
                                  fontSize: "13px",
                                  cursor: "pointer",
                                }}
                              >
                                Đóng
                              </button>
                              <button
                                type="button"
                                onClick={() => handleSubmitSupplement(ticket.id)}
                                style={{
                                  padding: "6px 16px",
                                  borderRadius: "6px",
                                  border: "none",
                                  backgroundColor: "#d97706",
                                  color: "#ffffff",
                                  fontWeight: 600,
                                  fontSize: "13px",
                                  cursor: "pointer",
                                }}
                              >
                                Gửi bổ sung cho cán bộ
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* CSAT Satisfaction Rating for Resolved / Closed tickets */}
                    {isDone && (
                      <div
                        style={{
                          backgroundColor: "#f0fdf4",
                          border: "1.5px solid #bbf7d0",
                          padding: "14px 18px",
                          borderRadius: "10px",
                        }}
                      >
                        <h4 style={{ margin: "0 0 6px 0", fontSize: "13px", fontWeight: 700, color: "#166534" }}>
                          ⭐ Đánh giá mức độ hài lòng về kết quả xử lý
                        </h4>
                        <p style={{ margin: "0 0 10px 0", fontSize: "12px", color: "#15803d" }}>
                          Ý kiến của bạn giúp Nhà trường không ngừng nâng cao chất lượng dịch vụ Một cửa số.
                        </p>

                        {isRated ? (
                          <div style={{ color: "#15803d", fontWeight: 600, fontSize: "13px" }}>
                            ✓ Cảm ơn bạn đã gửi đánh giá! Nhà trường đã ghi nhận phản hồi của bạn.
                          </div>
                        ) : (
                          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                              <span style={{ fontSize: "13px", fontWeight: 600, color: "#166534" }}>Chọn số sao:</span>
                              {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                  key={star}
                                  type="button"
                                  onClick={() => setRatings((prev) => ({ ...prev, [ticket.id]: star }))}
                                  aria-label={`${star} sao`}
                                  style={{
                                    padding: "4px 8px",
                                    borderRadius: "6px",
                                    border: star === currentRating ? "1px solid #16a34a" : "1px solid #cbd5e1",
                                    backgroundColor: star <= currentRating ? "#fef08a" : "#ffffff",
                                    cursor: "pointer",
                                    fontSize: "13px",
                                    fontWeight: 700,
                                    color: "#854d0e",
                                  }}
                                >
                                  ★ {star}
                                </button>
                              ))}
                            </div>

                            <textarea
                              rows={2}
                              placeholder="Ý kiến đóng góp cải tiến chất lượng phục vụ (không bắt buộc)..."
                              value={comments[ticket.id] || ""}
                              onChange={(e) =>
                                setComments((prev) => ({ ...prev, [ticket.id]: e.target.value }))
                              }
                              style={{
                                width: "100%",
                                padding: "8px 12px",
                                borderRadius: "8px",
                                border: "1px solid #cbd5e1",
                                fontSize: "13px",
                                boxSizing: "border-box",
                              }}
                            />

                            <button
                              type="button"
                              onClick={() => handleSubmitFeedback(ticket.id)}
                              style={{
                                alignSelf: "flex-start",
                                padding: "6px 16px",
                                borderRadius: "6px",
                                border: "none",
                                backgroundColor: "#16a34a",
                                color: "#ffffff",
                                fontWeight: 600,
                                fontSize: "13px",
                                cursor: "pointer",
                              }}
                            >
                              Gửi đánh giá
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Ordered Public Event History (No Internal Notes) */}
                    {ticket.events && ticket.events.length > 0 && (
                      <div style={{ borderTop: "1px dashed var(--color-slate-200, #e2e8f0)", paddingTop: "12px" }}>
                        <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", fontWeight: 700, color: "var(--color-slate-800, #1e293b)" }}>
                          Lịch sử xử lý công khai:
                        </h4>
                        <ol style={{ margin: 0, paddingLeft: "18px", display: "flex", flexDirection: "column", gap: "6px" }}>
                          {ticket.events.map((evt) => (
                            <li key={evt.id} style={{ fontSize: "13px", color: "var(--color-slate-700, #334155)", lineHeight: 1.5 }}>
                              <span style={{ fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>{evt.timestamp}</span>
                              {evt.actor && <span> ({evt.actor})</span>}
                              <span>: </span>
                              <span>{evt.description}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
