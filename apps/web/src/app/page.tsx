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
  FileTextIcon,
  CheckCircle2Icon,
} from "../components/Icons";

export default function HomePage() {
  const serviceCards = [
    {
      title: "Hỏi đáp AI 24/7",
      href: "/chat",
      icon: <BotIcon size={24} />,
      iconBg: "#eff6ff",
      iconColor: "#1d4ed8",
      badge: "AI Hỗ trợ",
      badgeColor: "#1d4ed8",
      badgeBg: "#eff6ff",
      description: "Tra cứu quy chế đào tạo, tín chỉ, chuẩn đầu ra và thủ tục hành chính có dẫn nguồn văn bản nhà trường.",
      cta: "Bắt đầu cuộc trò chuyện",
    },
    {
      title: "Thời khóa biểu & Lịch thi",
      href: "/schedule",
      icon: <CalendarIcon size={24} />,
      iconBg: "#f0fdfa",
      iconColor: "#0f766e",
      badge: "Đồng bộ tự động",
      badgeColor: "#0f766e",
      badgeBg: "#f0fdfa",
      description: "Theo dõi lịch học trong tuần, phòng học thời gian thực và lịch thi kết thúc học phần chính xác.",
      cta: "Xem lịch của tôi",
    },
    {
      title: "Thủ tục & Một cửa số",
      href: "/tickets",
      icon: <ClipboardListIcon size={24} />,
      iconBg: "#fffbeb",
      iconColor: "#b45309",
      badge: "Dịch vụ hành chính",
      badgeColor: "#b45309",
      badgeBg: "#fffbeb",
      description: "Đăng ký xin cấp giấy xác nhận sinh viên, bảng điểm tạm thời và theo dõi tiến trình phê duyệt hồ sơ.",
      cta: "Quản lý yêu cầu",
    },
    {
      title: "Đăng ký mượn phòng",
      href: "/rooms",
      icon: <BuildingIcon size={24} />,
      iconBg: "#f5f3ff",
      iconColor: "#6d28d9",
      badge: "Tiện ích cơ sở",
      badgeColor: "#6d28d9",
      badgeBg: "#f5f3ff",
      description: "Tra cứu phòng học còn trống, phòng tự học cá nhân hoặc đăng ký phòng sinh hoạt câu lạc bộ sinh viên.",
      cta: "Tra cứu phòng trống",
    },
  ];

  const quickPrompts = [
    { label: "Điều kiện xét học bổng", href: "/chat?q=Điều kiện xét học bổng" },
    { label: "Thủ tục xin cấp bảng điểm", href: "/chat?q=Thủ tục xin cấp bảng điểm" },
    { label: "Quy chế hoãn thi học kỳ", href: "/chat?q=Quy chế hoãn thi học kỳ" },
    { label: "Phòng tự học mở cửa hôm nay", href: "/rooms" },
  ];

  const administrativeSteps = [
    {
      step: 1,
      title: "Chọn thủ tục & điền thông tin:",
      desc: "Chọn mẫu đơn trực tuyến (bảng điểm, xác nhận sinh viên) trong mục Thủ tục & Yêu cầu.",
      bg: "#eff6ff",
      color: "#1d4ed8",
    },
    {
      step: 2,
      title: "Kiểm tra bản xem trước & xác nhận:",
      desc: "Hệ thống tạo bản nháp có đóng dấu dự thảo để sinh viên rà soát tính chính xác trước khi gửi.",
      bg: "#eff6ff",
      color: "#1d4ed8",
    },
    {
      step: 3,
      title: "Nhận mã hẹn & kết quả ký số:",
      desc: "Theo dõi tiến độ duyệt hồ sơ của cán bộ phòng Đào tạo và nhận kết quả tại cổng một cửa.",
      bg: "#ecfdf5",
      color: "#065f46",
    },
  ];

  return (
    <AppShell activeNav="home">
      <div style={{ display: "flex", flexDirection: "column", gap: "36px" }}>
        {/* Modern Academic Workspace Hero Section */}
        <section
          style={{
            position: "relative",
            overflow: "hidden",
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-xl, 20px)",
            padding: "40px 36px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
            display: "flex",
            flexDirection: "column",
            gap: "24px",
          }}
        >
          {/* Header Metadata Chips & Landing Primary Actions (UX-SCR-001) */}
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "4px 12px",
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
                    boxShadow: "0 0 0 3px rgba(16, 185, 129, 0.2)",
                  }}
                />
                Trợ lý AI Campus 24/7
              </span>
              <span style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)", fontWeight: 500 }}>
                HUCE Demo — Môi trường thử nghiệm mô phỏng không chính thức
              </span>
            </div>

            {/* Primary Actions for UX-SCR-001 Landing: Đăng nhập & Xem trợ giúp */}
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <a
                href="/login"
                style={{
                  padding: "6px 14px",
                  borderRadius: "var(--radius-md, 10px)",
                  backgroundColor: "var(--color-primary, #1e3a8a)",
                  color: "#ffffff",
                  fontSize: "13px",
                  fontWeight: 600,
                  textDecoration: "none",
                  transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                }}
              >
                Đăng nhập
              </a>
              <a
                href="/privacy"
                style={{
                  padding: "6px 14px",
                  borderRadius: "var(--radius-md, 10px)",
                  backgroundColor: "var(--color-slate-100, #f1f5f9)",
                  color: "var(--color-slate-700, #334155)",
                  fontSize: "13px",
                  fontWeight: 500,
                  textDecoration: "none",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                }}
              >
                Xem trợ giúp
              </a>
            </div>
          </div>

          {/* Core Headline */}
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "32px",
                fontWeight: 800,
                letterSpacing: "-0.7px",
                color: "var(--color-slate-900, #0f172a)",
                lineHeight: 1.25,
              }}
            >
              Không Gian Làm Việc Học Thuật & Một Cửa Số
            </h1>
            <p
              style={{
                margin: "12px 0 0 0",
                fontSize: "15px",
                color: "var(--color-slate-600, #475569)",
                maxWidth: "780px",
                lineHeight: 1.6,
              }}
            >
              Nền tảng hỗ trợ sinh viên và cán bộ Trường Đại học Xây dựng Hà Nội tra cứu quy chế,
              lịch trình giảng đường và xử lý hồ sơ hành chính có trích dẫn nguồn văn bản chính thức.
            </p>
          </div>

          {/* Fast AI Ask Bar (Information Foraging Theory & UX-A11Y-010) */}
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
                backgroundColor: "var(--color-slate-50, #f8fafc)",
                padding: "8px 12px 8px 16px",
                borderRadius: "var(--radius-lg, 14px)",
                border: "1.5px solid var(--color-slate-200, #e2e8f0)",
                maxWidth: "800px",
                width: "100%",
                boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
              }}
            >
              <div style={{ color: "var(--color-slate-500, #64748b)", display: "flex", alignItems: "center" }}>
                <SearchIcon size={20} />
              </div>
              <input
                type="text"
                name="q"
                aria-label="Hỏi Trợ lý AI về quy chế, tín chỉ, lịch thi"
                placeholder="Hỏi Trợ lý AI về quy chế, tín chỉ, lịch thi (Ví dụ: 'Điều kiện xét học bổng kỳ 1?')..."
                style={{
                  flex: 1,
                  border: "none",
                  background: "transparent",
                  fontSize: "14px",
                  color: "var(--color-slate-800, #1e293b)",
                }}
              />
              <button
                type="submit"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  backgroundColor: "var(--color-primary, #1e3a8a)",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "var(--radius-md, 10px)",
                  padding: "8px 18px",
                  fontSize: "13px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                }}
              >
                <SparklesIcon size={16} />
                <span>Hỏi ngay</span>
              </button>
            </form>
            <span style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)", fontStyle: "italic" }}>
              Trợ lý AI có thể mắc lỗi; luôn đối chiếu nguồn trích dẫn quy chế trước khi ra quyết định học vụ (UX-TRUST-001).
            </span>
          </div>

          {/* Contextual Suggestion Pills */}
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)", fontWeight: 500 }}>
              Gợi ý nhanh:
            </span>
            {quickPrompts.map((prompt) => (
              <a
                key={prompt.label}
                href={prompt.href}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  padding: "4px 10px",
                  borderRadius: "var(--radius-full, 9999px)",
                  backgroundColor: "var(--color-slate-100, #f1f5f9)",
                  color: "var(--color-slate-700, #334155)",
                  fontSize: "12px",
                  fontWeight: 500,
                  textDecoration: "none",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                }}
              >
                {prompt.label}
              </a>
            ))}
          </div>
        </section>

        {/* Next Class Spotlight Card (Preattentive Visual Cue & Provenance Label) */}
        <section
          style={{
            backgroundColor: "#ffffff",
            borderRadius: "var(--radius-lg, 14px)",
            padding: "20px 24px",
            border: "1px solid var(--color-primary-border, #bfdbfe)",
            boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "16px",
            background: "linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%)",
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
                  Lịch học minh họa
                </span>
                <span style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
                  Dữ liệu lịch học mô phỏng • Đồng bộ 07:00 hôm nay
                </span>
              </div>
              <h2 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                Lập trình Web nâng cao (IT3020) — Nhóm 02
              </h2>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "4px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                  <BuildingIcon size={14} /> Phòng 402-H1
                </span>
                <span>•</span>
                <span>Tiết 3 - 5 (09:15 - 11:45)</span>
                <span>•</span>
                <span>TS. Nguyễn Văn A</span>
              </div>
            </div>
          </div>

          <a
            href="/schedule"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "10px 18px",
              borderRadius: "var(--radius-md, 10px)",
              backgroundColor: "var(--color-primary, #1e3a8a)",
              color: "#ffffff",
              fontSize: "13px",
              fontWeight: 600,
              textDecoration: "none",
              whiteSpace: "nowrap",
              transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
            }}
          >
            <span>Thời khóa biểu đầy đủ</span>
            <ArrowRightIcon size={16} />
          </a>
        </section>

        {/* 4 Core Pillars Grid (Gestalt Common Region) */}
        <section>
          <div style={{ marginBottom: "18px" }}>
            <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}>
              Trụ cột dịch vụ số
            </h2>
            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
              Truy cập nhanh các phân hệ chuyên trách phục vụ học tập và thủ tục sinh viên
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: "20px",
            }}
          >
            {serviceCards.map((card) => (
              <a
                key={card.title}
                href={card.href}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  backgroundColor: "#ffffff",
                  borderRadius: "var(--radius-lg, 14px)",
                  padding: "24px",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                  textDecoration: "none",
                  color: "inherit",
                  boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
                  transition: "var(--transition-spring, 220ms cubic-bezier(0.16, 1, 0.3, 1))",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
                    <div
                      style={{
                        width: "44px",
                        height: "44px",
                        borderRadius: "var(--radius-md, 10px)",
                        backgroundColor: card.iconBg,
                        color: card.iconColor,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {card.icon}
                    </div>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 600,
                        padding: "3px 9px",
                        borderRadius: "var(--radius-full, 9999px)",
                        backgroundColor: card.badgeBg,
                        color: card.badgeColor,
                      }}
                    >
                      {card.badge}
                    </span>
                  </div>

                  <h3 style={{ margin: "0 0 8px 0", fontSize: "17px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                    {card.title}
                  </h3>

                  <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-600, #475569)", lineHeight: 1.6 }}>
                    {card.description}
                  </p>
                </div>

                <div
                  style={{
                    marginTop: "24px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "var(--color-primary, #1e3a8a)",
                  }}
                >
                  <span>{card.cta}</span>
                  <ArrowRightIcon size={16} />
                </div>
              </a>
            ))}
          </div>
        </section>

        {/* Administrative Guidance & Institutional Trust */}
        <section>
          <div style={{ marginBottom: "18px" }}>
            <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}>
              Quy chuẩn Một cửa & Bảo đảm Học thuật
            </h2>
            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
              Quy trình giải quyết hồ sơ minh bạch và bảo đảm pháp quy theo chuẩn nhà trường
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
              gap: "20px",
            }}
          >
            {/* Box 1: Multi-Step Stepper Guidance (Zeigarnik Effect - DRY refactored) */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "var(--radius-lg, 14px)",
                padding: "24px",
                border: "1px solid var(--color-slate-200, #e2e8f0)",
                boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
                <div style={{ color: "var(--color-primary, #1e3a8a)" }}>
                  <FileTextIcon size={20} />
                </div>
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                  Quy trình Nộp hồ sơ Một cửa số 3 bước
                </h3>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {administrativeSteps.map((item) => (
                  <div key={item.step} style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
                    <span
                      style={{
                        width: "22px",
                        height: "22px",
                        borderRadius: "50%",
                        backgroundColor: item.bg,
                        color: item.color,
                        fontSize: "12px",
                        fontWeight: 700,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      {item.step}
                    </span>
                    <div>
                      <strong style={{ fontSize: "13px", color: "var(--color-slate-800, #1e293b)" }}>
                        {item.title}
                      </strong>
                      <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
                        {item.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Box 2: Institutional Authority & Privacy Safeguard (UX-TRUST-001) */}
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "var(--radius-lg, 14px)",
                padding: "24px",
                border: "1px solid var(--color-slate-200, #e2e8f0)",
                boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
                  <div style={{ color: "#065f46" }}>
                    <ShieldCheckIcon size={20} />
                  </div>
                  <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                    Bảo đảm Pháp quy & Trách nhiệm AI
                  </h3>
                </div>

                <p style={{ margin: "0 0 16px 0", fontSize: "13px", color: "var(--color-slate-600, #475569)", lineHeight: 1.6 }}>
                  Đây là trợ lý AI trong môi trường mô phỏng HUCE Demo, không phải kênh chính thức của Trường Đại học Xây dựng Hà Nội.
                  Hãy kiểm tra nguồn trích dẫn trước khi thực hiện thủ tục. Bạn luôn có thể chuyển yêu cầu tới cán bộ phụ trách.
                </p>

                <div
                  style={{
                    backgroundColor: "var(--color-slate-50, #f8fafc)",
                    borderRadius: "var(--radius-md, 10px)",
                    padding: "12px 16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    fontSize: "13px",
                  }}
                >
                  <span style={{ color: "var(--color-slate-700, #334155)", fontWeight: 600 }}>
                    Trợ lý AI Campus 24/7 — Môi trường thử nghiệm
                  </span>
                  <span style={{ color: "var(--color-slate-600, #475569)", fontSize: "12px" }}>
                    Dữ liệu mô phỏng tổng hợp • Tuân thủ Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân
                  </span>
                </div>
              </div>

              <div style={{ marginTop: "18px", display: "flex", alignItems: "center", gap: "6px" }}>
                <CheckCircle2Icon size={16} style={{ color: "#10b981" }} />
                <span style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
                  Tuân thủ chuẩn tiếp cận WCAG 2.2 AA & UX-TRUST-001
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
