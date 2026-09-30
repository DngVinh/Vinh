import React, { useState } from "react";
import { BuildingIcon, ClockIcon, CheckCircle2Icon, ArrowRightIcon } from "../../components/Icons";
import { ActionOutcome, type ActionState } from "../../components/ActionOutcome";

export interface RoomSlot {
  id: string;
  name: string;
  capacity: number;
  timeSlot: string;
  isAvailable: boolean;
  conflictReason?: string;
  accessibility?: string;
  equipment?: string;
}

export interface RoomBookingProps {
  rooms?: RoomSlot[];
  actionOutcomeState?: ActionState;
  idempotencyKey?: string;
  onBook?: (roomId: string) => void;
  onReconcile?: (idempotencyKey: string) => void;
}

export function RoomBooking({
  rooms = [],
  actionOutcomeState,
  idempotencyKey = "idem-room-default",
  onBook,
  onReconcile,
}: RoomBookingProps) {
  const [filterCapacity, setFilterCapacity] = useState<number>(0);
  const [selectedRoom, setSelectedRoom] = useState<RoomSlot | null>(null);
  const [bookingDate, setBookingDate] = useState<string>(() => {
    const d = new Date();
    return d.toISOString().split("T")[0];
  });
  const [bookingShift, setBookingShift] = useState<string>("morning");
  const [bookingPurpose, setBookingPurpose] = useState<string>("");

  const SHIFTS: Record<string, { label: string; time: string }> = {
    morning: { label: "Ca sáng", time: "07:00 - 11:30" },
    afternoon: { label: "Ca chiều", time: "13:00 - 17:00" },
    evening: { label: "Ca tối", time: "18:00 - 21:00" },
  };

  const filteredRooms = rooms.filter((room) => room.capacity >= filterCapacity);

  const handleConfirm = () => {
    if (selectedRoom) {
      onBook?.(selectedRoom.id);
      setSelectedRoom(null);
      setBookingPurpose("");
    }
  };

  if (selectedRoom) {
    return (
      <section
        aria-labelledby="booking-preview-heading"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "24px",
          backgroundColor: "#ffffff",
          padding: "32px",
          borderRadius: "var(--radius-xl, 20px)",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        }}
      >
        <div style={{ borderBottom: "1px solid var(--color-slate-100, #f1f5f9)", paddingBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
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
              <CheckCircle2Icon size={20} />
            </div>
            <h2
              id="booking-preview-heading"
              style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}
            >
              Xác nhận đăng ký mượn phòng học
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)" }}>
            Vui lòng kiểm tra kỹ thông tin phòng, mốc thời gian và điều kiện mượn trước khi gửi yêu cầu
          </p>
        </div>

        {/* Structured Booking Preview */}
        <dl
          style={{
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: "16px",
            backgroundColor: "var(--color-slate-50, #f8fafc)",
            padding: "20px",
            borderRadius: "var(--radius-lg, 14px)",
            border: "1px solid var(--color-slate-200, #e2e8f0)",
            margin: 0,
          }}
        >
          <div>
            <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Phòng đăng ký
            </dt>
            <dd style={{ margin: "4px 0 0 0", fontSize: "16px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
              {selectedRoom.name} ({selectedRoom.capacity} chỗ ngồi) - Khu giảng đường HUCE
            </dd>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px" }}>
            <div>
              <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
                Thời gian mượn (Giờ Việt Nam, UTC+7)
              </dt>
              <dd style={{ margin: "4px 0 0 0", fontSize: "14px", fontWeight: 600, color: "var(--color-slate-900, #0f172a)" }}>
                {selectedRoom.timeSlot}
              </dd>
            </div>

            <div>
              <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
                Hỗ trợ tiếp cận & Cơ sở vật chất
              </dt>
              <dd style={{ margin: "4px 0 0 0", fontSize: "14px", color: "var(--color-slate-700, #334155)" }}>
                {selectedRoom.accessibility || "Tiêu chuẩn"} · {selectedRoom.equipment || "Tiêu chuẩn"}
              </dd>
            </div>
          </div>

          <div>
            <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Quy trình phê duyệt
            </dt>
            <dd style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--color-slate-700, #334155)", lineHeight: 1.5 }}>
              Yêu cầu mượn phòng cần được Ban Quản lý Giảng đường xét duyệt (dự kiến phản hồi trong 24 giờ làm việc).
            </dd>
          </div>

          <div>
            <dt style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
              Quy định hủy mượn phòng
            </dt>
            <dd style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--color-slate-700, #334155)", lineHeight: 1.5 }}>
              Bạn có thể hủy đăng ký trước giờ bắt đầu tối thiểu 2 giờ mà không bị tính điểm phạt vi phạm quy chế cơ sở vật chất.
            </dd>
          </div>
        </dl>

        {/* Action Controls */}
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "12px", marginTop: "8px" }}>
          <button
            type="button"
            onClick={() => setSelectedRoom(null)}
            style={{
              padding: "10px 18px",
              minHeight: "44px",
              borderRadius: "var(--radius-md, 10px)",
              border: "1px solid var(--color-slate-300, #cbd5e1)",
              backgroundColor: "#ffffff",
              color: "var(--color-slate-700, #334155)",
              fontSize: "14px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
            }}
          >
            Quay lại danh sách phòng
          </button>

          <button
            type="button"
            onClick={handleConfirm}
            style={{
              padding: "12px 28px",
              minHeight: "44px",
              backgroundColor: "var(--color-primary, #1e3a8a)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-md, 10px)",
              fontWeight: 600,
              fontSize: "14px",
              cursor: "pointer",
              boxShadow: "var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.06))",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
            }}
          >
            <span>Xác nhận đặt phòng</span>
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </section>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Ambiguous or Completed Action Outcome Banner (AC-TASK-WEB-RESULT-001) */}
      {actionOutcomeState && (
        <ActionOutcome
          state={actionOutcomeState}
          idempotencyKey={idempotencyKey}
          actionTitle="Đăng ký mượn phòng học"
          onReconcile={onReconcile}
        />
      )}

      {/* Header and Filter */}
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
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
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
              <BuildingIcon size={20} />
            </div>
            <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)", letterSpacing: "-0.3px" }}>
              Tra cứu & Đăng ký mượn phòng học
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)" }}>
            Tra cứu phòng học trống, giảng đường lớn và phòng tự học phục vụ sinh hoạt học thuật HUCE
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <label htmlFor="capacity-filter" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
            Sức chứa tối thiểu:
          </label>
          <select
            id="capacity-filter"
            value={filterCapacity}
            onChange={(e) => setFilterCapacity(Number(e.target.value))}
            style={{
              padding: "8px 14px",
              borderRadius: "var(--radius-md, 10px)",
              border: "1.5px solid var(--color-slate-300, #cbd5e1)",
              backgroundColor: "#ffffff",
              fontSize: "13px",
              color: "var(--color-slate-900, #0f172a)",
              outline: "none",
              cursor: "pointer",
              boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
            }}
          >
            <option value={0}>Tất cả quy mô</option>
            <option value={50}>Từ 50+ chỗ ngồi</option>
            <option value={100}>Hội trường 100+ chỗ</option>
          </select>
        </div>
      </div>

      {/* Date + Shift Selector Bar */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "16px",
          alignItems: "flex-end",
          backgroundColor: "#ffffff",
          padding: "16px 20px",
          borderRadius: "var(--radius-lg, 14px)",
          border: "1px solid var(--color-slate-200, #e2e8f0)",
          boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <label htmlFor="booking-date" style={{ fontSize: "12px", fontWeight: 700, color: "var(--color-slate-600, #475569)", textTransform: "uppercase" }}>
            Ngày mượn
          </label>
          <input
            id="booking-date"
            type="date"
            value={bookingDate}
            onChange={(e) => setBookingDate(e.target.value)}
            min={new Date().toISOString().split("T")[0]}
            style={{
              padding: "8px 14px",
              borderRadius: "var(--radius-md, 10px)",
              border: "1.5px solid var(--color-slate-300, #cbd5e1)",
              fontSize: "13px",
              cursor: "pointer",
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--color-slate-600, #475569)", textTransform: "uppercase" }}>
            Ca mượn
          </span>
          <div style={{ display: "flex", gap: "6px" }}>
            {Object.entries(SHIFTS).map(([key, shift]) => (
              <button
                key={key}
                type="button"
                onClick={() => setBookingShift(key)}
                style={{
                  padding: "6px 14px",
                  borderRadius: "var(--radius-md, 10px)",
                  border: bookingShift === key ? "1.5px solid var(--color-primary, #1e3a8a)" : "1px solid var(--color-slate-200, #e2e8f0)",
                  backgroundColor: bookingShift === key ? "var(--color-primary-light, #eff6ff)" : "#ffffff",
                  color: bookingShift === key ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-600, #475569)",
                  fontWeight: bookingShift === key ? 700 : 500,
                  fontSize: "12px",
                  cursor: "pointer",
                  transition: "all 150ms ease",
                }}
              >
                <div>{shift.label}</div>
                <div style={{ fontSize: "10px", opacity: 0.7 }}>{shift.time}</div>
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "4px", flex: 1, minWidth: "200px" }}>
          <label htmlFor="booking-purpose" style={{ fontSize: "12px", fontWeight: 700, color: "var(--color-slate-600, #475569)", textTransform: "uppercase" }}>
            Mục đích mượn
          </label>
          <input
            id="booking-purpose"
            type="text"
            value={bookingPurpose}
            onChange={(e) => setBookingPurpose(e.target.value)}
            placeholder="VD: Họp nhóm đồ án, Sinh hoạt CLB..."
            style={{
              padding: "8px 14px",
              borderRadius: "var(--radius-md, 10px)",
              border: "1.5px solid var(--color-slate-300, #cbd5e1)",
              fontSize: "13px",
            }}
          />
        </div>
      </div>

      {/* Room Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "20px" }}>
        {filteredRooms.map((room) => {
          const shortName = room.name.replace("Phòng ", "");
          return (
            <article
              key={room.id}
              style={{
                border: "1px solid var(--color-slate-200, #e2e8f0)",
                borderRadius: "var(--radius-lg, 14px)",
                padding: "24px",
                backgroundColor: "#ffffff",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
                boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
                transition: "var(--transition-spring, 220ms cubic-bezier(0.16, 1, 0.3, 1))",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                <div>
                  <h3 style={{ margin: "0 0 4px 0", fontSize: "17px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                    {room.name} ({room.capacity} chỗ)
                  </h3>
                  <div style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)", fontWeight: 500 }}>
                    Khu giảng đường HUCE
                  </div>
                </div>

                <span
                  style={{
                    fontSize: "12px",
                    padding: "3px 10px",
                    borderRadius: "var(--radius-full, 9999px)",
                    fontWeight: 600,
                    backgroundColor: room.isAvailable ? "#ecfdf5" : "#fef2f2",
                    color: room.isAvailable ? "#065f46" : "#991b1b",
                    border: `1px solid ${room.isAvailable ? "#a7f3d0" : "#fecaca"}`,
                    whiteSpace: "nowrap",
                  }}
                >
                  {room.isAvailable ? "Còn trống" : "Trùng lịch"}
                </span>
              </div>

              <div
                style={{
                  fontSize: "13px",
                  color: "var(--color-slate-700, #334155)",
                  backgroundColor: "var(--color-slate-50, #f8fafc)",
                  padding: "10px 14px",
                  borderRadius: "var(--radius-md, 10px)",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  border: "1px solid var(--color-slate-200, #e2e8f0)",
                }}
              >
                <ClockIcon size={15} style={{ color: "var(--color-slate-500, #64748b)" }} />
                <span>Ca mượn: <strong>{room.timeSlot}</strong></span>
              </div>

              {/* Accessibility and Equipment Facts */}
              <div style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
                {room.accessibility && (
                  <div>
                    <span style={{ fontWeight: 600 }}>Tiếp cận:</span> {room.accessibility}
                  </div>
                )}
                {room.equipment && (
                  <div>
                    <span style={{ fontWeight: 600 }}>Thiết bị:</span> {room.equipment}
                  </div>
                )}
              </div>

              {!room.isAvailable && room.conflictReason && (
                <div
                  role="alert"
                  style={{
                    fontSize: "12px",
                    color: "#991b1b",
                    backgroundColor: "#fef2f2",
                    border: "1px solid #fecaca",
                    padding: "10px 14px",
                    borderRadius: "var(--radius-md, 10px)",
                    lineHeight: 1.5,
                  }}
                >
                  Lý do: {room.conflictReason}
                </div>
              )}

              <button
                type="button"
                onClick={() => setSelectedRoom(room)}
                disabled={!room.isAvailable}
                aria-label={
                  room.isAvailable
                    ? `Đăng ký mượn ${shortName}`
                    : `Đã có lịch - ${shortName}`
                }
                style={{
                  marginTop: "auto",
                  padding: "11px 18px",
                  borderRadius: "var(--radius-md, 10px)",
                  border: "none",
                  backgroundColor: room.isAvailable ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-200, #e2e8f0)",
                  color: room.isAvailable ? "#ffffff" : "var(--color-slate-500, #64748b)",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: room.isAvailable ? "pointer" : "not-allowed",
                  minHeight: "44px",
                  boxShadow: room.isAvailable ? "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))" : "none",
                  transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                }}
              >
                {room.isAvailable ? "Đăng ký mượn phòng" : "Không khả dụng"}
              </button>
            </article>
          );
        })}
      </div>
    </div>
  );
}
