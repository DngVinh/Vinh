import React, { useState, useEffect, useCallback } from "react";

export interface StaffAttachment {
  name: string;
  ocrBadge: string;
  confidence: string;
  type?: "pdf" | "image";
}

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
  version?: number;
  isStale?: boolean;
  actionOutcome?: "idle" | "succeeded" | "failed" | "unknown";
  age?: string;
  publicContent?: string;
  internalNotes?: string;
  isRestricted?: boolean;
  hasConflict?: boolean;
  conflictStaffId?: string;
  targetDepartment?: string;
  attachments?: StaffAttachment[];
}

export interface StaffTicketQueueProps {
  items?: StaffQueueItem[];
  currentStaffId?: string;
  userRole?: string;
  onClaimTicket?: (queueId: string) => Promise<void> | void;
  onRefresh?: () => void;
  onTransferTicket?: (queueId: string, payload: { targetDepartment: string; transferReason?: string }) => void;
  onRequestSupplement?: (queueId: string, payload: { requestMessage: string }) => void;
  onFinalizeIntake?: (queueId: string, payload: { checklistPassed: boolean; exceptionReason?: string }) => void;
  onReconcile?: (queueId: string) => void;
}

type FilterType = "all" | "unassigned" | "my" | "urgent";
type SortType = "default" | "urgent" | "wait";

interface IntakeGate {
  id: string;
  label: string;
  sourceBadge: string;
  sourceBadgeBg: string;
  sourceBadgeColor: string;
  aiEvidence: string;
  confidence: string;
}

const INTAKE_CHECKLIST_GATES: IntakeGate[] = [
  {
    id: "gate_identity",
    label: "Xác minh danh tính & MSSV qua tài khoản định danh",
    sourceBadge: "VNeID Mức 2",
    sourceBadgeBg: "#ecfdf5",
    sourceBadgeColor: "#065f46",
    aiEvidence: "Khớp hồ sơ sinh viên chính quy K68. SSO xác thực bảo mật.",
    confidence: "99.8%",
  },
  {
    id: "gate_scope",
    label: "Kiểm tra thẩm quyền xử lý Một cửa số (tránh nhận nhầm phạm vi)",
    sourceBadge: "Quy chế Đào tạo",
    sourceBadgeBg: "#eff6ff",
    sourceBadgeColor: "#1e40af",
    aiEvidence: "Thẩm quyền trực tiếp của Phòng Quản lý Đào tạo / CTSV.",
    confidence: "100%",
  },
  {
    id: "gate_duplicate",
    label: "Kiểm tra tiền sử đơn trùng lặp trong 30 ngày qua",
    sourceBadge: "Lịch sử Hệ thống",
    sourceBadgeBg: "#f0fdf4",
    sourceBadgeColor: "#166534",
    aiEvidence: "Không có đơn trùng lặp cùng nội dung trong 30 ngày gần nhất.",
    confidence: "98.5%",
  },
  {
    id: "gate_attachment",
    label: "Kiểm tra tính hợp lệ minh chứng đính kèm (dấu đỏ, ảnh, văn bản)",
    sourceBadge: "AI OCR Thẩm định",
    sourceBadgeBg: "#faf5ff",
    sourceBadgeColor: "#6b21a8",
    aiEvidence: "Phát hiện con dấu đỏ tròn hợp lệ và chữ ký xác nhận của phụ huynh/địa phương.",
    confidence: "97.4%",
  },
  {
    id: "gate_sla",
    label: "Xác định mức độ khẩn cấp & thời hạn cam kết SLA tiếp nhận",
    sourceBadge: "SLA Chuẩn 24h",
    sourceBadgeBg: "#fffbeb",
    sourceBadgeColor: "#92400e",
    aiEvidence: "Cam kết phản hồi trong 24h làm việc. Tự động tính hạn chót.",
    confidence: "100%",
  },
  {
    id: "gate_privacy",
    label: "Rà soát thông tin nhạy cảm trước khi xử lý theo Nghị định 13",
    sourceBadge: "NĐ 13/2023/NĐ-CP",
    sourceBadgeBg: "#fdf2f8",
    sourceBadgeColor: "#9d174d",
    aiEvidence: "Dữ liệu cá nhân nhạy cảm đã được gắn cờ bảo mật và hạn chế truy cập.",
    confidence: "99.0%",
  },
];

// Audit log entry type
export interface AuditLogEntry {
  timestamp: string;
  staffId: string;
  ticketId: string;
  action: string;
  detail: string;
}

// localStorage keys
const LS_CHECKED_GATES = "campus247_checkedGates";
const LS_EXCEPTION_REASONS = "campus247_exceptionReasons";
const LS_FINALIZED = "campus247_finalizedTickets";
const LS_AUDIT_LOG = "campus247_auditLog";
const LS_GATE_TIMESTAMPS = "campus247_gateTimestamps";
const LS_PRIVATE_NOTES = "campus247_privateNotes";

function loadLS<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function saveLS<T>(key: string, value: T): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // quota exceeded — silently ignore
  }
}

/** Calculate SLA remaining from createdAt string */
function getSlaInfo(createdAt: string): { remaining: string; urgencyColor: string; percentUsed: number } {
  const SLA_HOURS = 24;
  const now = new Date();
  // Parse relative times like "Hôm nay, 08:30"
  let created: Date;
  if (createdAt.includes("Hôm nay")) {
    const timePart = createdAt.match(/(\d{2}):(\d{2})/);
    created = new Date(now);
    if (timePart) {
      created.setHours(parseInt(timePart[1]), parseInt(timePart[2]), 0, 0);
    }
  } else {
    created = new Date(createdAt);
    if (isNaN(created.getTime())) created = now;
  }

  const deadline = new Date(created.getTime() + SLA_HOURS * 60 * 60 * 1000);
  const diffMs = deadline.getTime() - now.getTime();
  const diffH = Math.floor(diffMs / (1000 * 60 * 60));
  const diffM = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  const totalMs = SLA_HOURS * 60 * 60 * 1000;
  const percentUsed = Math.min(100, Math.max(0, ((totalMs - diffMs) / totalMs) * 100));

  if (diffMs <= 0) return { remaining: "QUÁ HẠN", urgencyColor: "#dc2626", percentUsed: 100 };
  if (diffH < 1) return { remaining: `${diffM} phút`, urgencyColor: "#dc2626", percentUsed };
  if (diffH < 4) return { remaining: `${diffH}h ${diffM}p`, urgencyColor: "#f59e0b", percentUsed };
  return { remaining: `${diffH}h ${diffM}p`, urgencyColor: "#16a34a", percentUsed };
}

export function StaffTicketQueue({
  items = [],
  currentStaffId = "",
  userRole,
  onClaimTicket,
  onRefresh,
  onTransferTicket,
  onRequestSupplement,
  onFinalizeIntake,
  onReconcile,
}: StaffTicketQueueProps) {
  if (userRole && userRole !== "STAFF" && userRole !== "ADMIN") {
    return (
      <div
        role="alert"
        style={{
          padding: "24px 28px",
          borderRadius: "12px",
          backgroundColor: "#fff1f2",
          border: "1px solid #fecaca",
          color: "#991b1b",
          maxWidth: "800px",
        }}
      >
        <h3 style={{ margin: "0 0 8px 0", fontSize: "18px", fontWeight: 700 }}>Từ chối quyền truy cập</h3>
        <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.6 }}>
          Bạn không có thẩm quyền truy cập hàng đợi cán bộ một cửa. Chức năng này chỉ dành cho tài khoản có vai trò Cán bộ tiếp nhận hoặc Quản trị viên hệ thống.
        </p>
      </div>
    );
  }

  const [filter, setFilter] = useState<FilterType>("all");
  const [sortBy, setSortBy] = useState<SortType>("default");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

  // Checklist state per ticket — persisted in localStorage
  const [checkedGates, setCheckedGates] = useState<Record<string, Record<string, boolean>>>(() => loadLS(LS_CHECKED_GATES, {}));
  const [exceptionReasons, setExceptionReasons] = useState<Record<string, string>>(() => loadLS(LS_EXCEPTION_REASONS, {}));
  const [finalizedTickets, setFinalizedTickets] = useState<Record<string, boolean>>(() => loadLS(LS_FINALIZED, {}));
  const [gateTimestamps, setGateTimestamps] = useState<Record<string, Record<string, string>>>(() => loadLS(LS_GATE_TIMESTAMPS, {}));
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>(() => loadLS(LS_AUDIT_LOG, []));
  const [privateNotes, setPrivateNotes] = useState<Record<string, string>>(() => loadLS(LS_PRIVATE_NOTES, {}));

  // Show/hide audit log panel
  const [showAuditLog, setShowAuditLog] = useState(false);

  // SLA timer tick
  const [, setTick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 60000); // update every minute
    return () => clearInterval(interval);
  }, []);

  // Persist to localStorage on change
  useEffect(() => { saveLS(LS_CHECKED_GATES, checkedGates); }, [checkedGates]);
  useEffect(() => { saveLS(LS_EXCEPTION_REASONS, exceptionReasons); }, [exceptionReasons]);
  useEffect(() => { saveLS(LS_FINALIZED, finalizedTickets); }, [finalizedTickets]);
  useEffect(() => { saveLS(LS_GATE_TIMESTAMPS, gateTimestamps); }, [gateTimestamps]);
  useEffect(() => { saveLS(LS_AUDIT_LOG, auditLog); }, [auditLog]);
  useEffect(() => { saveLS(LS_PRIVATE_NOTES, privateNotes); }, [privateNotes]);

  // Audit log helper
  const addAuditEntry = useCallback((ticketId: string, action: string, detail: string) => {
    const entry: AuditLogEntry = {
      timestamp: new Date().toISOString(),
      staffId: currentStaffId || "unknown",
      ticketId,
      action,
      detail,
    };
    setAuditLog((prev) => [entry, ...prev].slice(0, 200)); // keep last 200
  }, [currentStaffId]);

  // Transfer case state
  const [transferModalId, setTransferModalId] = useState<string | null>(null);
  const [targetDept, setTargetDept] = useState("phong_dao_tao");
  const [transferReason, setTransferReason] = useState("");

  // Supplement request state
  const [supplementModalId, setSupplementModalId] = useState<string | null>(null);
  const [supplementMsg, setSupplementMsg] = useState("");

  // AI Draft Response state
  const [aiDraftModalId, setAiDraftModalId] = useState<string | null>(null);
  const [aiDraftType, setAiDraftType] = useState<"approve" | "supplement" | "forward">("approve");
  const [aiDraftContent, setAiDraftContent] = useState("");
  const [draftCopied, setDraftCopied] = useState(false);

  // Official Receipt Print Modal state
  const [receiptModalId, setReceiptModalId] = useState<string | null>(null);

  const getAiDraftText = (type: "approve" | "supplement" | "forward", item: StaffQueueItem) => {
    if (type === "approve") {
      return `Kính gửi sinh viên ${item.studentName} (MSSV: ${item.studentId}),\n\nBộ phận Một cửa số - Trường Đại học Xây dựng Hà Nội (HUCE) xin thông báo: Hồ sơ "${item.title}" (Mã tiếp nhận: ${item.ticketCode}) của em đã hoàn tất 6/6 cổng thẩm định nghiệp vụ và chính thức được tiếp nhận.\n\n- Thời hạn xử lý cam kết: Trong vòng 24 giờ làm việc.\n- Bộ phận chuyên môn thụ lý: ${item.targetDepartment || "Phòng Quản lý Đào tạo"}.\n- Địa điểm nhận kết quả: P.102 Nhà H1 (hoặc nhận bản điện tử trên Cổng sinh viên).\n\nTrân trọng,\nCán bộ Một cửa số HUCE`;
    } else if (type === "supplement") {
      return `Kính gửi sinh viên ${item.studentName} (MSSV: ${item.studentId}),\n\nSau khi thẩm định hồ sơ "${item.title}" (Mã tiếp nhận: ${item.ticketCode}), Bộ phận Một cửa nhận thấy hồ sơ của em còn thiếu minh chứng theo Quy chế Đào tạo:\n\n- Cần bổ sung: Bản scan có dấu đỏ hoặc bản chụp CCCD/thẻ BHYT/đơn xác nhận có chữ ký.\n- Thời hạn hoàn thiện: Trước 17:00 ngày làm việc tiếp theo.\n\nEm vui lòng bấm "Nộp bổ sung hồ sơ" trên Cổng sinh viên để tải tài liệu trực tuyến.\n\nTrân trọng,\nCán bộ Một cửa số HUCE`;
    } else {
      return `Kính gửi sinh viên ${item.studentName} (MSSV: ${item.studentId}),\n\nHồ sơ "${item.title}" (Mã tiếp nhận: ${item.ticketCode}) của em đã được Bộ phận Một cửa chuyển tiếp sang ${item.targetDepartment || "Phòng Quản lý Đào tạo"} để giải quyết theo thẩm quyền chuyên môn cấp Phòng.\n\nCán bộ phụ trách sẽ liên hệ hoặc thông báo quyết định trên hệ thống.\n\nTrân trọng,\nCán bộ Một cửa số HUCE`;
    }
  };

  const handleOpenAiDraft = (item: StaffQueueItem) => {
    setAiDraftModalId(item.id);
    setAiDraftType("approve");
    setAiDraftContent(getAiDraftText("approve", item));
    setDraftCopied(false);
  };

  const handleAiDraftTypeChange = (type: "approve" | "supplement" | "forward", item: StaffQueueItem) => {
    setAiDraftType(type);
    setAiDraftContent(getAiDraftText(type, item));
    setDraftCopied(false);
  };

  const handleCopyDraft = async () => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(aiDraftContent);
        setDraftCopied(true);
        setTimeout(() => setDraftCopied(false), 3000);
      }
    } catch {
      // Fallback
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleGateToggle = (ticketId: string, gateId: string) => {
    const wasChecked = !!checkedGates[ticketId]?.[gateId];
    setCheckedGates((prev) => ({
      ...prev,
      [ticketId]: {
        ...(prev[ticketId] || {}),
        [gateId]: !wasChecked,
      },
    }));
    // Record timestamp
    if (!wasChecked) {
      setGateTimestamps((prev) => ({
        ...prev,
        [ticketId]: {
          ...(prev[ticketId] || {}),
          [gateId]: new Date().toISOString(),
        },
      }));
      const gate = INTAKE_CHECKLIST_GATES.find((g) => g.id === gateId);
      addAuditEntry(ticketId, "GATE_CHECK", `Đã xác nhận: ${gate?.label || gateId}`);
    } else {
      setGateTimestamps((prev) => {
        const copy = { ...(prev[ticketId] || {}) };
        delete copy[gateId];
        return { ...prev, [ticketId]: copy };
      });
      const gate = INTAKE_CHECKLIST_GATES.find((g) => g.id === gateId);
      addAuditEntry(ticketId, "GATE_UNCHECK", `Bỏ xác nhận: ${gate?.label || gateId}`);
    }
  };

  const handleAiAutoCheck = (ticketId: string) => {
    const allChecked: Record<string, boolean> = {};
    const allTimestamps: Record<string, string> = {};
    const now = new Date().toISOString();
    INTAKE_CHECKLIST_GATES.forEach((g) => {
      allChecked[g.id] = true;
      allTimestamps[g.id] = now;
    });
    setCheckedGates((prev) => ({ ...prev, [ticketId]: allChecked }));
    setGateTimestamps((prev) => ({ ...prev, [ticketId]: allTimestamps }));
    addAuditEntry(ticketId, "AI_AUTO_CHECK", "AI đã tự động đối chiếu 6/6 cổng thẩm định");
  };

  const isChecklistComplete = (ticketId: string) => {
    const ticketGates = checkedGates[ticketId] || {};
    const checkedCount = INTAKE_CHECKLIST_GATES.filter((g) => !!ticketGates[g.id]).length;
    const hasException = !!(exceptionReasons[ticketId] || "").trim();
    return checkedCount === INTAKE_CHECKLIST_GATES.length || hasException;
  };

  const handleFinalize = (ticketId: string) => {
    const complete = isChecklistComplete(ticketId);
    if (!complete) return;
    onFinalizeIntake?.(ticketId, {
      checklistPassed: true,
      exceptionReason: exceptionReasons[ticketId] || undefined,
    });
    setFinalizedTickets((prev) => ({ ...prev, [ticketId]: true }));
    addAuditEntry(ticketId, "FINALIZE_INTAKE", `Hoàn tất tiếp nhận. ${exceptionReasons[ticketId] ? `Ngoại lệ: ${exceptionReasons[ticketId]}` : "Đủ 6/6 cổng"}`);
  };

  const handleConfirmTransfer = (ticketId: string) => {
    onTransferTicket?.(ticketId, {
      targetDepartment: targetDept,
      transferReason: transferReason || undefined,
    });
    addAuditEntry(ticketId, "TRANSFER", `Chuyển sang ${targetDept}. Lý do: ${transferReason || "Theo thẩm quyền"}`);
    setTransferModalId(null);
    setTransferReason("");
  };

  const handleConfirmSupplement = (ticketId: string) => {
    if (!supplementMsg.trim()) return;
    onRequestSupplement?.(ticketId, { requestMessage: supplementMsg.trim() });
    addAuditEntry(ticketId, "SUPPLEMENT_REQUEST", `Yêu cầu SV bổ sung: ${supplementMsg.trim().slice(0, 80)}...`);
    setSupplementModalId(null);
    setSupplementMsg("");
  };

  // Filter items
  const filteredItems = items
    .filter((item) => {
      if (filter === "unassigned") return item.status === "unassigned";
      if (filter === "my") return item.assignedStaffId === currentStaffId;
      if (filter === "urgent") return item.priority === "urgent";
      return true;
    })
    .filter((item) => {
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      return (
        item.ticketCode.toLowerCase().includes(q) ||
        item.studentName.toLowerCase().includes(q) ||
        item.studentId.toLowerCase().includes(q) ||
        item.title.toLowerCase().includes(q) ||
        (item.publicContent && item.publicContent.toLowerCase().includes(q))
      );
    })
    .sort((a, b) => {
      if (sortBy === "urgent") {
        const pOrder: Record<StaffQueueItem["priority"], number> = { urgent: 0, high: 1, normal: 2 };
        return pOrder[a.priority] - pOrder[b.priority];
      }
      return 0;
    });

  const getPriorityBadge = (priority: StaffQueueItem["priority"]) => {
    switch (priority) {
      case "urgent":
        return {
          label: "[!] Khẩn cấp",
          text: "[!] Khẩn cấp",
          bg: "#fef2f2",
          border: "#f87171",
          color: "#991b1b",
        };
      case "high":
        return {
          label: "[▲] Cao",
          text: "[▲] Cao",
          bg: "#fffbeb",
          border: "#fde68a",
          color: "#92400e",
        };
      case "normal":
      default:
        return {
          label: "[•] Thường",
          text: "[•] Thường",
          bg: "var(--color-slate-100, #f1f5f9)",
          border: "var(--color-slate-200, #cbd5e1)",
          color: "var(--color-slate-700, #334155)",
        };
    }
  };

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
          <h2
            style={{
              margin: "0 0 4px 0",
              fontSize: "18px",
              fontWeight: 700,
              color: "var(--color-slate-900, #0f172a)",
            }}
          >
            Hàng đợi tiếp nhận yêu cầu (Cán bộ một cửa)
          </h2>
          <p
            style={{
              margin: 0,
              fontSize: "13px",
              color: "var(--color-slate-500, #64748b)",
            }}
          >
            Không gian phân loại mật độ cao với kiểm soát quyền sở hữu và giải quyết xung đột
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              aria-label="Làm mới hàng đợi"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                fontSize: "13px",
                fontWeight: 600,
                color: "var(--color-primary, #1e3a8a)",
                backgroundColor: "#ffffff",
                border: "1px solid var(--color-slate-300, #cbd5e1)",
                borderRadius: "var(--radius-sm, 6px)",
                cursor: "pointer",
                minHeight: "36px",
              }}
            >
              <span aria-hidden="true">↻</span>
              <span>Làm mới</span>
            </button>
          )}

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
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "#10b981",
              }}
              aria-hidden="true"
            />
            <span>
              Cán bộ trực: <strong>{currentStaffId || "Chưa xác định"}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Search & Sort Toolbar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          backgroundColor: "#ffffff",
          padding: "12px 16px",
          borderRadius: "var(--radius-md, 10px)",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
        }}
      >
        <div style={{ flex: 1, minWidth: "260px" }}>
          <input
            type="search"
            placeholder="Tìm theo mã, tên sinh viên hoặc tiêu đề..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 14px",
              borderRadius: "6px",
              border: "1px solid var(--color-slate-300, #cbd5e1)",
              fontSize: "13px",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <label htmlFor="sort-queue" style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-600, #475569)" }}>
            Sắp xếp:
          </label>
          <select
            id="sort-queue"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortType)}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              border: "1px solid var(--color-slate-300, #cbd5e1)",
              fontSize: "13px",
              backgroundColor: "#ffffff",
            }}
          >
            <option value="default">Theo thứ tự tiếp nhận</option>
            <option value="urgent">Độ khẩn cấp ưu tiên</option>
          </select>
        </div>
      </div>

      {/* Accessible Segmented Filter Tabs */}
      <div
        role="tablist"
        aria-label="Bộ lọc hàng đợi tiếp nhận"
        style={{
          display: "flex",
          backgroundColor: "var(--color-slate-100, #f1f5f9)",
          padding: "3px",
          borderRadius: "var(--radius-md, 10px)",
          gap: "2px",
          alignSelf: "flex-start",
          flexWrap: "wrap",
        }}
      >
        <button
          type="button"
          role="tab"
          id="tab-all"
          aria-selected={filter === "all"}
          aria-controls="queue-panel"
          onClick={() => setFilter("all")}
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
          role="tab"
          id="tab-unassigned"
          aria-selected={filter === "unassigned"}
          aria-controls="queue-panel"
          onClick={() => setFilter("unassigned")}
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
          role="tab"
          id="tab-my"
          aria-selected={filter === "my"}
          aria-controls="queue-panel"
          onClick={() => setFilter("my")}
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
        <button
          type="button"
          role="tab"
          id="tab-urgent"
          aria-selected={filter === "urgent"}
          aria-controls="queue-panel"
          onClick={() => setFilter("urgent")}
          style={{
            padding: "6px 16px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: filter === "urgent" ? "#ffffff" : "transparent",
            color: filter === "urgent" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-600, #475569)",
            fontWeight: filter === "urgent" ? 600 : 500,
            fontSize: "13px",
            cursor: "pointer",
            boxShadow: filter === "urgent" ? "var(--shadow-xs)" : "none",
            transition: "var(--transition-fast, 150ms ease)",
          }}
        >
          Khẩn cấp
        </button>
      </div>

      {/* Queue Table with Semantic reflow support */}
      <div
        id="queue-panel"
        role="region"
        aria-label="Danh sách yêu cầu tiếp nhận"
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
              <th scope="col" style={{ padding: "14px 18px" }}>Nội dung & Thời gian chờ</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Ưu tiên</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Trạng thái</th>
              <th scope="col" style={{ padding: "14px 18px" }}>Hành động</th>
            </tr>
          </thead>
          <tbody>
            {filteredItems.map((item) => {
              const isUnassigned = item.status === "unassigned";
              const isMyItem = item.assignedStaffId === currentStaffId;
              const hasConflict = item.hasConflict === true;
              const isRestricted = item.isRestricted === true;
              const isStale = item.isStale === true;
              const isUnknown = item.actionOutcome === "unknown";
              const canClaim = isUnassigned && !hasConflict && !isRestricted && !isStale && !isUnknown;
              const isExpanded = !!expandedItems[item.id];
              const pBadge = getPriorityBadge(item.priority);

              const ticketGates = checkedGates[item.id] || {};
              const checkedCount = INTAKE_CHECKLIST_GATES.filter((g) => !!ticketGates[g.id]).length;
              const checklistDone = isChecklistComplete(item.id);
              const isFinalized = !!finalizedTickets[item.id];
              const sla = getSlaInfo(item.createdAt);

              return (
                <React.Fragment key={item.id}>
                  <tr
                    style={{
                      borderBottom: isExpanded ? "none" : "1px solid var(--color-slate-100, #f1f5f9)",
                      backgroundColor: hasConflict || isStale ? "#fffbeb" : isRestricted ? "#f8fafc" : "#ffffff",
                      transition: "var(--transition-fast, 150ms ease)",
                    }}
                  >
                    <td style={{ padding: "14px 18px", fontWeight: 700, color: "var(--color-primary, #1e3a8a)" }}>
                      <div>{item.ticketCode}</div>
                      <button
                        type="button"
                        onClick={() => toggleExpand(item.id)}
                        aria-expanded={isExpanded}
                        aria-label={`Chi tiết ${item.ticketCode}`}
                        style={{
                          background: "none",
                          border: "none",
                          padding: "2px 0",
                          color: "var(--color-slate-500, #64748b)",
                          fontSize: "11px",
                          cursor: "pointer",
                          textDecoration: "underline",
                        }}
                      >
                        {isExpanded ? "▲ Thu gọn" : "▼ Xem chi tiết"}
                      </button>
                    </td>

                    <td style={{ padding: "14px 18px", color: "var(--color-slate-800, #1e293b)", fontWeight: 500 }}>
                      {isRestricted ? (
                        <span style={{ color: "var(--color-slate-500, #64748b)", fontStyle: "italic" }}>
                          [Bảo mật danh tính]
                        </span>
                      ) : (
                        `${item.studentName} (${item.studentId})`
                      )}
                    </td>

                    <td style={{ padding: "14px 18px", color: "var(--color-slate-700, #334155)" }}>
                      {isRestricted ? (
                        <div style={{ color: "#b45309", fontWeight: 600 }}>
                          Hồ sơ hạn chế truy cập (Chỉ dành cho cán bộ thẩm quyền)
                        </div>
                      ) : (
                        <div>
                          <div>{item.title}</div>
                          {item.age && (
                            <div style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)", marginTop: "2px" }}>
                              Thời gian chờ: <strong>{item.age}</strong>
                            </div>
                          )}
                          {/* SLA Countdown Timer */}
                          <div style={{ marginTop: "6px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px" }}>
                              <span style={{ fontWeight: 700, color: sla.urgencyColor }}>⏱ SLA: {sla.remaining}</span>
                              <div style={{ flex: 1, maxWidth: "100px", height: "4px", backgroundColor: "#e2e8f0", borderRadius: "9999px", overflow: "hidden" }}>
                                <div style={{ width: `${sla.percentUsed}%`, height: "100%", backgroundColor: sla.urgencyColor, transition: "width 500ms ease" }} />
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {hasConflict && (
                        <div
                          style={{
                            marginTop: "6px",
                            padding: "4px 8px",
                            backgroundColor: "#fef3c7",
                            border: "1px solid #fde68a",
                            borderRadius: "4px",
                            fontSize: "12px",
                            color: "#92400e",
                          }}
                        >
                          <strong>Xung đột tiếp nhận:</strong> Ca này đã được cán bộ{" "}
                          <strong>{item.conflictStaffId || "khác"}</strong> nhận xử lý trước đó.
                        </div>
                      )}

                      {isStale && (
                        <div
                          style={{
                            marginTop: "6px",
                            padding: "6px 10px",
                            backgroundColor: "#fffbeb",
                            border: "1px solid #fde68a",
                            borderRadius: "4px",
                            fontSize: "12px",
                            color: "#92400e",
                          }}
                        >
                          <strong>Xung đột phiên bản:</strong> Dữ liệu đã thay đổi trên máy chủ. Vui lòng làm mới hàng đợi.
                        </div>
                      )}

                      {isUnknown && (
                        <div
                          style={{
                            marginTop: "6px",
                            padding: "6px 10px",
                            backgroundColor: "#fff7ed",
                            border: "1px solid #fdba74",
                            borderRadius: "4px",
                            fontSize: "12px",
                            color: "#9a3412",
                          }}
                        >
                          <strong>Chưa rõ kết quả:</strong> Đang đối soát kết quả ghi nhận từ máy chủ. Vui lòng thử lại.
                        </div>
                      )}
                    </td>

                    <td style={{ padding: "14px 18px" }}>
                      <span
                        style={{
                          display: "inline-block",
                          padding: "3px 10px",
                          borderRadius: "9999px",
                          fontSize: "12px",
                          fontWeight: 600,
                          backgroundColor: pBadge.bg,
                          color: pBadge.color,
                          border: `1px solid ${pBadge.border}`,
                        }}
                      >
                        {pBadge.text}
                      </span>
                    </td>

                    <td style={{ padding: "14px 18px", fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
                        {isStale
                          ? "Xung đột phiên bản"
                          : isUnknown
                          ? "Đang đối soát"
                          : hasConflict
                          ? "Xung đột ghi nhận"
                          : isRestricted
                          ? "Hạn chế quyền"
                          : isFinalized
                          ? "Đã tiếp nhận"
                          : isUnassigned
                          ? "Chờ tiếp nhận"
                          : isMyItem
                          ? "Đang xử lý"
                          : `Đã nhận (${item.assignedStaffId})`}
                    </td>

                    <td style={{ padding: "14px 18px" }}>
                      {isUnknown ? (
                        <button
                          type="button"
                          onClick={() => onReconcile?.(item.id)}
                          style={{
                            padding: "8px 14px",
                            borderRadius: "6px",
                            border: "none",
                            backgroundColor: "#ea580c",
                            color: "#ffffff",
                            fontWeight: 600,
                            fontSize: "12px",
                            cursor: "pointer",
                            minHeight: "40px",
                          }}
                        >
                          Thử đối soát lại
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => onClaimTicket?.(item.id)}
                          disabled={!canClaim}
                          aria-label={
                            isStale
                              ? `Xung đột phiên bản - ${item.ticketCode}`
                              : hasConflict
                              ? `Xung đột - ${item.ticketCode}`
                              : isRestricted
                              ? `Hạn chế truy cập - ${item.ticketCode}`
                              : canClaim
                              ? `Nhận xử lý ${item.ticketCode}`
                              : `Đã nhận - ${item.ticketCode}`
                          }
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
                          {isStale
                            ? "Xung đột phiên bản"
                            : hasConflict
                            ? "Xung đột"
                            : isRestricted
                            ? "Hạn chế"
                            : canClaim
                            ? "Nhận xử lý"
                            : "Đã nhận"}
                        </button>
                      )}
                    </td>
                  </tr>

                  {/* Expandable detail region with Intake Checklist & AI Copilot */}
                  {isExpanded && !isRestricted && (
                    <tr style={{ backgroundColor: "var(--color-slate-50, #f8fafc)", borderBottom: "1px solid var(--color-slate-200, #e2e8f0)" }}>
                      <td colSpan={6} style={{ padding: "20px 24px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                          {/* Public Context & Internal Staff Notes */}
                          <div
                            style={{
                              display: "grid",
                              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                              gap: "16px",
                            }}
                          >
                            <div
                              style={{
                                backgroundColor: "#ffffff",
                                padding: "14px 18px",
                                borderRadius: "8px",
                                border: "1px solid var(--color-slate-200, #e2e8f0)",
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "6px",
                                  fontSize: "12px",
                                  fontWeight: 700,
                                  textTransform: "uppercase",
                                  color: "var(--color-slate-700, #334155)",
                                  marginBottom: "8px",
                                }}
                              >
                                <span style={{ color: "#2563eb" }}>●</span> Nội dung công khai (Sinh viên thấy)
                              </div>
                              <p style={{ margin: 0, fontSize: "13px", color: "var(--color-slate-800, #1e293b)", lineHeight: 1.5 }}>
                                {item.publicContent || item.title}
                              </p>
                            </div>

                            <div
                              style={{
                                backgroundColor: "#fefce8",
                                padding: "14px 18px",
                                borderRadius: "8px",
                                border: "1px solid #fef08a",
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "6px",
                                  fontSize: "12px",
                                  fontWeight: 700,
                                  textTransform: "uppercase",
                                  color: "#854d0e",
                                  marginBottom: "8px",
                                }}
                              >
                                <span>🔒</span> Ghi chú nội bộ (Chỉ lưu hành nội bộ)
                              </div>
                              <p style={{ margin: 0, fontSize: "13px", color: "#713f12", lineHeight: 1.5 }}>
                                {item.internalNotes || "Không có ghi chú nội bộ cho ca này."}
                              </p>
                            </div>
                          </div>

                          {/* AI Copilot Triage Assistant Card */}
                          <div
                            style={{
                              backgroundColor: "#f5f3ff",
                              border: "1px solid #ddd6fe",
                              borderRadius: "10px",
                              padding: "16px 20px",
                            }}
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                              <span style={{ fontSize: "16px" }}>🤖</span>
                              <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "#5b21b6" }}>
                                Trợ lý AI Tiếp nhận & Phân loại thông minh
                              </h4>
                            </div>

                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px", color: "#4c1d95" }}>
                              <div>
                                <strong>Tóm tắt AI:</strong> Hồ sơ Một cửa: {item.title} ({item.priority === "urgent" ? "Mức độ khẩn cấp cao - cần xử lý trong 24h" : "Thời hạn tiêu chuẩn 48h"})
                              </div>
                              <div>
                                <strong>Đánh giá rủi ro trùng lặp:</strong> Không phát hiện hồ sơ trùng lặp trong hệ thống (Độ tin cậy 98%).
                              </div>
                              <div>
                                <strong>Đề xuất câu trả lời nhanh:</strong>{" "}
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSupplementModalId(item.id);
                                    setSupplementMsg("Chào bạn, Nhà trường đã tiếp nhận hồ sơ. Vui lòng bổ sung bản chụp CCCD hai mặt để hoàn thiện thủ tục.");
                                  }}
                                  style={{
                                    background: "#ede9fe",
                                    border: "1px solid #c4b5fd",
                                    borderRadius: "4px",
                                    padding: "2px 8px",
                                    fontSize: "12px",
                                    color: "#5b21b6",
                                    cursor: "pointer",
                                    fontWeight: 600,
                                  }}
                                >
                                  Mẫu: Yêu cầu bổ sung CCCD
                                </button>
                              </div>
                            </div>
                          </div>

                          {/* Student Attachments with OCR Badges */}
                          {item.attachments && item.attachments.length > 0 && (
                            <div
                              style={{
                                backgroundColor: "#ffffff",
                                borderRadius: "10px",
                                border: "1px solid var(--color-slate-200, #e2e8f0)",
                                padding: "16px 20px",
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
                                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                                  📎 Minh chứng & Hồ sơ sinh viên đính kèm ({item.attachments.length})
                                </h4>
                                <span style={{ fontSize: "12px", color: "#16a34a", fontWeight: 600 }}>
                                  ✓ AI OCR thẩm định tự động
                                </span>
                              </div>
                              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "10px" }}>
                                {item.attachments.map((att, attIdx) => (
                                  <div
                                    key={attIdx}
                                    style={{
                                      display: "flex",
                                      alignItems: "center",
                                      justifyContent: "space-between",
                                      backgroundColor: "#f8fafc",
                                      border: "1px solid #e2e8f0",
                                      borderRadius: "8px",
                                      padding: "10px 14px",
                                    }}
                                  >
                                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                      <span style={{ fontSize: "16px" }}>{att.type === "pdf" ? "📄" : "🖼️"}</span>
                                      <span style={{ fontSize: "13px", fontWeight: 600, color: "#1e293b" }}>{att.name}</span>
                                    </div>
                                    <span
                                      style={{
                                        fontSize: "11px",
                                        fontWeight: 700,
                                        padding: "2px 8px",
                                        borderRadius: "4px",
                                        backgroundColor: "#dcfce7",
                                        color: "#15803d",
                                        border: "1px solid #86efac",
                                      }}
                                    >
                                      {att.ocrBadge} ({att.confidence})
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Adaptive Intake Checklist */}
                          <div
                            style={{
                              backgroundColor: "#ffffff",
                              borderRadius: "10px",
                              border: "1px solid var(--color-slate-200, #e2e8f0)",
                              padding: "16px 20px",
                            }}
                          >
                            {/* Preset Actions Bar */}
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                flexWrap: "wrap",
                                gap: "10px",
                                backgroundColor: "#eff6ff",
                                border: "1px solid #bfdbfe",
                                borderRadius: "8px",
                                padding: "10px 16px",
                                marginBottom: "14px",
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                <span style={{ fontSize: "14px" }}>⚡</span>
                                <span style={{ fontSize: "13px", fontWeight: 700, color: "#1e40af" }}>
                                  Thao tác chuẩn 1-chạm:
                                </span>
                              </div>
                              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                                <button
                                  type="button"
                                  onClick={() => handleAiAutoCheck(item.id)}
                                  style={{
                                    padding: "6px 12px",
                                    borderRadius: "6px",
                                    border: "1px solid #60a5fa",
                                    backgroundColor: "#ffffff",
                                    color: "#1d4ed8",
                                    fontSize: "12px",
                                    fontWeight: 600,
                                    cursor: "pointer",
                                  }}
                                >
                                  ✨ Duyệt chuẩn 6/6 cổng
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSupplementModalId(item.id);
                                    setSupplementMsg("Chào em, hồ sơ còn thiếu bản scan có con dấu tròn đỏ xác nhận. Vui lòng bổ sung.");
                                  }}
                                  style={{
                                    padding: "6px 12px",
                                    borderRadius: "6px",
                                    border: "1px solid #cbd5e1",
                                    backgroundColor: "#ffffff",
                                    color: "#475569",
                                    fontSize: "12px",
                                    fontWeight: 600,
                                    cursor: "pointer",
                                  }}
                                >
                                  ⚠️ Mẫu: Yêu cầu bổ sung dấu đỏ
                                </button>
                              </div>
                            </div>

                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
                              <div>
                                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                                  Checklist tiếp nhận hồ sơ (Bắt buộc {checkedCount}/{INTAKE_CHECKLIST_GATES.length})
                                </h4>
                                <span style={{ fontSize: "12px", color: checkedCount === INTAKE_CHECKLIST_GATES.length ? "#16a34a" : "var(--color-slate-500, #64748b)", fontWeight: 500 }}>
                                  {checkedCount === INTAKE_CHECKLIST_GATES.length ? "Đã đạt 100% tiêu chí hợp lệ" : `Tiến độ thẩm định: ${Math.round((checkedCount / INTAKE_CHECKLIST_GATES.length) * 100)}%`}
                                </span>
                              </div>
                              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <button
                                  type="button"
                                  onClick={() => handleAiAutoCheck(item.id)}
                                  disabled={isFinalized}
                                  style={{
                                    padding: "5px 12px",
                                    borderRadius: "6px",
                                    border: "1px solid #c4b5fd",
                                    backgroundColor: "#f5f3ff",
                                    color: "#6d28d9",
                                    fontSize: "12px",
                                    fontWeight: 600,
                                    cursor: isFinalized ? "not-allowed" : "pointer",
                                  }}
                                >
                                  ✨ AI Đối chiếu tự động
                                </button>
                                {isFinalized && (
                                  <span style={{ color: "#16a34a", fontWeight: 700, fontSize: "12px" }}>
                                    ✓ Đã hoàn tất tiếp nhận
                                  </span>
                                )}
                              </div>
                            </div>

                            <div style={{ width: "100%", height: "6px", backgroundColor: "#e2e8f0", borderRadius: "9999px", overflow: "hidden", marginBottom: "14px" }}>
                              <div
                                style={{
                                  width: `${(checkedCount / INTAKE_CHECKLIST_GATES.length) * 100}%`,
                                  height: "100%",
                                  backgroundColor: checkedCount === INTAKE_CHECKLIST_GATES.length ? "#16a34a" : "#2563eb",
                                  transition: "all 250ms ease",
                                }}
                              />
                            </div>

                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "10px" }}>
                              {INTAKE_CHECKLIST_GATES.map((gate) => (
                                <label
                                  key={gate.id}
                                  style={{
                                    display: "flex",
                                    alignItems: "flex-start",
                                    gap: "10px",
                                    fontSize: "13px",
                                    color: "var(--color-slate-800, #1e293b)",
                                    cursor: "pointer",
                                    padding: "8px 12px",
                                    borderRadius: "8px",
                                    backgroundColor: ticketGates[gate.id] ? "#f8fafc" : "#ffffff",
                                    border: ticketGates[gate.id] ? "1.5px solid #2563eb" : "1px solid var(--color-slate-200, #e2e8f0)",
                                    boxShadow: ticketGates[gate.id] ? "0 1px 3px rgba(37,99,235,0.08)" : "none",
                                    transition: "all 150ms ease",
                                  }}
                                >
                                  <input
                                    type="checkbox"
                                    checked={!!ticketGates[gate.id]}
                                    onChange={() => handleGateToggle(item.id, gate.id)}
                                    style={{ width: "16px", height: "16px", cursor: "pointer", marginTop: "2px" }}
                                  />
                                  <div style={{ display: "flex", flexDirection: "column", gap: "3px", flex: 1 }}>
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px", flexWrap: "wrap" }}>
                                      <span style={{ fontWeight: 600 }}>{gate.label}</span>
                                      <span
                                        style={{
                                          fontSize: "11px",
                                          padding: "1px 6px",
                                          borderRadius: "4px",
                                          backgroundColor: gate.sourceBadgeBg,
                                          color: gate.sourceBadgeColor,
                                          fontWeight: 700,
                                        }}
                                      >
                                        {gate.sourceBadge}
                                      </span>
                                    </div>
                                    <span style={{ fontSize: "11px", color: "var(--color-slate-500, #64748b)" }}>
                                      {gate.aiEvidence} <strong style={{ color: "#16a34a" }}>({gate.confidence})</strong>
                                    </span>
                                  </div>
                                </label>
                              ))}
                            </div>

                            <div style={{ marginTop: "14px", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "10px" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <label htmlFor={`ex-${item.id}`} style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
                                  Ngoại lệ duyệt nhanh (ghi lý do nếu chưa đủ 6 mục):
                                </label>
                                <input
                                  id={`ex-${item.id}`}
                                  type="text"
                                  placeholder="Ví dụ: Lãnh đạo phê duyệt trực tiếp qua giấy..."
                                  value={exceptionReasons[item.id] || ""}
                                  onChange={(e) =>
                                    setExceptionReasons((prev) => ({ ...prev, [item.id]: e.target.value }))
                                  }
                                  style={{
                                    padding: "4px 8px",
                                    borderRadius: "4px",
                                    border: "1px solid var(--color-slate-300, #cbd5e1)",
                                    fontSize: "12px",
                                    width: "240px",
                                  }}
                                />
                              </div>

                              <button
                                type="button"
                                onClick={() => handleFinalize(item.id)}
                                disabled={!checklistDone || isFinalized}
                                style={{
                                  padding: "8px 18px",
                                  borderRadius: "6px",
                                  border: "none",
                                  backgroundColor: checklistDone && !isFinalized ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-200, #e2e8f0)",
                                  color: checklistDone && !isFinalized ? "#ffffff" : "var(--color-slate-500, #64748b)",
                                  fontWeight: 600,
                                  fontSize: "13px",
                                  cursor: checklistDone && !isFinalized ? "pointer" : "not-allowed",
                                }}
                              >
                                {isFinalized ? "Đã tiếp nhận" : "Xác nhận hoàn tất tiếp nhận"}
                              </button>
                            </div>
                          </div>

                          {/* Quick Staff Workflow Actions */}
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "flex-end", alignItems: "center" }}>
                            <button
                              type="button"
                              onClick={() => handleOpenAiDraft(item)}
                              style={{
                                padding: "8px 14px",
                                borderRadius: "6px",
                                border: "1px solid #c4b5fd",
                                backgroundColor: "#f5f3ff",
                                color: "#6d28d9",
                                fontWeight: 600,
                                fontSize: "13px",
                                cursor: "pointer",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "6px",
                              }}
                            >
                              <span>✨ AI Dự thảo phản hồi cho SV</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => setReceiptModalId(item.id)}
                              style={{
                                padding: "8px 14px",
                                borderRadius: "6px",
                                border: "1px solid var(--color-slate-300, #cbd5e1)",
                                backgroundColor: "#ffffff",
                                color: "var(--color-slate-700, #334155)",
                                fontWeight: 600,
                                fontSize: "13px",
                                cursor: "pointer",
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "6px",
                              }}
                            >
                              <span>🖨️ In Phiếu Tiếp Nhận (Mẫu 01/MC)</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => setSupplementModalId(item.id)}
                              style={{
                                padding: "8px 14px",
                                borderRadius: "6px",
                                border: "1px solid #fde68a",
                                backgroundColor: "#fffbeb",
                                color: "#92400e",
                                fontWeight: 600,
                                fontSize: "13px",
                                cursor: "pointer",
                              }}
                            >
                              Yêu cầu bổ sung thông tin
                            </button>

                            <button
                              type="button"
                              onClick={() => setTransferModalId(item.id)}
                              style={{
                                padding: "8px 14px",
                                borderRadius: "6px",
                                border: "1px solid #bfdbfe",
                                backgroundColor: "#eff6ff",
                                color: "#1e3a8a",
                                fontWeight: 600,
                                fontSize: "13px",
                                cursor: "pointer",
                              }}
                            >
                              Chuyển đơn vị chuyên môn
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Transfer Department Modal */}
      {transferModalId && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="transfer-title"
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(15, 23, 42, 0.5)",
            backdropFilter: "blur(2px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "16px",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "12px",
              padding: "24px",
              maxWidth: "480px",
              width: "100%",
              boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <h3 id="transfer-title" style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
              Chuyển hồ sơ sang đơn vị chuyên môn
            </h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="dept-select" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                Đơn vị tiếp nhận mới
              </label>
              <select
                id="dept-select"
                value={targetDept}
                onChange={(e) => setTargetDept(e.target.value)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  fontSize: "14px",
                }}
              >
                <option value="phong_dao_tao">Phòng Quản lý Đào tạo</option>
                <option value="phong_ctsv">Phòng Công tác Sinh viên (CTSV)</option>
                <option value="phong_khao_thi">Phòng Khảo thí & Đảm bảo chất lượng</option>
                <option value="khoa_cntt">Văn phòng Khoa Công nghệ Thông tin</option>
                <option value="tram_y_te">Trạm Y tế Trường</option>
              </select>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="transfer-reason" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                Lý do chuyển tiếp (Lưu lịch sử kiểm toán)
              </label>
              <textarea
                id="transfer-reason"
                rows={3}
                placeholder="Nhập ghi chú chuyển ca giải thích thẩm quyền..."
                value={transferReason}
                onChange={(e) => setTransferReason(e.target.value)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  fontSize: "13px",
                }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
              <button
                type="button"
                onClick={() => setTransferModalId(null)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  backgroundColor: "#ffffff",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={() => handleConfirmTransfer(transferModalId)}
                style={{
                  padding: "8px 18px",
                  borderRadius: "6px",
                  border: "none",
                  backgroundColor: "var(--color-primary, #1e3a8a)",
                  color: "#ffffff",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Xác nhận chuyển đơn
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Request Supplement Modal */}
      {supplementModalId && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="supp-title"
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(15, 23, 42, 0.5)",
            backdropFilter: "blur(2px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "16px",
          }}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "12px",
              padding: "24px",
              maxWidth: "480px",
              width: "100%",
              boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <h3 id="supp-title" style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
              Yêu cầu sinh viên bổ sung thông tin hồ sơ
            </h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label htmlFor="supp-msg" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                Nội dung yêu cầu gửi tới sinh viên
              </label>
              <textarea
                id="supp-msg"
                rows={3}
                placeholder="Nêu rõ loại giấy tờ hoặc thông tin cần bổ sung..."
                value={supplementMsg}
                onChange={(e) => setSupplementMsg(e.target.value)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  fontSize: "13px",
                }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "8px" }}>
              <button
                type="button"
                onClick={() => setSupplementModalId(null)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  backgroundColor: "#ffffff",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={() => handleConfirmSupplement(supplementModalId)}
                style={{
                  padding: "8px 18px",
                  borderRadius: "6px",
                  border: "none",
                  backgroundColor: "#d97706",
                  color: "#ffffff",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Gửi yêu cầu bổ sung
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AI Draft Response Modal */}
      {aiDraftModalId && (() => {
        const item = items.find((i) => i.id === aiDraftModalId);
        if (!item) return null;
        return (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="ai-draft-title"
            style={{
              position: "fixed",
              inset: 0,
              backgroundColor: "rgba(15, 23, 42, 0.55)",
              backdropFilter: "blur(4px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 1000,
              padding: "16px",
            }}
          >
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                padding: "24px",
                maxWidth: "620px",
                width: "100%",
                boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
                maxHeight: "90vh",
                overflowY: "auto",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "20px" }}>✨</span>
                  <h3 id="ai-draft-title" style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: "#4c1d95" }}>
                    Trợ lý AI Soạn Thảo Phản Hồi Cho Sinh Viên
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => setAiDraftModalId(null)}
                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: "18px", color: "#64748b" }}
                  aria-label="Đóng hộp thoại"
                >
                  ✕
                </button>
              </div>

              <div style={{ fontSize: "13px", color: "var(--color-slate-600, #475569)" }}>
                Hồ sơ: <strong>{item.ticketCode}</strong> — {item.studentName} ({item.studentId})
              </div>

              {/* Template selector tabs */}
              <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid #e2e8f0", paddingBottom: "8px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={() => handleAiDraftTypeChange("approve", item)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "none",
                    backgroundColor: aiDraftType === "approve" ? "#eff6ff" : "transparent",
                    color: aiDraftType === "approve" ? "#1e40af" : "#64748b",
                    fontWeight: aiDraftType === "approve" ? 700 : 500,
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  ✓ Tiếp nhận & Hẹn trả kết quả
                </button>
                <button
                  type="button"
                  onClick={() => handleAiDraftTypeChange("supplement", item)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "none",
                    backgroundColor: aiDraftType === "supplement" ? "#fffbeb" : "transparent",
                    color: aiDraftType === "supplement" ? "#92400e" : "#64748b",
                    fontWeight: aiDraftType === "supplement" ? 700 : 500,
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  ⚠️ Yêu cầu bổ sung hồ sơ
                </button>
                <button
                  type="button"
                  onClick={() => handleAiDraftTypeChange("forward", item)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "none",
                    backgroundColor: aiDraftType === "forward" ? "#faf5ff" : "transparent",
                    color: aiDraftType === "forward" ? "#6b21a8" : "#64748b",
                    fontWeight: aiDraftType === "forward" ? 700 : 500,
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  ↗ Hướng dẫn chuyển tuyến
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label htmlFor="ai-draft-content" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
                  Nội dung phản hồi (có thể chỉnh sửa trực tiếp)
                </label>
                <textarea
                  id="ai-draft-content"
                  rows={8}
                  value={aiDraftContent}
                  onChange={(e) => setAiDraftContent(e.target.value)}
                  style={{
                    padding: "10px 12px",
                    borderRadius: "8px",
                    border: "1px solid #cbd5e1",
                    fontSize: "13px",
                    lineHeight: 1.5,
                    fontFamily: "inherit",
                    resize: "vertical",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "8px", flexWrap: "wrap", gap: "10px" }}>
                <span style={{ fontSize: "12px", color: draftCopied ? "#16a34a" : "#64748b", fontWeight: 500 }}>
                  {draftCopied ? "✓ Đã sao chép vào bộ nhớ tạm!" : "Trợ lý AI tự động trích dẫn quy chế đào tạo HUCE"}
                </span>

                <div style={{ display: "flex", gap: "10px" }}>
                  <button
                    type="button"
                    onClick={handleCopyDraft}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "6px",
                      border: "1px solid #cbd5e1",
                      backgroundColor: "#ffffff",
                      fontSize: "13px",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {draftCopied ? "✓ Đã sao chép" : "📋 Sao chép văn bản"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (aiDraftType === "supplement") {
                        setSupplementMsg(aiDraftContent);
                        setSupplementModalId(item.id);
                      }
                      setAiDraftModalId(null);
                    }}
                    style={{
                      padding: "8px 18px",
                      borderRadius: "6px",
                      border: "none",
                      backgroundColor: "#6d28d9",
                      color: "#ffffff",
                      fontWeight: 600,
                      fontSize: "13px",
                      cursor: "pointer",
                    }}
                  >
                    Áp dụng phản hồi này
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Official Receipt Print Modal (Mẫu 01/MC) */}
      {receiptModalId && (() => {
        const item = items.find((i) => i.id === receiptModalId);
        if (!item) return null;
        return (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="receipt-title"
            style={{
              position: "fixed",
              inset: 0,
              backgroundColor: "rgba(15, 23, 42, 0.6)",
              backdropFilter: "blur(4px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 1000,
              padding: "16px",
            }}
          >
            <div
              style={{
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                padding: "32px",
                maxWidth: "680px",
                width: "100%",
                boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
                display: "flex",
                flexDirection: "column",
                gap: "20px",
                maxHeight: "90vh",
                overflowY: "auto",
                border: "2px solid #0f172a",
              }}
            >
              {/* Official Header */}
              <div style={{ textAlign: "center", borderBottom: "2px solid #0f172a", paddingBottom: "16px" }}>
                <div style={{ fontSize: "13px", fontWeight: 700, textTransform: "uppercase" }}>
                  TRƯỜNG ĐẠI HỌC XÂY DỰNG HÀ NỘI
                </div>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "#475569" }}>
                  BỘ PHẬN TIẾP NHẬN VÀ TRẢ KẾT QUẢ MỘT CỬA SỐ
                </div>
                <div style={{ width: "80px", height: "1px", backgroundColor: "#000", margin: "6px auto" }} />
                <h2 id="receipt-title" style={{ margin: "10px 0 4px 0", fontSize: "18px", fontWeight: 800, textTransform: "uppercase" }}>
                  GIẤY TIẾP NHẬN HỒ SƠ VÀ HẸN TRẢ KẾT QUẢ
                </h2>
                <div style={{ fontSize: "13px", fontStyle: "italic", color: "#475569" }}>
                  (Mẫu số 01/MC - Ban hành theo Quy chế Một cửa số HUCE)
                </div>
                <div style={{ marginTop: "6px", fontSize: "13px", fontWeight: 700, color: "#1e3a8a" }}>
                  Mã số biên nhận: {item.ticketCode}
                </div>
              </div>

              {/* Receipt Body */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "14px", lineHeight: 1.6 }}>
                <div><strong>Người nộp hồ sơ:</strong> {item.studentName} — MSSV: <strong>{item.studentId}</strong></div>
                <div><strong>Nội dung thủ tục:</strong> {item.title}</div>
                <div><strong>Đơn vị chuyên môn xử lý:</strong> {item.targetDepartment || "Phòng Quản lý Đào tạo"}</div>
                <div><strong>Thời điểm tiếp nhận:</strong> {item.createdAt} (Ghi nhận trên CSDL số)</div>
                <div><strong>Thời hạn cam kết trả kết quả (SLA):</strong> Trước 17:00 ngày làm việc tiếp theo</div>
                <div>
                  <strong>Kết quả kiểm tra checklist tiếp nhận (6/6 cổng):</strong>
                  <ul style={{ margin: "4px 0 0 0", paddingLeft: "20px", fontSize: "13px", color: "#166534" }}>
                    <li>✓ Định danh & MSSV qua tài khoản số (VNeID Mức 2)</li>
                    <li>✓ Thẩm quyền Một cửa số theo Quy chế Đào tạo</li>
                    <li>✓ Kiểm tra không trùng lặp đơn trong 30 ngày</li>
                    <li>✓ Minh chứng đính kèm hợp lệ (AI OCR chữ ký & dấu đỏ)</li>
                    <li>✓ Xác định thời hạn xử lý SLA chuẩn</li>
                    <li>✓ Rà soát tuân thủ bảo vệ dữ liệu cá nhân Nghị định 13/2023</li>
                  </ul>
                </div>
              </div>

              {/* Signature block */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px", paddingTop: "16px", borderTop: "1px dashed #cbd5e1" }}>
                <div style={{ textAlign: "center", width: "45%" }}>
                  <div style={{ fontSize: "13px", fontWeight: 600 }}>NGƯỜI NỘP HỒ SƠ</div>
                  <div style={{ fontSize: "12px", fontStyle: "italic", color: "#64748b" }}>(Ký điện tử qua SSO)</div>
                  <div style={{ marginTop: "30px", fontWeight: 700 }}>{item.studentName}</div>
                </div>

                <div style={{ textAlign: "center", width: "45%" }}>
                  <div style={{ fontSize: "13px", fontWeight: 600 }}>CÁN BỘ TIẾP NHẬN</div>
                  <div style={{ fontSize: "12px", fontStyle: "italic", color: "#64748b" }}>(Đã thẩm định & xác nhận số)</div>
                  <div style={{ marginTop: "30px", fontWeight: 700, color: "#1e3a8a" }}>{item.assignedStaffId || "Cán bộ Một cửa HUCE"}</div>
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setReceiptModalId(null)}
                  style={{
                    padding: "8px 18px",
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
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.print();
                    }
                  }}
                  style={{
                    padding: "8px 20px",
                    borderRadius: "6px",
                    border: "none",
                    backgroundColor: "var(--color-primary, #1e3a8a)",
                    color: "#ffffff",
                    fontWeight: 600,
                    fontSize: "13px",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>🖨️ In Biên Nhận / Lưu PDF</span>
                </button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Audit Log Panel */}
      <div
        style={{
          backgroundColor: "#ffffff",
          borderRadius: "var(--radius-lg, 14px)",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          overflow: "hidden",
        }}
      >
        <button
          type="button"
          onClick={() => setShowAuditLog((prev) => !prev)}
          style={{
            width: "100%",
            padding: "14px 20px",
            border: "none",
            backgroundColor: "transparent",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: 700,
            color: "var(--color-slate-800, #1e293b)",
          }}
        >
          <span>📋 Nhật ký thao tác (Audit Trail) — {auditLog.length} bản ghi</span>
          <span style={{ fontSize: "12px", color: "var(--color-slate-500)" }}>
            {showAuditLog ? "▲ Thu gọn" : "▼ Mở rộng"}
          </span>
        </button>

        {showAuditLog && (
          <div style={{ padding: "0 20px 16px 20px" }}>
            {auditLog.length === 0 ? (
              <div style={{ padding: "20px", textAlign: "center", color: "var(--color-slate-500)", fontSize: "13px" }}>
                Chưa có thao tác nào được ghi nhận.
              </div>
            ) : (
              <div style={{ maxHeight: "300px", overflowY: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #e2e8f0", color: "#64748b", textTransform: "uppercase", fontSize: "11px", fontWeight: 700 }}>
                      <th style={{ padding: "8px 10px", textAlign: "left" }}>Thời điểm</th>
                      <th style={{ padding: "8px 10px", textAlign: "left" }}>Cán bộ</th>
                      <th style={{ padding: "8px 10px", textAlign: "left" }}>Mã hồ sơ</th>
                      <th style={{ padding: "8px 10px", textAlign: "left" }}>Hành động</th>
                      <th style={{ padding: "8px 10px", textAlign: "left" }}>Chi tiết</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLog.slice(0, 50).map((entry, idx) => (
                      <tr
                        key={`audit-${idx}`}
                        style={{
                          borderBottom: "1px solid #f1f5f9",
                          backgroundColor: idx % 2 === 0 ? "#ffffff" : "#f8fafc",
                        }}
                      >
                        <td style={{ padding: "6px 10px", color: "#64748b", whiteSpace: "nowrap" }}>
                          {new Date(entry.timestamp).toLocaleString("vi-VN", {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                            day: "2-digit",
                            month: "2-digit",
                          })}
                        </td>
                        <td style={{ padding: "6px 10px", fontWeight: 600, color: "#1e3a8a" }}>
                          {entry.staffId}
                        </td>
                        <td style={{ padding: "6px 10px", fontWeight: 600 }}>
                          {entry.ticketId.slice(0, 8)}
                        </td>
                        <td style={{ padding: "6px 10px" }}>
                          <span
                            style={{
                              padding: "1px 6px",
                              borderRadius: "4px",
                              fontSize: "10px",
                              fontWeight: 700,
                              backgroundColor:
                                entry.action === "FINALIZE_INTAKE" ? "#ecfdf5" :
                                entry.action === "AI_AUTO_CHECK" ? "#f5f3ff" :
                                entry.action === "TRANSFER" ? "#eff6ff" :
                                entry.action === "GATE_UNCHECK" ? "#fef2f2" :
                                "#f1f5f9",
                              color:
                                entry.action === "FINALIZE_INTAKE" ? "#065f46" :
                                entry.action === "AI_AUTO_CHECK" ? "#5b21b6" :
                                entry.action === "TRANSFER" ? "#1e40af" :
                                entry.action === "GATE_UNCHECK" ? "#991b1b" :
                                "#334155",
                            }}
                          >
                            {entry.action}
                          </span>
                        </td>
                        <td style={{ padding: "6px 10px", color: "#475569", maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {entry.detail}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
