import React, { useState } from "react";
import { ClipboardListIcon, ClockIcon, FileTextIcon, ShieldCheckIcon } from "../../components/Icons";

export interface StudentTicket {
  id: string;
  code: string;
  title: string;
  category: string;
  status: "submitted" | "in_progress" | "waiting_student" | "resolved" | "closed";
  createdAt: string;
  description: string;
}

export interface TicketListProps {
  tickets?: StudentTicket[];
}

const statusLabels: Record<StudentTicket["status"], { label: string; bg: string; color: string; border: string }> = {
  submitted: { label: "Đã tiếp nhận", bg: "#f1f5f9", color: "#334155", border: "#cbd5e1" },
  in_progress: { label: "Đang xử lý", bg: "#eff6ff", color: "#1d4ed8", border: "#bfdbfe" },
  waiting_student: { label: "Chờ sinh viên bổ sung", bg: "#fffbeb", color: "#92400e", border: "#fde68a" },
  resolved: { label: "Đã giải quyết", bg: "#ecfdf5", color: "#065f46", border: "#a7f3d0" },
  closed: { label: "Đã đóng", bg: "#f8fafc", color: "#475569", border: "#e2e8f0" },
};

export function TicketList({ tickets = [] }: TicketListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "resolved">("all");

  const toggleDetail = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const filteredTickets = tickets.filter((ticket) => {
    if (filterStatus === "active") {
      return ticket.status === "submitted" || ticket.status === "in_progress" || ticket.status === "waiting_student";
    }
    if (filterStatus === "resolved") {
      return ticket.status === "resolved" || ticket.status === "closed";
    }
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
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

      {/* Ticket List */}
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
          Không có yêu cầu nào trong mục này.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {filteredTickets.map((ticket) => {
            const isExpanded = expandedId === ticket.id;
            const badge = statusLabels[ticket.status] || statusLabels.submitted;
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
                          padding: "3px 10px",
                          borderRadius: "var(--radius-sm, 6px)",
                        }}
                      >
                        {ticket.code}
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

                    <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
                      <ClockIcon size={13} style={{ color: "var(--color-slate-400, #94a3b8)" }} />
                      <span>Ngày gửi: {ticket.createdAt}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleDetail(ticket.id)}
                    aria-expanded={isExpanded}
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
                    style={{
                      marginTop: "16px",
                      paddingTop: "16px",
                      borderTop: "1px solid var(--color-slate-200, #e2e8f0)",
                      fontSize: "14px",
                      backgroundColor: "var(--color-slate-50, #f8fafc)",
                      padding: "16px 20px",
                      borderRadius: "var(--radius-md, 10px)",
                    }}
                  >
                    <p style={{ margin: "0 0 6px 0", fontWeight: 600, fontSize: "13px", color: "var(--color-slate-800, #1e293b)" }}>
                      Nội dung yêu cầu chi tiết:
                    </p>
                    <p style={{ margin: 0, color: "var(--color-slate-700, #334155)", lineHeight: 1.6 }}>
                      {ticket.description}
                    </p>
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
