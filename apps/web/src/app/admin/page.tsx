"use client";

import React, { useState } from "react";
import { AppShell } from "../../components/AppShell";

interface SlaConfigItem {
  id: string;
  name: string;
  department: string;
  currentHours: number;
}

interface AuditLogItem {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  targetId: string;
  details: string;
}

export default function AdminDashboardPage() {
  const [slaConfigs, setSlaConfigs] = useState<SlaConfigItem[]>([
    { id: "xac_nhan_sv", name: "Giấy xác nhận sinh viên", department: "Phòng CTSV", currentHours: 24 },
    { id: "bang_diem", name: "Bảng điểm tạm thời", department: "Phòng Quản lý Đào tạo", currentHours: 48 },
    { id: "gioi_thieu_tt", name: "Giấy giới thiệu thực tập", department: "Khoa CNTT", currentHours: 24 },
    { id: "hoan_nvqs", name: "Giấy xác nhận tạm hoãn NVQS", department: "Phòng CTSV", currentHours: 24 },
  ]);

  const [editingSlaId, setEditingSlaId] = useState<string | null>(null);
  const [newSlaHours, setNewSlaHours] = useState<number>(24);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([
    {
      id: "log-001",
      timestamp: "2026-09-26 16:45:10",
      actor: "staff-huce-01",
      action: "CLAIM_TICKET",
      targetId: "TCK-2026-0101",
      details: "Tiếp nhận hồ sơ xin miễn giảm học phí",
    },
    {
      id: "log-002",
      timestamp: "2026-09-26 16:30:22",
      actor: "system-auto",
      action: "AI_TRIAGE_CHECK",
      targetId: "TCK-2026-0102",
      details: "Kiểm tra trùng lặp và đề xuất phân loại",
    },
    {
      id: "log-003",
      timestamp: "2026-09-26 15:10:05",
      actor: "admin-huce-01",
      action: "UPDATE_SLA",
      targetId: "CONFIG-SLA-01",
      details: "Điều chỉnh SLA cấp bảng điểm từ 72h xuống 48h",
    },
  ]);

  const handleEditSla = (item: SlaConfigItem) => {
    setEditingSlaId(item.id);
    setNewSlaHours(item.currentHours);
  };

  const handleSaveSla = (id: string) => {
    const config = slaConfigs.find((c) => c.id === id);
    const oldHours = config?.currentHours;
    setSlaConfigs((prev) =>
      prev.map((c) => (c.id === id ? { ...c, currentHours: Number(newSlaHours) } : c))
    );
    // Auto-log SLA change to audit trail
    if (config && oldHours !== Number(newSlaHours)) {
      const newLog: AuditLogItem = {
        id: `log-${Date.now()}`,
        timestamp: new Date().toLocaleString("vi-VN"),
        actor: "admin-huce-01",
        action: "UPDATE_SLA",
        targetId: `CONFIG-${id}`,
        details: `Đổi SLA "${config.name}" từ ${oldHours}h → ${newSlaHours}h`,
      };
      setAuditLogs((prev) => [newLog, ...prev]);
    }
    setEditingSlaId(null);
  };

  const handleExportAudit = () => {
    const csvContent =
      "data:text/csv;charset=utf-8,ID,Timestamp,Actor,Action,Target,Details\n" +
      auditLogs
        .map((l) => `${l.id},${l.timestamp},${l.actor},${l.action},${l.targetId},"${l.details}"`)
        .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `audit_log_campus247_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setExportNotice("Đã xuất thành công tệp kiểm toán CSV!");
    setTimeout(() => setExportNotice(null), 4000);
  };

  return (
    <AppShell activeNav="admin" userRole="admin">
      <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "1140px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h1 style={{ margin: "0 0 6px 0", fontSize: "24px", fontWeight: 800, color: "var(--color-slate-900, #0f172a)" }}>
              Bảng điều khiển Quản trị Một cửa số (Admin Ops)
            </h1>
            <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)" }}>
              Giám sát chất lượng tiếp nhận, cấu hình cam kết SLA và kiểm toán tuân thủ toàn trường
            </p>
          </div>

          <button
            type="button"
            onClick={handleExportAudit}
            style={{
              padding: "10px 18px",
              borderRadius: "8px",
              border: "1px solid var(--color-slate-300, #cbd5e1)",
              backgroundColor: "#ffffff",
              color: "var(--color-slate-800, #1e293b)",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "var(--shadow-xs)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>📥</span>
            <span>Xuất dữ liệu kiểm toán</span>
          </button>
        </div>

        {exportNotice && (
          <div
            role="status"
            style={{
              padding: "10px 16px",
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "8px",
              color: "#166534",
              fontSize: "13px",
              fontWeight: 600,
            }}
          >
            {exportNotice}
          </div>
        )}

        {/* Operational KPI Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "16px",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              padding: "20px",
              borderRadius: "14px",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Tổng hồ sơ tiếp nhận
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-slate-900, #0f172a)", marginTop: "6px" }}>
              1,248
            </div>
            <div style={{ fontSize: "12px", color: "#16a34a", marginTop: "4px", fontWeight: 600 }}>
              ↑ +12.4% so với tuần trước
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#ffffff",
              padding: "20px",
              borderRadius: "14px",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Tỷ lệ đúng hạn SLA
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#1e3a8a", marginTop: "6px" }}>
              98.5%
            </div>
            <div style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)", marginTop: "4px" }}>
              Cam kết dịch vụ vượt chỉ tiêu 95%
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#ffffff",
              padding: "20px",
              borderRadius: "14px",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Hồ sơ đang tồn đọng
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#d97706", marginTop: "6px" }}>
              14
            </div>
            <div style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)", marginTop: "4px" }}>
              0 ca quá hạn thời gian cam kết
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#ffffff",
              padding: "20px",
              borderRadius: "14px",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Mức độ hài lòng CSAT
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#16a34a", marginTop: "6px" }}>
              4.85 / 5
            </div>
            <div style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)", marginTop: "4px" }}>
              Dựa trên 412 lượt đánh giá sinh viên
            </div>
          </div>
        </div>

        {/* SLA Configuration Table */}
        <section
          style={{
            backgroundColor: "#ffffff",
            padding: "24px",
            borderRadius: "14px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            boxShadow: "var(--shadow-xs)",
          }}
        >
          <div style={{ marginBottom: "16px" }}>
            <h2 style={{ margin: "0 0 4px 0", fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
              Cấu hình cam kết thời hạn xử lý (SLA)
            </h2>
            <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-500, #64748b)" }}>
              Thiết lập thời gian phản hồi và xử lý tối đa theo từng loại hồ sơ Một cửa số
            </p>
          </div>

          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
            <thead>
              <tr style={{ backgroundColor: "var(--color-slate-50, #f8fafc)", borderBottom: "1px solid var(--color-slate-200, #e2e8f0)", color: "var(--color-slate-600, #475569)" }}>
                <th style={{ padding: "12px 16px" }}>Loại giấy tờ / Thủ tục</th>
                <th style={{ padding: "12px 16px" }}>Đơn vị phụ trách</th>
                <th style={{ padding: "12px 16px" }}>Thời hạn cam kết SLA</th>
                <th style={{ padding: "12px 16px" }}>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {slaConfigs.map((config) => {
                const isEditing = editingSlaId === config.id;
                return (
                  <tr key={config.id} style={{ borderBottom: "1px solid var(--color-slate-100, #f1f5f9)" }}>
                    <td style={{ padding: "14px 16px", fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>
                      {config.name}
                    </td>
                    <td style={{ padding: "14px 16px", color: "var(--color-slate-600, #475569)" }}>
                      {config.department}
                    </td>
                    <td style={{ padding: "14px 16px" }}>
                      {isEditing ? (
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <label htmlFor={`sla-input-${config.id}`} style={{ display: "none" }}>
                            Thời hạn SLA mới (giờ)
                          </label>
                          <input
                            id={`sla-input-${config.id}`}
                            type="number"
                            min={1}
                            max={168}
                            value={newSlaHours}
                            onChange={(e) => setNewSlaHours(Number(e.target.value))}
                            style={{
                              width: "70px",
                              padding: "4px 8px",
                              borderRadius: "4px",
                              border: "1px solid #cbd5e1",
                              fontSize: "13px",
                            }}
                          />
                          <span>giờ</span>
                        </div>
                      ) : (
                        <span
                          style={{
                            fontWeight: 700,
                            color: "var(--color-primary, #1e3a8a)",
                            backgroundColor: "var(--color-primary-light, #eff6ff)",
                            padding: "3px 10px",
                            borderRadius: "9999px",
                          }}
                        >
                          {config.currentHours} giờ
                        </span>
                      )}
                    </td>
                    <td style={{ padding: "14px 16px" }}>
                      {isEditing ? (
                        <div style={{ display: "flex", gap: "6px" }}>
                          <button
                            type="button"
                            onClick={() => handleSaveSla(config.id)}
                            style={{
                              padding: "4px 12px",
                              borderRadius: "6px",
                              border: "none",
                              backgroundColor: "var(--color-primary, #1e3a8a)",
                              color: "#ffffff",
                              fontSize: "12px",
                              fontWeight: 600,
                              cursor: "pointer",
                            }}
                          >
                            Lưu cấu hình SLA
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditingSlaId(null)}
                            style={{
                              padding: "4px 10px",
                              borderRadius: "6px",
                              border: "1px solid #cbd5e1",
                              backgroundColor: "#ffffff",
                              fontSize: "12px",
                              cursor: "pointer",
                            }}
                          >
                            Hủy
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleEditSla(config)}
                          aria-label={`Chỉnh sửa SLA ${config.name}`}
                          style={{
                            padding: "4px 12px",
                            borderRadius: "6px",
                            border: "1px solid var(--color-slate-300, #cbd5e1)",
                            backgroundColor: "#ffffff",
                            color: "var(--color-slate-700, #334155)",
                            fontSize: "12px",
                            fontWeight: 600,
                            cursor: "pointer",
                          }}
                        >
                          Chỉnh sửa
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>

        {/* Audit Log Section */}
        <section
          style={{
            backgroundColor: "#ffffff",
            padding: "24px",
            borderRadius: "14px",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            boxShadow: "var(--shadow-xs)",
          }}
        >
          <div style={{ marginBottom: "16px" }}>
            <h2 style={{ margin: "0 0 4px 0", fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
              Nhật ký kiểm toán Một cửa số (Audit Trail)
            </h2>
            <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-500, #64748b)" }}>
              Ghi nhận bất biến mọi tác vụ nghiệp vụ, phân quyền và can thiệp thủ tục của cán bộ
            </p>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
              <thead>
                <tr style={{ backgroundColor: "var(--color-slate-50, #f8fafc)", borderBottom: "1px solid var(--color-slate-200, #e2e8f0)", color: "var(--color-slate-600, #475569)" }}>
                  <th style={{ padding: "10px 14px" }}>Thời gian</th>
                  <th style={{ padding: "10px 14px" }}>Người thực hiện (Actor)</th>
                  <th style={{ padding: "10px 14px" }}>Hành động</th>
                  <th style={{ padding: "10px 14px" }}>Mã đối tượng</th>
                  <th style={{ padding: "10px 14px" }}>Chi tiết tác vụ</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: "1px solid var(--color-slate-100, #f1f5f9)" }}>
                    <td style={{ padding: "12px 14px", color: "var(--color-slate-500, #64748b)", fontFamily: "monospace", fontSize: "12px" }}>
                      {log.timestamp}
                    </td>
                    <td style={{ padding: "12px 14px", fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>
                      {log.actor}
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span
                        style={{
                          fontSize: "11px",
                          fontFamily: "monospace",
                          fontWeight: 700,
                          backgroundColor: "var(--color-slate-100, #f1f5f9)",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          color: "var(--color-slate-700, #334155)",
                        }}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td style={{ padding: "12px 14px", color: "var(--color-primary, #1e3a8a)", fontWeight: 600 }}>
                      {log.targetId}
                    </td>
                    <td style={{ padding: "12px 14px", color: "var(--color-slate-700, #334155)" }}>
                      {log.details}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
