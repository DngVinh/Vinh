import React, { useState } from "react";
import { BuildingIcon, ClockIcon } from "../../components/Icons";

export interface RoomSlot {
  id: string;
  name: string;
  capacity: number;
  timeSlot: string;
  isAvailable: boolean;
  conflictReason?: string;
}

export interface RoomBookingProps {
  rooms?: RoomSlot[];
  onBook?: (roomId: string) => void;
}

export function RoomBooking({ rooms = [], onBook }: RoomBookingProps) {
  const [filterCapacity, setFilterCapacity] = useState<number>(0);

  const filteredRooms = rooms.filter((r) => r.capacity >= filterCapacity);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
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

      {/* Room Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "20px" }}>
        {filteredRooms.map((room) => {
          const shortName = room.name.replace("Phòng ", "");
          return (
            <div
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
                onClick={() => onBook?.(room.id)}
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
            </div>
          );
        })}
      </div>
    </div>
  );
}
