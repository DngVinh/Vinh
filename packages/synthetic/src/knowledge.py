from __future__ import annotations

import hashlib
import json
from typing import Any
import uuid

HUCE_KNOWLEDGE_TOPICS = [
    {
        "source_key": "hoc_phi",
        "name": "Quy định Học phí HUCE 2026-2027",
        "uri": "https://demo.huce.example/policy/hoc-phi-2026",
        "title": "Quy định mức thu học phí và chính sách miễn giảm năm học 2026-2027",
        "text": (
            "Trường Đại học Xây dựng Hà Nội (HUCE) thông báo quy định học phí năm học 2026-2027:\n"
            "1. Mức học phí tiêu chuẩn đối với chương trình đào tạo đại học chính quy là 480.000 VNĐ / tín chỉ.\n"
            "2. Học phí các lớp chất lượng cao và chương trình liên kết là 750.000 VNĐ / tín chỉ.\n"
            "3. Thời hạn nộp học phí học kỳ 1: trước ngày 30 tháng 10 năm 2026. Sinh viên nộp qua cổng thanh toán số HUCE.\n"
            "4. Chính sách miễn giảm: Sinh viên thuộc hộ nghèo, con thương binh liệt sĩ được miễn giảm 100% hoặc 50% theo Nghị định 81."
        ),
    },
    {
        "source_key": "tin_chi",
        "name": "Quy chế Đào tạo Tín chỉ HUCE",
        "uri": "https://demo.huce.example/policy/quy-che-tin-chi",
        "title": "Quy chế đào tạo đại học theo học chế tín chỉ",
        "text": (
            "Quy chế đào tạo tín chỉ tại Trường Đại học Xây dựng Hà Nội (HUCE):\n"
            "1. Sinh viên phải đăng ký tối thiểu 14 tín chỉ trong mỗi học kỳ chính, tối đa 24 tín chỉ.\n"
            "2. Hủy môn học hoặc rút bớt học phần: thực hiện trong 2 tuần đầu học kỳ qua cổng sinh viên portal.\n"
            "3. Điểm đánh giá gồm: chuyên cần (10%), kiểm tra giữa kỳ (30%) và thi kết thúc học phần (60%).\n"
            "4. Điều kiện cảnh báo học tập: Điểm trung bình tích lũy CPA dưới 1.20 ở năm thứ nhất hoặc dưới 1.40 ở năm thứ hai."
        ),
    },
    {
        "source_key": "thu_tuc_giay_to",
        "name": "Thủ tục Hành chính và Giấy tờ Sinh viên",
        "uri": "https://demo.huce.example/policy/giay-to-sinh-vien",
        "title": "Hướng dẫn cấp giấy chứng nhận sinh viên và bảng điểm",
        "text": (
            "Phòng Quản lý Đào tạo HUCE hướng dẫn thủ tục xin cấp giấy tờ:\n"
            "1. Giấy xác nhận là sinh viên (vay vốn ngân hàng, tạm hoãn nghĩa vụ quân sự): tiếp nhận online và trả sau 2 ngày làm việc.\n"
            "2. Cấp bảng điểm học tập: nộp yêu cầu trực tuyến trên cổng Campus 24/7, lệ phí 20.000 VNĐ / bản.\n"
            "3. Nơi nhận kết quả trực tiếp: Bộ phận Một cửa - Tầng 1 Nhà H1 Đại học Xây dựng Hà Nội."
        ),
    },
    {
        "source_key": "muon_phong_hoc",
        "name": "Quy định Sử dụng Giảng đường và Phòng học",
        "uri": "https://demo.huce.example/policy/muon-phong-hoc",
        "title": "Quy định mượn phòng học, giảng đường H1, H2, H3",
        "text": (
            "Quy định đặt và mượn phòng học phục vụ học nhóm, sinh hoạt câu lạc bộ tại HUCE:\n"
            "1. Đối tượng áp dụng: Cán bộ lớp, Bí thư chi đoàn, Chủ nhiệm CLB sinh viên trực thuộc trường.\n"
            "2. Các phòng học cho phép đặt: Khu giảng đường H1, H2, H3 và Hội trường G3 (cần phê duyệt bổ sung).\n"
            "3. Thời gian gửi đăng ký mượn phòng: tối thiểu trước 24 giờ kể từ thời điểm bắt đầu sử dụng."
        ),
    },
    {
        "source_key": "khan_cap_y_te",
        "name": "Quy trình Xử lý Khẩn cấp và Hỗ trợ Y tế",
        "uri": "https://demo.huce.example/policy/ho-tro-y-te-khan-cap",
        "title": "Hướng dẫn ứng phó khẩn cấp y tế và tâm lý sinh viên",
        "text": (
            "Quy trình xử lý khẩn cấp tại Đại học Xây dựng Hà Nội (HUCE):\n"
            "1. Trạm Y tế trường: Tầng 1 Nhà A1, Hotline trực 24/7: 024-3869-XXXX.\n"
            "2. Hỗ trợ tư vấn tâm lý học đường: Phòng Công tác Sinh viên (Tầng 2 Nhà H1).\n"
            "3. Bất kỳ tình huống khẩn cấp, đe dọa an toàn hoặc khủng hoảng sức khỏe, hệ thống tự động chuyển tiếp tới cán bộ trực ban."
        ),
    },
    {
        "source_key": "tot_nghiep",
        "name": "Quy định Xét và Công nhận Tốt nghiệp HUCE",
        "uri": "https://demo.huce.example/policy/xet-tot-nghiep",
        "title": "Điều kiện xét tốt nghiệp và cấp bằng kỹ sư, cử nhân",
        "text": (
            "Điều kiện xét công nhận tốt nghiệp đại học chính quy tại Đại học Xây dựng Hà Nội (HUCE):\n"
            "1. Tích lũy đủ số tín chỉ quy định của chương trình đào tạo (từ 130 đến 155 tín chỉ tùy ngành).\n"
            "2. Điểm trung bình tích lũy toàn khóa (CPA) đạt từ 2.00 trở lên theo thang điểm 4.\n"
            "3. Đạt chuẩn đầu ra Ngoại ngữ (TOEIC 450 hoặc tương đương) và Tin học chuẩn quốc tế (MOS/IC3).\n"
            "4. Hoàn thành chứng chỉ Giáo dục Thể chất và Giáo dục Quốc phòng - An ninh.\n"
            "5. Không bị truy cứu trách nhiệm hình sự hoặc đang trong thời gian bị kỷ luật từ mức đình chỉ học tập."
        ),
    },
    {
        "source_key": "hoc_bong",
        "name": "Chính sách Học bổng Khuyến khích Học tập",
        "uri": "https://demo.huce.example/policy/hoc-bong-khuyen-khich",
        "title": "Tiêu chuẩn và mức xét cấp học bổng khuyến khích học kỳ",
        "text": (
            "Quy định xét cấp học bổng khuyến khích học tập tại HUCE theo từng kỳ học chính:\n"
            "1. Học bổng loại Xuất sắc: Điểm GPA học kỳ >= 3.60 và Điểm rèn luyện >= 90; mức học bổng bằng 120% học phí.\n"
            "2. Học bổng loại Giỏi: Điểm GPA học kỳ >= 3.20 và Điểm rèn luyện >= 80; mức học bổng bằng 100% học phí.\n"
            "3. Học bổng loại Khá: Điểm GPA học kỳ >= 2.50 và Điểm rèn luyện >= 70; mức học bổng bằng 80% học phí.\n"
            "4. Điều kiện tiên quyết: Sinh viên phải đăng ký tối thiểu 14 tín chỉ trong kỳ xét và không có học phần nào bị điểm F."
        ),
    },
    {
        "source_key": "diem_ren_luyen",
        "name": "Quy chế Đánh giá Điểm Rèn luyện Sinh viên",
        "uri": "https://demo.huce.example/policy/diem-ren-luyen",
        "title": "Quy trình tự đánh giá và xếp loại điểm rèn luyện theo Thông tư 10",
        "text": (
            "Quy định đánh giá kết quả rèn luyện của sinh viên HUCE theo thang điểm 100:\n"
            "1. Khung đánh giá gồm 5 tiêu chí: Ý thức học tập (tối đa 20đ), Chấp hành nội quy (tối đa 25đ), Hoạt động đoàn thể/cộng đồng (tối đa 20đ), Phẩm chất công dân (tối đa 25đ), Phụ trách tập thể/khen thưởng (tối đa 10đ).\n"
            "2. Phân loại rèn luyện: Xuất sắc (90-100đ), Tốt (80-89đ), Khá (65-79đ), Trung bình (50-64đ), Yếu (35-49đ), Kém (<35đ).\n"
            "3. Quy trình thực hiện: Sinh viên tự chấm trên cổng portal trước tuần 3 sau khi kết thúc học kỳ, sau đó họp chi đoàn/lớp bình xét và hội đồng khoa duyệt."
        ),
    },
    {
        "source_key": "canh_bao_hoc_tap",
        "name": "Quy định Cảnh báo Học tập và Buộc thôi học",
        "uri": "https://demo.huce.example/policy/canh-bao-hoc-tap",
        "title": "Các mức cảnh báo kết quả học tập và xử lý học vụ theo tín chỉ",
        "text": (
            "Quy định cảnh báo kết quả học tập tại HUCE theo Thông tư 08/2021/TT-BGDĐT:\n"
            "1. Cảnh báo mức 1: Điểm GPA học kỳ < 1.00 đối với học kỳ đầu; < 1.10 đối với các học kỳ tiếp theo; hoặc CPA < 1.20 (năm 1), < 1.40 (năm 2), < 1.60 (năm 3), < 1.80 (các năm cuối).\n"
            "2. Cảnh báo mức 2: Sinh viên bị cảnh báo mức 1 liên tiếp 2 học kỳ chính.\n"
            "3. Buộc thôi học: Sinh viên bị cảnh báo học tập liên tiếp 3 lần, hoặc vượt quá thời gian tối đa được phép học tập tại trường (tối đa 6 năm đối với hệ 4 năm, 7.5 năm đối với hệ 5 năm)."
        ),
    },
    {
        "source_key": "phuc_khao_hoan_thi",
        "name": "Quy trình Phúc khảo Điểm và Hoãn thi",
        "uri": "https://demo.huce.example/policy/phuc-khao-hoan-thi",
        "title": "Hướng dẫn nộp đơn xin phúc khảo bài thi và hoãn thi kết thúc học phần",
        "text": (
            "Thủ tục phúc khảo và hoãn thi tại Phòng Khảo thí & ĐBCL Giáo dục HUCE:\n"
            "1. Đơn xin hoãn thi: Nộp trực tuyến hoặc tại Bộ phận Một cửa trước buổi thi tối thiểu 01 ngày kèm theo minh chứng hợp lệ (giấy viện, triệu tập nghĩa vụ, việc hiếu).\n"
            "2. Điểm môn hoãn thi: Được ghi nhận điểm 'I' (chưa hoàn thành), sinh viên phải thi bù vào đợt thi gần nhất trong vòng 01 học kỳ kế tiếp.\n"
            "3. Đơn xin phúc khảo bài thi: Nộp trong vòng 07 ngày làm việc kể từ ngày công bố điểm thi trên hệ thống portal. Kết quả phúc khảo được công bố sau tối đa 15 ngày làm việc."
        ),
    },
    {
        "source_key": "song_bang_chuyen_nganh",
        "name": "Quy chế Học cùng lúc Hai chương trình và Chuyển ngành",
        "uri": "https://demo.huce.example/policy/song-bang-chuyen-nganh",
        "title": "Điều kiện đăng ký học song bằng và xin chuyển ngành đào tạo",
        "text": (
            "Quy chế học văn bằng thứ hai và chuyển ngành tại Đại học Xây dựng Hà Nội:\n"
            "1. Học cùng lúc hai chương trình (Song bằng): Sinh viên đã hoàn thành năm thứ nhất, điểm CPA tích lũy đạt từ 2.50 trở lên và không bị cảnh báo học tập; được công nhận chuyển đổi các học phần tương đương.\n"
            "2. Điều kiện chuyển ngành học: Sinh viên học hết năm thứ nhất, không bị cảnh báo học tập, điểm trúng tuyển của ngành chuyển đến không cao hơn điểm trúng tuyển ngành đang học tại kỳ thi tuyển sinh.\n"
            "3. Thời hạn nộp hồ sơ xin chuyển ngành/học song bằng: Trong 02 tuần trước khi bắt đầu học kỳ mới tại Phòng Đào tạo."
        ),
    },
    {
        "source_key": "ky_tuc_xa",
        "name": "Quy định Quản lý và Đăng ký Nội trú Ký túc xá",
        "uri": "https://demo.huce.example/policy/ky-tuc-xa",
        "title": "Chính sách ưu tiên và thủ tục đăng ký phòng ở Ký túc xá HUCE",
        "text": (
            "Quy định xét duyệt chỗ ở tại Ký túc xá Đại học Xây dựng Hà Nội (Đường Trần Đại Nghĩa):\n"
            "1. Đối tượng ưu tiên: Con liệt sĩ, thương bệnh binh, sinh viên khuyết tật, sinh viên dân tộc thiểu số, hộ nghèo/cận nghèo và tân sinh viên khóa mới ở xa.\n"
            "2. Thời gian tiếp nhận đơn nội trú: Đầu mỗi năm học (tháng 8 đối với khóa cũ, tháng 9 đối với tân sinh viên) qua cổng quản lý ký túc xá trực tuyến.\n"
            "3. Nội quy an toàn: Nghiêm cấm sử dụng thiết bị điện công suất lớn không phép, nấu ăn bằng bếp gas trong phòng, cấm mang chất dễ cháy nổ hoặc người lạ vào phòng ở sau 22h30."
        ),
    },
    {
        "source_key": "tam_hoan_nghia_vu",
        "name": "Thủ tục Cấp giấy Tạm hoãn Nghĩa vụ Quân sự",
        "uri": "https://demo.huce.example/policy/tam-hoan-nghia-vu",
        "title": "Hướng dẫn xin cấp giấy xác nhận tạm hoãn gọi nhập ngũ cho nam sinh viên",
        "text": (
            "Thủ tục cấp Giấy chứng nhận sinh viên phục vụ tạm hoãn gọi nhập ngũ tại HUCE:\n"
            "1. Đối tượng áp dụng: Nam sinh viên hệ đại học chính quy trong độ tuổi gọi nhập ngũ đang theo học trong thời gian đào tạo chuẩn.\n"
            "2. Thời điểm cấp định kỳ: Nhà trường tổ chức cấp tập trung vào đợt khám tuyển nghĩa vụ quân sự hàng năm (từ ngày 15/9 đến 30/10).\n"
            "3. Quy trình cấp trực tuyến: Sinh viên gửi yêu cầu trên cổng Campus 24/7, đính kèm thông tin Ban Chỉ huy Quân sự cấp quận/huyện; nhận bản ký số qua email sinh viên hoặc bản giấy đóng dấu mộc tại Phòng Một cửa H1 sau 02 ngày làm việc."
        ),
    },
    {
        "source_key": "do_an_tot_nghiep_cntt",
        "name": "Quy định Làm Đồ án Tốt nghiệp Khoa CNTT",
        "uri": "https://demo.huce.example/policy/do-an-tot-nghiep-cntt",
        "title": "Điều kiện nhận đề tài và quy trình bảo vệ đồ án tốt nghiệp ngành CNTT",
        "text": (
            "Quy định giao và bảo vệ đồ án tốt nghiệp đối với sinh viên Khoa CNTT HUCE:\n"
            "1. Điều kiện nhận đồ án: Sinh viên đã tích lũy tối thiểu 120 tín chỉ, CPA tích lũy >= 2.00, không bị nợ các học phần tiên quyết thuộc khối ngành cốt lõi.\n"
            "2. Thời gian thực hiện: Kéo dài 15 tuần kể từ ngày có quyết định giao đề tài của Hiệu trưởng.\n"
            "3. Điều kiện bảo vệ trước hội đồng: Hoàn thành báo cáo đúng hạn, nộp bản cứng và mã nguồn demo, có xác nhận đồng ý cho bảo vệ của giảng viên hướng dẫn và giảng viên phản biện (điểm phản biện >= 5.0/10)."
        ),
    },
    {
        "source_key": "chuan_dau_ra_ngoai_ngu",
        "name": "Quy định Chuẩn đầu ra Ngoại ngữ và Tin học",
        "uri": "https://demo.huce.example/policy/chuan-dau-ra",
        "title": "Bảng quy đổi chứng chỉ ngoại ngữ và chuẩn công nghệ thông tin HUCE",
        "text": (
            "Quy định chuẩn đầu ra đối với sinh viên đại học chính quy tại HUCE:\n"
            "1. Chuẩn Ngoại ngữ: Điểm TOEIC quốc tế tối thiểu 450, hoặc VSTEP B1 (Bậc 3 Khung 6 bậc Việt Nam), hoặc IELTS 4.5, hoặc chứng chỉ tiếng Pháp DELF A2 (đối với lớp Pháp ngữ).\n"
            "2. Chuẩn Tin học: Chứng chỉ ứng dụng CNTT nâng cao theo chuẩn Bộ Thông tin & Truyền thông, hoặc chứng chỉ quốc tế MOS (tối thiểu 2 bài thi Word và Excel đạt từ 700/1000) hoặc IC3.\n"
            "3. Thời hạn nộp hồ sơ xét chuẩn: Trước kỳ xét tốt nghiệp tối thiểu 30 ngày tại Phòng Khảo thí & ĐBCL Giáo dục."
        ),
    },
]


def _deterministic_uuid7(seed_val: str) -> str:
    h = hashlib.sha256(seed_val.encode("utf-8")).digest()
    raw = bytearray(h[:16])
    raw[6] = (raw[6] & 0x0F) | 0x70  # Version 7
    raw[8] = (raw[8] & 0x3F) | 0x80  # Variant
    return str(uuid.UUID(bytes=bytes(raw)))


from pathlib import Path


def generate_knowledge_corpus(seed: int = 2026, include_courses: bool = False) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    topics = list(HUCE_KNOWLEDGE_TOPICS)
    if include_courses:
        sample_file = Path(__file__).resolve().parents[1] / "samples" / "course_topics.json"
        if sample_file.exists():
            with open(sample_file, "r", encoding="utf-8") as f:
                topics.extend(json.load(f))

    for idx, item in enumerate(topics):
        source_id = _deterministic_uuid7(f"src-{seed}-{item['source_key']}")
        doc_version_id = _deterministic_uuid7(f"doc-ver-{seed}-{item['source_key']}")

        text_content = item["text"]
        content_hash = f"sha256:{hashlib.sha256(text_content.encode('utf-8')).hexdigest()}"

        sources.append(
            {
                "source_id": source_id,
                "name": item["name"],
                "source_type": "policy",
                "uri": item["uri"],
                "quarantine_status": "released",
            }
        )

        documents.append(
            {
                "document_version_id": doc_version_id,
                "source_id": source_id,
                "version_tag": "1.0.0",
                "title": item["title"],
                "raw_text": text_content,
                "canonical_hash": content_hash,
                "effective_from": "2026-09-01T00:00:00+07:00",
            }
        )

    return {
        "seed": seed,
        "sources": sources,
        "documents": documents,
    }
