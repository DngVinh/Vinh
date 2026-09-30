import React, { useState } from "react";
import { CalendarIcon, ClockIcon, BuildingIcon, FileTextIcon, AlertTriangleIcon } from "../../components/Icons";

export interface ScheduleEntry {
  id: string;
  courseCode: string;
  courseName: string;
  dayOfWeek: string;
  date?: string;
  time: string;
  room: string;
  lecturer: string;
  type: "class" | "exam";
}

export interface ScheduleViewProps {
  entries?: ScheduleEntry[];
  freshnessTimestamp?: string;
  isStale?: boolean;
  isDegraded?: boolean;
}

export function ScheduleView({
  entries = [],
  freshnessTimestamp,
  isStale = false,
  isDegraded = false,
}: ScheduleViewProps) {
  const [filter, setFilter] = useState<"all" | "class" | "exam">("all");

  const filteredEntries = entries.filter((item) => {
    if (filter === "all") return true;
    return item.type === filter;
  });

  // Next upcoming priority item
  const nextEvent = filteredEntries[0] || null;

  // Group entries by day
  const groupedByDay = filteredEntries.reduce<Record<string, ScheduleEntry[]>>((acc, entry) => {
    const key = entry.dayOfWeek || "Chung";
    if (!acc[key]) acc[key] = [];
    acc[key].push(entry);
    return acc;
  }, {});

  // Check for overlaps within same day
  const hasOverlap = (dayEntries: ScheduleEntry[], current: ScheduleEntry) => {
    return dayEntries.some(
      (other) => other.id !== current.id && other.time === current.time
    );
  };

  const handleExportIcs = () => {
    if (typeof window === "undefined") return;
    let ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//HUCE//Campus 24/7//VI\nCALSCALE:GREGORIAN\n";
    entries.forEach((e) => {
      ics += `BEGIN:VEVENT\nSUMMARY:${e.courseName} (${e.courseCode})\nLOCATION:${e.room}\nDESCRIPTION:Giảng viên: ${e.lecturer} - Loại: ${e.type === "exam" ? "Lịch thi" : "Lịch học"}\nEND:VEVENT\n`;
    });
    ics += "END:VCALENDAR";

    try {
      const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `lich_hoc_huce_${new Date().toISOString().split("T")[0]}.ics`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // Fallback
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header with Timezone & Provenance Info */}
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
          <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
            <span>Múi giờ: <strong>ICT (UTC+7)</strong></span>
            <span>•</span>
            <span>Nguồn: <strong>Cổng đào tạo HUCE (Dữ liệu mô phỏng)</strong></span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
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
                  backgroundColor: isStale || isDegraded ? "#f59e0b" : "#10b981",
                }}
              />
              <span>
                Đồng bộ lúc:{" "}
                <strong>
                  {(() => {
                    const d = new Date(freshnessTimestamp);
                    return isNaN(d.getTime()) 
                      ? freshnessTimestamp 
                      : d.toLocaleTimeString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit" }) + 
                        " " + 
                        d.toLocaleDateString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" });
                  })()}
                </strong>
              </span>
            </div>
          )}

          <button
            type="button"
            onClick={handleExportIcs}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              borderRadius: "var(--radius-full, 9999px)",
              backgroundColor: "#ffffff",
              border: "1px solid var(--color-slate-300, #cbd5e1)",
              color: "var(--color-slate-700, #334155)",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
            }}
          >
            <span>📥</span> Xuất lịch iCal (.ics)
          </button>
        </div>
      </div>

      {/* Priority 1: Next Event Spotlight Hero */}
      {nextEvent && (
        <section
          aria-labelledby="heading-next-spotlight"
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-lg, 14px)",
            padding: "20px 24px",
            border: "1px solid var(--color-primary-border, #bfdbfe)",
            background: "linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%)",
            boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04))",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "var(--radius-md, 10px)",
                backgroundColor: "#eff6ff",
                color: "#1d4ed8",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <ClockIcon size={24} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    color: "#1d4ed8",
                    backgroundColor: "#dbeafe",
                    padding: "2px 8px",
                    borderRadius: "4px",
                  }}
                >
                  {nextEvent.type === "exam" ? "Lịch thi kế tiếp" : "Tiết học kế tiếp"}
                </span>
                <span style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
                  {nextEvent.dayOfWeek}
                </span>
              </div>
              <h3 id="heading-next-spotlight" style={{ margin: 0, fontSize: "17px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                Sự kiện kế tiếp: {nextEvent.courseName} ({nextEvent.courseCode})
              </h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "4px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", fontWeight: 600 }}>
                  <BuildingIcon size={14} /> {nextEvent.room}
                </span>
                <span>•</span>
                <time dateTime={nextEvent.time}>{nextEvent.time}</time>
                <span>•</span>
                <span>{nextEvent.lecturer}</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Filter Control Bar */}
      <div
        role="group"
        aria-label="Bộ lọc phân loại lịch"
        style={{
          display: "inline-flex",
          backgroundColor: "var(--color-slate-100, #f1f5f9)",
          padding: "4px",
          borderRadius: "var(--radius-lg, 12px)",
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
            padding: "8px 16px",
            borderRadius: "var(--radius-md, 8px)",
            border: "none",
            backgroundColor: filter === "all" ? "#ffffff" : "transparent",
            color: filter === "all" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
            fontWeight: filter === "all" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "all" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
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
            padding: "8px 16px",
            borderRadius: "var(--radius-md, 8px)",
            border: "none",
            backgroundColor: filter === "class" ? "#ffffff" : "transparent",
            color: filter === "class" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
            fontWeight: filter === "class" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "class" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
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
            padding: "8px 16px",
            borderRadius: "var(--radius-md, 8px)",
            border: "none",
            backgroundColor: filter === "exam" ? "#ffffff" : "transparent",
            color: filter === "exam" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
            fontWeight: filter === "exam" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "exam" ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
          }}
        >
          <FileTextIcon size={14} />
          <span>Lịch thi</span>
        </button>
      </div>

      {/* Agenda Grouped Content Area (Accessible Scroll Region) */}
      {filteredEntries.length === 0 ? (
        <div
          role="status"
          style={{
            padding: "48px 24px",
            textAlign: "center",
            color: "var(--color-slate-600, #475569)",
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-xl, 16px)",
            border: "1.5px dashed var(--color-slate-300, #cbd5e1)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "50%",
              backgroundColor: "var(--color-slate-100, #f1f5f9)",
              color: "var(--color-slate-500, #64748b)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CalendarIcon size={24} />
          </div>
          <div>
            <p style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700, color: "var(--color-slate-800, #1e293b)" }}>
              Chưa có lịch học hoặc lịch thi nào.
            </p>
            <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-500, #64748b)" }}>
              Lịch học mới sẽ tự động cập nhật khi có thông báo chính thức từ phòng Đào tạo.
            </p>
          </div>
        </div>
      ) : (
        <div
          role="region"
          aria-label="Lịch học sinh viên"
          tabIndex={0}
          style={{
            overflowX: "auto",
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-xl, 16px)",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04))",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {Object.entries(groupedByDay).map(([day, dayEntries]) => (
            <div key={day} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <h4
                style={{
                  margin: 0,
                  fontSize: "14px",
                  fontWeight: 700,
                  color: "var(--color-primary, #1e3a8a)",
                  paddingBottom: "6px",
                  borderBottom: "1.5px solid var(--color-slate-200, #e2e8f0)",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span>{day}</span>
                <span style={{ fontSize: "12px", fontWeight: 500, color: "var(--color-slate-500, #64748b)" }}>
                  ({dayEntries.length} ca)
                </span>
              </h4>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {dayEntries.map((row) => {
                  const overlapping = hasOverlap(dayEntries, row);
                  return (
                    <article
                      key={row.id}
                      style={{
                        padding: "14px 16px",
                        borderRadius: "8px",
                        backgroundColor: overlapping ? "#fff1f2" : "var(--color-slate-50, #f8fafc)",
                        border: overlapping ? "1px solid #fecdd3" : "1px solid var(--color-slate-200, #e2e8f0)",
                        display: "flex",
                        flexWrap: "wrap",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "12px",
                      }}
                    >
                      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontWeight: 700, color: "var(--color-primary, #1e3a8a)", fontSize: "14px" }}>
                            {row.courseCode}
                          </span>
                          <span style={{ fontWeight: 600, color: "var(--color-slate-900, #0f172a)", fontSize: "14px" }}>
                            {row.courseName}
                          </span>
                          {overlapping && (
                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "4px",
                                fontSize: "11px",
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: "4px",
                                backgroundColor: "#fee2e2",
                                color: "#991b1b",
                              }}
                            >
                              <AlertTriangleIcon size={12} />
                              <span>Trùng ca học</span>
                            </span>
                          )}
                        </div>

                        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                            <ClockIcon size={14} />
                            <time dateTime={row.time}>{row.time}</time>
                          </span>
                          <span>•</span>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", fontWeight: 600 }}>
                            <BuildingIcon size={14} /> {row.room}
                          </span>
                          <span>•</span>
                          <span>{row.lecturer}</span>
                        </div>
                      </div>

                      <span
                        style={{
                          padding: "3px 10px",
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
                    </article>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
