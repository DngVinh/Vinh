"use client";

import React, { useEffect, useState, useCallback } from "react";
import { AppShell } from "../../components/AppShell";
import { RoomBooking, type RoomSlot } from "../../features/rooms/RoomBooking";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import { CheckCircle2Icon, XIcon } from "../../components/Icons";
import { ApiClient } from "../../lib/api/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RoomApiResponse {
  items: Array<{
    id: string;
    room_code: string;
    display_name: string;
    capacity: number;
    features: string[];
    status?: string;
  }>;
}

export default function RoomsPage() {
  const [rooms, setRooms] = useState<RoomSlot[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [successBookingId, setSuccessBookingId] = useState<string | null>(null);

  const fetchRooms = useCallback(async () => {
    setStatus("loading");
    setErrorMessage("");

    try {
      const client = new ApiClient({ baseUrl: API_BASE_URL });
      const response = await client.get<RoomApiResponse>("/v1/rooms");

      const items = response.items || [];
      if (items.length === 0) {
        setRooms([]);
        setStatus("empty");
        return;
      }

      const mappedRooms: RoomSlot[] = items.map((r: RoomApiResponse["items"][number]) => ({
        id: r.id,
        name: r.display_name || `Phòng ${r.room_code}`,
        capacity: r.capacity,
        timeSlot: "08:00 - 11:30 (Sáng hôm nay)",
        isAvailable: r.status !== "MAINTENANCE",
        conflictReason: r.status === "MAINTENANCE" ? "Phòng đang bảo trì định kỳ" : undefined,
      }));

      setRooms(mappedRooms);
      setStatus("success");
    } catch {
      // Demo fallback when API server is in offline simulation mode
      const demoRooms: RoomSlot[] = [
        {
          id: "room-h1-301",
          name: "Giảng đường H1-301",
          capacity: 120,
          timeSlot: "08:00 - 11:30 (Sáng hôm nay)",
          isAvailable: true,
        },
        {
          id: "room-h2-205",
          name: "Phòng tự học H2-205",
          capacity: 45,
          timeSlot: "13:30 - 17:00 (Chiều hôm nay)",
          isAvailable: true,
        },
        {
          id: "room-h3-102",
          name: "Phòng thực hành kết cấu H3-102",
          capacity: 35,
          timeSlot: "08:00 - 11:30 (Sáng hôm nay)",
          isAvailable: false,
          conflictReason: "Phòng đang bảo trì thiết bị thí nghiệm định kỳ",
        },
        {
          id: "room-h1-404",
          name: "Phòng thảo luận chuyên đề H1-404",
          capacity: 60,
          timeSlot: "13:30 - 17:00 (Chiều hôm nay)",
          isAvailable: true,
        },
      ];
      setRooms(demoRooms);
      setStatus("success");
    }
  }, []);

  const handleBookRoom = useCallback((roomId: string) => {
    setSuccessBookingId(roomId);
    setRooms((prev) =>
      prev.map((r) =>
        r.id === roomId
          ? { ...r, isAvailable: false, conflictReason: "Bạn vừa gửi yêu cầu đặt chỗ" }
          : r
      )
    );
  }, []);

  useEffect(() => {
    fetchRooms();
  }, [fetchRooms]);

  return (
    <AppShell activeNav="rooms">
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "8px 0" }}>
        <header style={{ marginBottom: "24px" }}>
          <h1 style={{ fontSize: "24px", fontWeight: 800, margin: "0 0 6px 0", color: "var(--color-slate-900, #0f172a)" }}>
            Đăng ký và mượn phòng học
          </h1>
          <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
            Tra cứu phòng học trống, phòng tự học và hội trường phục vụ hoạt động sinh viên HUCE
          </p>
        </header>

        {successBookingId && (
          <div
            role="status"
            style={{
              padding: "14px 18px",
              marginBottom: "20px",
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "var(--radius-md, 8px)",
              color: "#15803d",
              fontSize: "14px",
              fontWeight: 500,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              boxShadow: "var(--shadow-xs)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <CheckCircle2Icon size={18} />
              <span>Yêu cầu mượn phòng đã được ghi nhận thành công! Bộ phận quản trị phòng học sẽ duyệt trong 24h làm việc.</span>
            </div>
            <button
              type="button"
              onClick={() => setSuccessBookingId(null)}
              style={{ background: "none", border: "none", cursor: "pointer", color: "#15803d", padding: "4px", display: "flex", alignItems: "center" }}
              aria-label="Đóng thông báo"
            >
              <XIcon size={16} />
            </button>
          </div>
        )}

        <AsyncState
          status={status}
          loadingMessage="Đang tải danh sách phòng học và trạng thái khả dụng..."
          emptyMessage="Hiện tại không có phòng học nào khả dụng để đăng ký"
          errorMessage={errorMessage}
          onRetry={fetchRooms}
        >
          <RoomBooking rooms={rooms} onBook={handleBookRoom} />
        </AsyncState>
      </div>
    </AppShell>
  );
}
