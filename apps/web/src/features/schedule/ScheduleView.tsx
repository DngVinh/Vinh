import React, { useState } from "react";
import { CalendarIcon, ClockIcon, BuildingIcon, FileTextIcon } from "../../components/Icons";

export interface ScheduleEntry {
  id: string;
  courseCode: string;
  courseName: string;
  dayOfWeek: string;
  time: string;
  room: string;
  lecturer: string;
  type: "class" | "exam";
}

export interface ScheduleViewProps {
  entries?: ScheduleEntry[];
  freshnessTimestamp?: string;
}

export function ScheduleView({
  entries = [],
  freshnessTimestamp,
}: ScheduleViewProps) {
  const [filter, setFilter] = useState<"all" | "class" | "exam">("all");

  const filteredEntries = entries.filter((item) => {
    if (filter === "all") return true;
    return item.type === filter;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header with Freshness Info & Provenance */}
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
            Thời khóa biểu & Lịch thi sinh viên
          </h2>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)" }}>
            Lịch học tập và thi kết thúc học phần được đồng bộ định kỳ từ cổng đào tạo HUCE
          </p>
        </div>

        {freshnessTimestamp && (
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "12px",
              color: "var(--color-slate-700, #334155)",
              backgroundColor: "#ffffff",
              padding: "6px 14px",
              borderRadius: "var(--radius-full, 9999px)",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
            }}
          >
            <span
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                backgroundColor: "#10b981",
                boxShadow: "0 0 0 2px rgba(16, 185, 129, 0.2)",
              }}
            />
            <span>
              Thời điểm đồng bộ:{" "}
              <strong>
                {(() => {
                  const d = new Date(freshnessTimestamp);
                  return isNaN(d.getTime()) ? freshnessTimestamp : d.toLocaleDateString("vi-VN");
                })()}
              </strong>{" "}
              (Dữ liệu mô phỏng)
            </span>
          </div>
        )}
      </div>

      {/* Segmented Filter Control */}
      <div
        role="group"
        aria-label="Bộ lọc phân loại lịch"
        style={{
          display: "inline-flex",
          backgroundColor: "var(--color-slate-100, #f1f5f9)",
          padding: "4px",
          borderRadius: "var(--radius-lg, 14px)",
          gap: "4px",
          alignSelf: "flex-start",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
        }}
      >
        <button
          type="button"
          onClick={() => setFilter("all")}
          aria-pressed={filter === "all"}
          style={{
            padding: "8px 18px",
            borderRadius: "var(--radius-md, 10px)",
            border: "none",
            backgroundColor: filter === "all" ? "#ffffff" : "transparent",
            color: filter === "all" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
            fontWeight: filter === "all" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "all" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
            transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
          }}
        >
          Tất cả
        </button>
        <button
          type="button"
          onClick={() => setFilter("class")}
          aria-pressed={filter === "class"}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "8px 18px",
            borderRadius: "var(--radius-md, 10px)",
            border: "none",
            backgroundColor: filter === "class" ? "#ffffff" : "transparent",
            color: filter === "class" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
            fontWeight: filter === "class" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "class" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
            transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
          }}
        >
          <CalendarIcon size={14} />
          <span>Lịch học</span>
        </button>
        <button
          type="button"
          onClick={() => setFilter("exam")}
          aria-pressed={filter === "exam"}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "8px 18px",
            borderRadius: "var(--radius-md, 10px)",
            border: "none",
            backgroundColor: filter === "exam" ? "#ffffff" : "transparent",
            color: filter === "exam" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
            fontWeight: filter === "exam" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "exam" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
            transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
          }}
        >
          <FileTextIcon size={14} />
          <span>Lịch thi</span>
        </button>
      </div>

      {/* Schedule Table */}
      {filteredEntries.length === 0 ? (
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
            <CalendarIcon size={28} />
          </div>
          <div>
            <p style={{ margin: "0 0 6px 0", fontSize: "16px", fontWeight: 700, color: "var(--color-slate-800, #1e293b)" }}>
              Chưa có lịch học hoặc lịch thi nào.
            </p>
            <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
              Lịch học mới sẽ tự động cập nhật khi phòng Đào tạo công bố danh sách lớp học phần.
            </p>
          </div>
        </div>
      ) : (
        <div
          style={{
            overflowX: "auto",
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-xl, 20px)",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
          }}
        >
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              textAlign: "left",
              fontSize: "14px",
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid var(--color-slate-200, #e2e8f0)",
                  backgroundColor: "var(--color-slate-50, #f8fafc)",
                  color: "var(--color-slate-600, #475569)",
                  fontSize: "12px",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                <th scope="col" style={{ padding: "16px 20px" }}>Mã môn</th>
                <th scope="col" style={{ padding: "16px 20px" }}>Tên học phần</th>
                <th scope="col" style={{ padding: "16px 20px" }}>Thứ</th>
                <th scope="col" style={{ padding: "16px 20px" }}>Thời gian</th>
                <th scope="col" style={{ padding: "16px 20px" }}>Phòng học</th>
                <th scope="col" style={{ padding: "16px 20px" }}>Giảng viên</th>
                <th scope="col" style={{ padding: "16px 20px" }}>Loại</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map((row) => (
                <tr
                  key={row.id}
                  style={{
                    borderBottom: "1px solid var(--color-slate-100, #f1f5f9)",
                    transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                  }}
                >
                  <td style={{ padding: "16px 20px", fontWeight: 700, color: "var(--color-primary, #1e3a8a)" }}>
                    {row.courseCode}
                  </td>
                  <td style={{ padding: "16px 20px", fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>
                    {row.courseName}
                  </td>
                  <td style={{ padding: "16px 20px", color: "var(--color-slate-600, #475569)" }}>
                    {row.dayOfWeek}
                  </td>
                  <td style={{ padding: "16px 20px", color: "var(--color-slate-600, #475569)", whiteSpace: "nowrap" }}>
                    <div style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                      <ClockIcon size={14} style={{ color: "var(--color-slate-400, #94a3b8)" }} />
                      <span>{row.time}</span>
                    </div>
                  </td>
                  <td style={{ padding: "16px 20px" }}>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        padding: "4px 10px",
                        borderRadius: "var(--radius-md, 8px)",
                        fontWeight: 600,
                        fontSize: "12px",
                        backgroundColor: "var(--color-primary-light, #eff6ff)",
                        color: "var(--color-primary, #1e3a8a)",
                      }}
                    >
                      <BuildingIcon size={13} />
                      <span>{row.room}</span>
                    </span>
                  </td>
                  <td style={{ padding: "16px 20px", color: "var(--color-slate-600, #475569)" }}>
                    {row.lecturer}
                  </td>
                  <td style={{ padding: "16px 20px" }}>
                    <span
                      style={{
                        padding: "4px 12px",
                        borderRadius: "var(--radius-full, 9999px)",
                        fontSize: "12px",
                        backgroundColor: row.type === "exam" ? "#fef2f2" : "#f0fdfa",
                        color: row.type === "exam" ? "#991b1b" : "#065f46",
                        border: `1px solid ${row.type === "exam" ? "#fecaca" : "#a7f3d0"}`,
                        fontWeight: 600,
                      }}
                    >
                      {row.type === "exam" ? "Lịch thi" : "Lịch học"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
