import React, { useState } from "react";

export interface StaffQueueItem {
  id: string;
  ticketCode: string;
  studentName: string;
  studentId: string;
  title: string;
  status: "unassigned" | "assigned" | "in_progress" | "resolved";
  assignedStaffId?: string;
  priority: "normal" | "high" | "urgent";
  createdAt: string;
}

export interface StaffTicketQueueProps {
  items?: StaffQueueItem[];
  currentStaffId?: string;
  onClaimTicket?: (queueId: string) => void;
}

export function StaffTicketQueue({
  items = [],
  currentStaffId = "",
  onClaimTicket,
}: StaffTicketQueueProps) {
  const [filter, setFilter] = useState<"all" | "unassigned" | "my">("all");

  const filteredItems = items.filter((item) => {
    if (filter === "unassigned") return item.status === "unassigned";
    if (filter === "my") return item.assignedStaffId === currentStaffId;
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header and Staff Identity */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <h2 style={{ margin: "0 0 4px 0", fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
            Hàng đợi tiếp nhận yêu cầu (Cán bộ một cửa)
          </h2>
          <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-500, #64748b)" }}>
            Tiếp nhận và xử lý các ca chuyển giao từ AI chatbot cần cán bộ hỗ trợ trực tiếp
          </p>
        </div>

        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "13px",
            color: "var(--color-slate-700, #334155)",
            backgroundColor: "var(--color-slate-100, #f1f5f9)",
            padding: "6px 14px",
            borderRadius: "9999px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
          }}
        >
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#10b981" }} />
          <span>Cán bộ trực: <strong>{currentStaffId || "Chưa xác định"}</strong></span>
        </div>
      </div>

      {/* Segmented Filter Tabs */}
      <div
        style={{
          display: "flex",
          backgroundColor: "var(--color-slate-100, #f1f5f9)",
          padding: "3px",
          borderRadius: "var(--radius-md, 10px)",
          gap: "2px",
          alignSelf: "flex-start",
        }}
      >
        <button
          type="button"
          onClick={() => setFilter("all")}
          aria-pressed={filter === "all"}
          style={{
            padding: "6px 16px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: filter === "all" ? "#ffffff" : "transparent",
            color: filter === "all" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-600, #475569)",
            fontWeight: filter === "all" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "all" ? "var(--shadow-xs)" : "none",
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          Tất cả ({items.length})
        </button>
        <button
          type="button"
          onClick={() => setFilter("unassigned")}
          aria-pressed={filter === "unassigned"}
          style={{
            padding: "6px 16px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: filter === "unassigned" ? "#ffffff" : "transparent",
            color: filter === "unassigned" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-600, #475569)",
            fontWeight: filter === "unassigned" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "unassigned" ? "var(--shadow-xs)" : "none",
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          Chưa nhận
        </button>
        <button
          type="button"
          onClick={() => setFilter("my")}
          aria-pressed={filter === "my"}
          style={{
            padding: "6px 16px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: filter === "my" ? "#ffffff" : "transparent",
            color: filter === "my" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-600, #475569)",
            fontWeight: filter === "my" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "my" ? "var(--shadow-xs)" : "none",
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          Ca của tôi
        </button>
      </div>

      {/* Queue Table */}
      <div
        style={{
          overflowX: "auto",
          backgroundColor: "#ffffff",
          borderRadius: "var(--radius-lg, 14px)",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.04))",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "14px" }}>
          <thead>
            <tr
              style={{
                backgroundColor: "var(--color-slate-50, #f8fafc)",
                borderBottom: "1px solid var(--color-slate-200, #e2e8f0)",
                color: "var(--color-slate-600, #475569)",
                fontSize: "12px",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
              }}
            >
              <th scope="col" style={{ padding: "14px 18px" }}>Mã yêu cầu</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Sinh viên</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Nội dung</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Ưu tiên</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Trạng thái</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => {
              const isUnassigned = item.status === "unassigned";
              const isMyItem = item.assignedStaffId === currentStaffId;
              const canClaim = isUnassigned;

              return (
                <tr
                  key={item.id}
                  style={{
                    borderBottom: "1px solid var(--color-slate-100, #f1f5f9)",
                    transition: "var(--transition-fast, 150ms ease)",
                  }}
                >
                  <td style={{ padding: "14px 18px", fontWeight: 700, color: "var(--color-primary, #1e3a8a)" }}>
                    {item.ticketCode}
                  </td>
                  <td style={{ padding: "14px 18px", color: "var(--color-slate-800, #1e293b)", fontWeight: 500 }}>
                    {item.studentName} ({item.studentId})
                  </td>
                  <td style={{ padding: "14px 18px", color: "var(--color-slate-700, #334155)" }}>
                    {item.title}
                  </td>
                  <td style={{ padding: "14px 18px" }}>
                    <span
                      style={{
                        padding: "3px 10px",
                        borderRadius: "9999px",
                        fontSize: "12px",
                        fontWeight: 600,
                        backgroundColor: item.priority === "high" ? "#fef2f2" : "#f1f5f9",
                        color: item.priority === "high" ? "#b91c1c" : "#475569",
                        border: `1px solid ${item.priority === "high" ? "#fecaca" : "#cbd5e1"}`,
                      }}
                    >
                      {item.priority === "high" ? "Cao" : "Thường"}
                    </span>
                  </td>
                  <td style={{ padding: "14px 18px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
                    {isUnassigned ? "Chờ tiếp nhận" : isMyItem ? "Tôi đang xử lý" : `Đã nhận (${item.assignedStaffId})`}
                  </td>
                  <td style={{ padding: "14px 18px" }}>
                    <button
                      type="button"
                      onClick={() => onClaimTicket?.(item.id)}
                      disabled={!canClaim}
                      aria-label={canClaim ? `Nhận xử lý ${item.ticketCode}` : `Đã nhận - ${item.ticketCode}`}
                      style={{
                        padding: "8px 16px",
                        borderRadius: "var(--radius-sm, 6px)",
                        border: "none",
                        backgroundColor: canClaim ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-200, #e2e8f0)",
                        color: canClaim ? "#ffffff" : "var(--color-slate-500, #64748b)",
                        fontWeight: 600,
                        fontSize: "13px",
                        cursor: canClaim ? "pointer" : "not-allowed",
                        minHeight: "44px",
                        boxShadow: canClaim ? "var(--shadow-xs)" : "none",
                        transition: "var(--transition-fast, 150ms ease)",
                      }}
                    >
                      {canClaim ? "Nhận xử lý" : "Đã nhận"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
