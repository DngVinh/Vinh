import React from "react";
import { AppShell } from "../components/AppShell";
import {
  SparklesIcon,
  BotIcon,
  CalendarIcon,
  ClipboardListIcon,
  BuildingIcon,
  ClockIcon,
  SearchIcon,
  ArrowRightIcon,
  ShieldCheckIcon,
} from "../components/Icons";
import { CapabilityBanner, type SystemOperationalStatus } from "../features/operations/CapabilityBanner";
import { AsyncState, type AsyncStatus } from "../components/AsyncState";

export interface UserSession {
  isAuthenticated: boolean;
  userId?: string;
  name?: string;
  role?: string;
}

export interface DashboardScheduleItem {
  id: string;
  courseName: string;
  courseCode: string;
  room: string;
  timeSlot: string;
  lecturer: string;
  syncTime: string;
  source?: string;
}

export interface DashboardTicketSummary {
  id: string;
  code: string;
  title: string;
  statusText: string;
  updatedAt: string;
  source?: string;
}

export interface HomePageProps {
  params?: Record<string, string | string[]>;
  searchParams?: Record<string, string | string[] | undefined>;
  user?: UserSession | null;
  systemStatus?: SystemOperationalStatus | null;
  schedule?: DashboardScheduleItem | null;
  tickets?: DashboardTicketSummary[];
  status?: AsyncStatus;
  errorMessage?: string;
  onRetry?: () => void;
  unavailableCapabilities?: string[];
}

export default function HomePage(props: any) {
  const currentStatus = props?.status || (props?.searchParams?.status as AsyncStatus) || "success";

  // Async state handling (Loading, Error, Outage)
  if (currentStatus === "loading") {
    return (
      <AppShell activeNav="home">
        <div style={{ padding: "40px 0" }}>
          <AsyncState status="loading" loadingMessage="Đang đồng bộ trạng thái học vụ..." />
        </div>
      </AppShell>
    );
  }

  if (currentStatus === "error") {
    return (
      <AppShell activeNav="home">
        <div style={{ padding: "40px 0" }}>
          <AsyncState
            status="error"
            errorMessage={props.errorMessage || "Không thể kết nối máy chủ dữ liệu học vụ"}
            onRetry={props.onRetry}
          />
        </div>
      </AppShell>
    );
  }

  // Authoritative identity resolution: default to authenticated unless explicitly anonymous or unauthenticated
  const isAnonymous = props.user
    ? !props.user.isAuthenticated
    : props.searchParams?.auth === "anonymous";
  const isAuthenticated = !isAnonymous;

  // Authoritative operational status resolution
  const systemStatus: SystemOperationalStatus | null = props.systemStatus || (
    props.searchParams?.status === "degraded"
      ? {
          mode: "degraded",
          message: "Hệ thống đang hoạt động ở chế độ suy giảm một phần tính năng.",
          affectedServices: ["Thời khóa biểu", "Tra cứu phòng"],
          impact: "Dữ liệu lịch học có thể bị trễ và không phản ánh thay đổi tức thời.",
          safeNextAction: "Vui lòng đối chiếu với thông báo trực tiếp từ Khoa.",
        }
      : null
  );

  // Capability availability checks
  const unavailableCaps = [
    ...(props.unavailableCapabilities || []),
    ...(props.searchParams?.unavailable_capability ? String(props.searchParams.unavailable_capability).split(",") : []),
  ];
  const isChatUnavailable = unavailableCaps.includes("chat");
  const isRoomsUnavailable = unavailableCaps.includes("rooms");
  const isScheduleUnavailable = unavailableCaps.includes("schedule");
  const isTicketsUnavailable = unavailableCaps.includes("tickets");

  const isScheduleEmpty = props.searchParams?.empty_schedule === "true";
  const isTicketsEmpty = props.searchParams?.empty_tickets === "true";

  // Authoritative schedule item: never fabricate private data when unauthenticated
  const schedule: DashboardScheduleItem | null = !isAuthenticated
    ? null
    : props.schedule !== undefined
    ? props.schedule
    : isScheduleEmpty
    ? null
    : {
        id: "sched-next-01",
        courseName: "Lập trình Web nâng cao",
        courseCode: "IT3020",
        room: "Phòng 402-H1",
        timeSlot: "Tiết 3 - 5 (09:15 - 11:45)",
        lecturer: "TS. Nguyễn Văn A",
        syncTime: "Đồng bộ 07:00 hôm nay",
        source: "api-student-schedule",
      };

  // Authoritative ticket summaries: never fabricate private data when unauthenticated
  const tickets: DashboardTicketSummary[] = !isAuthenticated
    ? []
    : props.tickets !== undefined
    ? props.tickets
    : isTicketsEmpty
    ? []
    : [
        {
          id: "ticket-01",
          code: "TK-2026-01",
          title: "Xin cấp lại thẻ sinh viên",
          statusText: "Cần bạn bổ sung thông tin",
          updatedAt: "10:30 hôm nay",
          source: "api-student-tickets",
        },
      ];

  const quickActions = [
    {
      id: "chat",
      label: "Hỏi đáp trợ lý",
      href: "/chat",
      icon: <BotIcon size={16} />,
      disabled: isChatUnavailable,
      unauthorized: false,
    },
    {
      id: "schedule",
      label: "Lịch học của tôi",
      href: isAuthenticated ? "/schedule" : "/login?redirect=/schedule",
      icon: <CalendarIcon size={16} />,
      disabled: isScheduleUnavailable,
      unauthorized: !isAuthenticated,
    },
    {
      id: "tickets",
      label: "Yêu cầu một cửa",
      href: isAuthenticated ? "/tickets" : "/login?redirect=/tickets",
      icon: <ClipboardListIcon size={16} />,
      disabled: isTicketsUnavailable,
      unauthorized: !isAuthenticated,
    },
    {
      id: "rooms",
      label: "Tra cứu phòng trống",
      href: "/rooms",
      icon: <BuildingIcon size={16} />,
      disabled: isRoomsUnavailable,
      unauthorized: false,
    },
  ];

  return (
    <AppShell activeNav="home">
      <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        {/* Capability / Operational Health Banner */}
        {systemStatus && (
          <CapabilityBanner status={systemStatus} />
        )}

        {/* Header Notification & Academic Workspace Overview */}
        <section
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-xl, 16px)",
            padding: "28px 24px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 6px 20px -4px rgba(15,23,42,0.05))",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {/* Metadata Chips & Quick Utility Actions */}
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 10px",
                  borderRadius: "var(--radius-full, 9999px)",
                  backgroundColor: "#ecfdf5",
                  color: "#065f46",
                  fontSize: "12px",
                  fontWeight: 600,
                }}
              >
                <span
                  style={{
                    width: "7px",
                    height: "7px",
                    borderRadius: "50%",
                    backgroundColor: "#10b981",
                  }}
                />
                Trợ lý AI Campus 24/7
              </span>
              <span style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)", fontWeight: 500 }}>
                HUCE Demo — Môi trường thử nghiệm mô phỏng không chính thức
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <a
                href="/login"
                style={{
                  padding: "6px 14px",
                  borderRadius: "var(--radius-md, 8px)",
                  backgroundColor: "var(--color-primary, #1e3a8a)",
                  color: "#ffffff",
                  fontSize: "13px",
                  fontWeight: 600,
                  textDecoration: "none",
                }}
              >
                Đăng nhập
              </a>
              <a
                href="/privacy"
                style={{
                  padding: "6px 14px",
                  borderRadius: "var(--radius-md, 8px)",
                  backgroundColor: "var(--color-slate-100, #f1f5f9)",
                  color: "var(--color-slate-700, #334155)",
                  fontSize: "13px",
                  fontWeight: 500,
                  textDecoration: "none",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                }}
              >
                Xem trợ giúp
              </a>
            </div>
          </div>

          {/* Core Title */}
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "26px",
                fontWeight: 800,
                letterSpacing: "-0.5px",
                color: "var(--color-slate-900, #0f172a)",
                lineHeight: 1.3,
              }}
            >
              Không Gian Làm Việc Học Thuật & Một Cửa Số
            </h1>
            <p
              style={{
                margin: "8px 0 0 0",
                fontSize: "14px",
                color: "var(--color-slate-600, #475569)",
                maxWidth: "740px",
                lineHeight: 1.5,
              }}
            >
              Tra cứu quy chế đào tạo, theo dõi nhịp giảng đường và xử lý hồ sơ hành chính có trích dẫn văn bản chính thức.
            </p>
          </div>

          {/* Fast AI Search Bar */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <form
              action="/chat"
              method="GET"
              role="search"
              aria-label="Tìm kiếm quy chế và thủ tục học vụ"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                backgroundColor: isChatUnavailable ? "var(--color-slate-100, #f1f5f9)" : "var(--color-slate-50, #f8fafc)",
                padding: "8px 12px 8px 16px",
                borderRadius: "var(--radius-lg, 12px)",
                border: "1.5px solid var(--color-slate-200, #e2e8f0)",
                maxWidth: "760px",
                width: "100%",
                boxSizing: "border-box",
                opacity: isChatUnavailable ? 0.7 : 1,
              }}
            >
              <div style={{ color: "var(--color-slate-500, #64748b)", display: "flex", alignItems: "center" }}>
                <SearchIcon size={18} />
              </div>
              <input
                type="text"
                name="q"
                disabled={isChatUnavailable}
                aria-label="Hỏi Trợ lý AI về quy chế, tín chỉ, lịch thi"
                placeholder={
                  isChatUnavailable
                    ? "Tạm ngừng phục vụ: Trợ lý AI đang bảo trì..."
                    : "Hỏi Trợ lý AI về quy chế, tín chỉ, lịch thi (Ví dụ: 'Điều kiện xét học bổng?')..."
                }
                style={{
                  flex: 1,
                  border: "none",
                  background: "transparent",
                  fontSize: "14px",
                  color: isChatUnavailable ? "var(--color-slate-400, #94a3b8)" : "var(--color-slate-800, #1e293b)",
                  outline: "none",
                  cursor: isChatUnavailable ? "not-allowed" : "text",
                }}
              />
              <button
                type="submit"
                disabled={isChatUnavailable}
                aria-label={isChatUnavailable ? "Tạm ngừng phục vụ" : "Hỏi ngay"}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  backgroundColor: isChatUnavailable ? "var(--color-slate-400, #94a3b8)" : "var(--color-primary, #1e3a8a)",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "var(--radius-md, 8px)",
                  padding: "8px 16px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: isChatUnavailable ? "not-allowed" : "pointer",
                }}
              >
                <SparklesIcon size={15} />
                <span>{isChatUnavailable ? "Tạm ngừng phục vụ" : "Hỏi ngay"}</span>
              </button>
            </form>
            <span style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
              {isChatUnavailable
                ? "Dịch vụ Trợ lý AI đang tạm bảo trì để bảo đảm độ chính xác văn bản."
                : "Trợ lý AI hỗ trợ tra cứu; luôn đối chiếu văn bản quy chế trước khi thực hiện thủ tục."}
            </span>
          </div>

          {/* Quick Contextual Action Chips */}
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px", paddingTop: "4px" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-700, #334155)" }}>
              Lối tắt tác vụ:
            </span>
            {quickActions.map((action) => {
              if (action.disabled) {
                return (
                  <button
                    key={action.label}
                    type="button"
                    disabled
                    aria-disabled="true"
                    aria-label={action.label}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 12px",
                      borderRadius: "var(--radius-md, 8px)",
                      backgroundColor: "var(--color-slate-100, #f1f5f9)",
                      color: "var(--color-slate-400, #94a3b8)",
                      fontSize: "13px",
                      fontWeight: 500,
                      border: "1px dashed var(--color-slate-300, #cbd5e1)",
                      cursor: "not-allowed",
                      opacity: 0.7,
                    }}
                  >
                    {action.icon}
                    <span>{action.label}</span>
                    <span
                      style={{
                        fontSize: "10px",
                        padding: "1px 5px",
                        backgroundColor: "#fee2e2",
                        color: "#991b1b",
                        borderRadius: "4px",
                        fontWeight: 600,
                      }}
                    >
                      Tạm ngừng
                    </span>
                  </button>
                );
              }

              return (
                <a
                  key={action.label}
                  href={action.href}
                  aria-label={action.label}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 12px",
                    borderRadius: "var(--radius-md, 8px)",
                    backgroundColor: "var(--color-slate-100, #f1f5f9)",
                    color: "var(--color-slate-800, #1e293b)",
                    fontSize: "13px",
                    fontWeight: 500,
                    textDecoration: "none",
                    border: "1px solid var(--color-slate-200, #e2e8f0)",
                    transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                  }}
                >
                  {action.icon}
                  <span>{action.label}</span>
                  {action.unauthorized && (
                    <span
                      style={{
                        fontSize: "10px",
                        padding: "1px 5px",
                        backgroundColor: "#fef3c7",
                        color: "#92400e",
                        borderRadius: "4px",
                        fontWeight: 600,
                      }}
                    >
                      Cần đăng nhập
                    </span>
                  )}
                </a>
              );
            })}
          </div>
        </section>

        {/* Priority Split View: Time-Sensitive Schedule vs Open Requests */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "20px",
          }}
        >
          {/* Priority 1: Next Schedule Spotlight Card */}
          <section
            aria-labelledby="heading-next-schedule"
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg, 12px)",
              padding: "20px",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              gap: "16px",
              boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04))",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "8px",
                      backgroundColor: "#eff6ff",
                      color: "#1d4ed8",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <ClockIcon size={20} />
                  </div>
                  <div>
                    <h2 id="heading-next-schedule" style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                      Lịch học kế tiếp
                    </h2>
                    <span style={{ fontSize: "11px", color: "var(--color-slate-500, #64748b)" }}>
                      {!isAuthenticated
                        ? "Yêu cầu định danh sinh viên"
                        : schedule
                        ? schedule.syncTime
                        : "Thời gian thực"}
                    </span>
                  </div>
                </div>

                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    color: "#1d4ed8",
                    backgroundColor: "#dbeafe",
                    padding: "3px 8px",
                    borderRadius: "4px",
                  }}
                >
                  Thời khóa biểu
                </span>
              </div>

              {!isAuthenticated ? (
                <div style={{ padding: "20px", textAlign: "center", color: "var(--color-slate-600, #475569)", fontSize: "13px", backgroundColor: "var(--color-slate-50, #f8fafc)", borderRadius: "8px" }}>
                  <p style={{ margin: 0, fontWeight: 600 }}>Vui lòng đăng nhập để xem lịch học cá nhân.</p>
                  <p style={{ margin: "6px 0 0", fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
                    Lịch học và giảng đường chỉ hiển thị sau khi xác thực danh tính.
                  </p>
                </div>
              ) : schedule ? (
                <div style={{ backgroundColor: "var(--color-slate-50, #f8fafc)", padding: "14px", borderRadius: "8px", border: "1px solid var(--color-slate-200, #e2e8f0)" }}>
                  <div style={{ fontSize: "15px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                    {schedule.courseName} ({schedule.courseCode})
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "8px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", fontWeight: 600 }}>
                      <BuildingIcon size={14} /> {schedule.room}
                    </span>
                    <span>•</span>
                    <span>{schedule.timeSlot}</span>
                    <span>•</span>
                    <span>{schedule.lecturer}</span>
                  </div>
                </div>
              ) : (
                <div style={{ padding: "20px", textAlign: "center", color: "var(--color-slate-500, #64748b)", fontSize: "13px", backgroundColor: "var(--color-slate-50, #f8fafc)", borderRadius: "8px" }}>
                  Chưa có lịch học mới trong ca tiếp theo.
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <a
                href={isAuthenticated ? "/schedule" : "/login?redirect=/schedule"}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "var(--color-primary, #1e3a8a)",
                  textDecoration: "none",
                }}
              >
                <span>{isAuthenticated ? "Xem toàn bộ lịch" : "Đăng nhập để xem lịch"}</span>
                <ArrowRightIcon size={16} />
              </a>
            </div>
          </section>

          {/* Priority 2: Open Tickets Summary Card */}
          <section
            aria-labelledby="heading-open-tickets"
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "var(--radius-lg, 12px)",
              padding: "20px",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              gap: "16px",
              boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04))",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "8px",
                      backgroundColor: "#fffbeb",
                      color: "#b45309",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <ClipboardListIcon size={20} />
                  </div>
                  <div>
                    <h2 id="heading-open-tickets" style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                      Hồ sơ một cửa đang xử lý
                    </h2>
                    <span style={{ fontSize: "11px", color: "var(--color-slate-500, #64748b)" }}>
                      {!isAuthenticated ? "Yêu cầu định danh sinh viên" : "Tiến độ giải quyết thủ tục sinh viên"}
                    </span>
                  </div>
                </div>

                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    color: "#b45309",
                    backgroundColor: "#fef3c7",
                    padding: "3px 8px",
                    borderRadius: "4px",
                  }}
                >
                  Một cửa số
                </span>
              </div>

              {!isAuthenticated ? (
                <div style={{ padding: "20px", textAlign: "center", color: "var(--color-slate-600, #475569)", fontSize: "13px", backgroundColor: "var(--color-slate-50, #f8fafc)", borderRadius: "8px" }}>
                  <p style={{ margin: 0, fontWeight: 600 }}>Vui lòng đăng nhập để theo dõi hồ sơ một cửa.</p>
                  <p style={{ margin: "6px 0 0", fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
                    Thông tin tiến độ thủ tục được mã hóa và chỉ phục vụ chủ hồ sơ.
                  </p>
                </div>
              ) : tickets && tickets.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {tickets.map((ticket) => (
                    <div
                      key={ticket.id}
                      style={{
                        backgroundColor: "var(--color-slate-50, #f8fafc)",
                        padding: "12px",
                        borderRadius: "8px",
                        border: "1px solid var(--color-slate-200, #e2e8f0)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <div>
                        <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>
                          {ticket.title}
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)", marginTop: "2px" }}>
                          Mã: {ticket.code} • Cập nhật: {ticket.updatedAt}
                        </div>
                      </div>
                      <span
                        style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          padding: "3px 8px",
                          borderRadius: "4px",
                          backgroundColor: "#fef3c7",
                          color: "#92400e",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {ticket.statusText}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ padding: "20px", textAlign: "center", color: "var(--color-slate-500, #64748b)", fontSize: "13px", backgroundColor: "var(--color-slate-50, #f8fafc)", borderRadius: "8px" }}>
                  Không có hồ sơ nào đang chờ xử lý.
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <a
                href={isAuthenticated ? "/tickets" : "/login?redirect=/tickets"}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "var(--color-primary, #1e3a8a)",
                  textDecoration: "none",
                }}
              >
                <span>{isAuthenticated ? "Xem tất cả yêu cầu" : "Đăng nhập để xem hồ sơ"}</span>
                <ArrowRightIcon size={16} />
              </a>
            </div>
          </section>
        </div>

        {/* Institutional Trust & Privacy Safeguard Note */}
        <section
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-lg, 12px)",
            padding: "18px 20px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ color: "#065f46" }}>
              <ShieldCheckIcon size={20} />
            </div>
            <div style={{ fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
              <strong style={{ color: "var(--color-slate-800, #1e293b)" }}>Bảo đảm Pháp quy & Quyền riêng tư: </strong>
              Hệ thống xử lý dữ liệu tuân thủ Nghị định 13/2023/NĐ-CP. Mọi yêu cầu cấp giấy tờ đều được tạo bản nháp dự thảo trước khi xác nhận.
            </div>
          </div>
          <a
            href="/privacy"
            style={{
              fontSize: "12px",
              fontWeight: 600,
              color: "var(--color-primary, #1e3a8a)",
              textDecoration: "none",
              whiteSpace: "nowrap",
            }}
          >
            Chính sách quyền riêng tư
          </a>
        </section>
      </div>
    </AppShell>
  );
}
