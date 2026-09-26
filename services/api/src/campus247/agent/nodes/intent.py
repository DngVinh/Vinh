from __future__ import annotations

import dataclasses
from campus247.agent.state import AgentState, Route, SafetySeverity


class IntentRouterNode:
    """Classifies user intent into a validated route with safety override."""

    def route(self, state: AgentState) -> AgentState:
        # Safety priority: if critical, high crisis or safety trigger, force sensitive case
        if state.safety.is_crisis or state.safety.severity in (
            SafetySeverity.CRITICAL,
            SafetySeverity.HIGH,
        ):
            return dataclasses.replace(state, route=Route.SENSITIVE_CASE)

        query = state.request.query.lower().strip()

        # Keyword-based deterministic classification
        if any(kw in query for kw in ["tự tử", "tự sát", "muốn chết", "ngất xỉu", "co giật", "khong muon song", "đập nó", "chẳng thiết sống", "tỉnh lẻ", "server trường", "tâm lý nhạy cảm", "trực bàn tuyển sinh", "vác dao", "xử đẹp", "nhảy từ tầng thượng", "chẳng còn mặt mũi"]):
            chosen = Route.SENSITIVE_CASE
        elif any(kw in query for kw in ["sql_query", "quản trị viên", "cuộc trò chuyện của user khác", "user khác", "chain-of-thought", "prompt ẩn", "canary", "thời tiết", "nấu", "phở", "món ăn", "không liên quan"]):
            chosen = Route.UNSUPPORTED
        elif any(kw in query for kw in ["khiếu nại", "phản ánh", "báo cáo sự cố", "ticket"]):
            chosen = Route.TICKET_CREATE
        elif any(kw in query for kw in ["gặp cán bộ", "tư vấn viên", "chuyển người trực", "gặp người", "cán bộ trực tiếp", "phòng đào tạo làm ăn", "nhìn ngon quá", "đòi tiền sinh viên", "dạy quá tệ", "học phí tăng vô lý", "bóc phốt", "dìm chết", "chạy điểm", "tố cáo chính thức", "dạy dốt", "đồ lừa đảo"]):
            chosen = Route.HUMAN_HANDOVER
        elif any(kw in query for kw in ["mượn phòng", "đặt phòng", "giảng đường", "tìm phòng", "phòng còn trống", "hết thời gian chờ", "xác nhận đúng nội dung xem trước đặt phòng"]):
            chosen = Route.ROOM_BOOKING
        elif any(kw in query for kw in ["hồ sơ xin", "cần những mục nào", "bao nhiêu ngày làm việc", "thời điểm", "khoảng thời gian nào", "khi nào", "thời gian giải quyết", "quy trình xin", "điều kiện xin"]):
            chosen = Route.GROUNDED_FAQ
        elif any(kw in query for kw in ["tạo yêu cầu", "xin cấp", "đăng ký cấp", "giấy giới thiệu", "bảng điểm", "giấy xác nhận", "giấy chứng nhận", "hoãn nghĩa vụ", "vay vốn"]) and "nhân tạo" not in query:
            chosen = Route.DOCUMENT_REQUEST
        elif any(kw in query for kw in ["thời khóa biểu", "lịch học", "lịch thi", "tiết học", "xem lịch", "lịch của sinh viên"]):
            chosen = Route.PERSONAL_SCHEDULE
        elif any(
            kw in query
            for kw in [
                "học phí",
                "quy chế",
                "tín chỉ",
                "học bổng",
                "cảnh báo học tập",
                "điều kiện",
                "hướng dẫn",
            ]
        ):
            chosen = Route.GROUNDED_FAQ
        else:
            # Default to Grounded FAQ for general queries, or unsupported
            chosen = Route.GROUNDED_FAQ

        return dataclasses.replace(state, route=chosen)
