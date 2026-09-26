---
document_id: "DOC-UX-REDESIGN-PLAN-001"
version: "0.1.0"
status: "draft"
owner: "Product and UX"
approvers: ["Product Owner", "UX Owner", "Accessibility Owner", "Security Owner"]
last_updated: "2026-09-26"
---

# Campus 24/7 — kế hoạch làm lại giao diện cho Antigravity 3.8 Flash

## Mục tiêu

Xây lại trải nghiệm web theo hướng hiện đại, học đường, tối giản, dễ đọc và đáng tin. Có thể thay bố cục, hệ màu, typography, component và điều hướng hiện có. Giữ nguyên nghĩa vụ sản phẩm đã được phê duyệt: quyền theo vai trò, dữ liệu giả lập, công bố trạng thái demo không chính thức, trích dẫn có thể kiểm tra, và mọi thao tác ghi đều có xem trước, xác nhận, idempotency và audit. Không coi UI hiện tại là chuẩn thiết kế.

Đây là **kế hoạch và backlog bản nháp**, chưa là lệnh triển khai. Tất cả tài liệu `docs/03-ux/**` hiện có trạng thái `draft`; theo `docs/00-governance/DOCUMENT_CONTROL.md`, chúng phải được duyệt trước khi task phụ thuộc vào chúng được chuyển sang `ready`. Nếu bản thiết kế mới thay đổi hành vi, route, hợp đồng, quyền, thông điệp an toàn hoặc yêu cầu, trình bản thay đổi cho đúng chủ sở hữu phê duyệt rồi mới thực thi. Không sửa nguồn cấp cao hơn để hợp thức hóa code.

## Đầu vào và hướng thiết kế

1. Kiểm kê từng màn hình, hành trình và trạng thái trong `docs/03-ux/SCREEN_INVENTORY.md`, `INFORMATION_ARCHITECTURE.md`, `UI_STATE_MATRIX.yaml`; đối chiếu route và component thực tế. Liệt kê chỗ lệch, không tự tạo route.
2. Thiết kế một hệ thống thị giác riêng cho môi trường học đường: nền sáng trung tính, màu nhấn rõ nhưng tiết chế, chữ Việt dễ đọc, phân cấp nội dung, khoảng trắng, icon nhất quán, dark mode chỉ khi được duyệt. Không dùng màu làm tín hiệu duy nhất. Không dùng ảnh trang trí gây nhiễu tác vụ.
3. Ưu tiên nhu cầu: sinh viên nhận biết việc cần làm, tìm thông tin, xem lịch, theo dõi yêu cầu; nhân viên xử lý hàng đợi; người phụ trách tri thức và vận hành thấy dữ liệu có nguồn và trạng thái. Giữ tác vụ chính nổi bật theo ngữ cảnh, giảm lựa chọn và chữ thừa có kiểm chứng.
4. Mọi màn hình có trạng thái loading, rỗng, lỗi, mất mạng, dữ liệu cũ, kết quả chưa xác định, không có quyền khi phù hợp; hành động nguy hiểm không bao giờ hiển thị thành công giả. Dữ liệu mô phỏng phải được dán nhãn rõ.
5. Thiết kế responsive cho điện thoại, tablet và desktop; kiểm tra bàn phím, focus, trình đọc màn hình, 200% zoom và reflow. Link trong câu được xử lý theo ngoại lệ WCAG, không ép CSS kích thước nút lên mọi thẻ `a`.

## Cơ sở nghiên cứu và cách kiểm chứng

| Bằng chứng | Giả thuyết thiết kế cần thử | Cách kiểm chứng |
| --- | --- | --- |
| [Nielsen, cách người dùng đọc trên web](https://www.nngroup.com/articles/how-users-read-on-the-web/) | Tiêu đề có nghĩa, đoạn ngắn, thông tin quan trọng đặt sớm sẽ giúp tìm việc nhanh hơn. | Cho người dùng tìm lịch, nguồn trích dẫn và trạng thái yêu cầu; quan sát đường đi, sai sót và câu họ hiểu. |
| [Sweller, cognitive load](https://onlinelibrary.wiley.com/doi/10.1207/s15516709cog1202_4) | Chia tác vụ phức tạp thành bước có ngữ cảnh và chỉ hiển thị thông tin cần thiết có thể giảm gánh nặng xử lý. Đây là suy luận thiết kế, không phải bảo đảm hiệu quả cho sản phẩm này. | Thử biểu mẫu yêu cầu và xác nhận với người dùng thực; đo lỗi, bỏ dở và khả năng nhắc lại hệ quả của thao tác. |
| [W3C WCAG 2.2 Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) | Kích thước hoặc khoảng cách mục tiêu tương tác đúng chuẩn sẽ giảm bấm nhầm; áp dụng đúng các ngoại lệ cho inline link. | Kiểm tra tự động và bằng tay trên mobile, 200% zoom, thiết bị trỏ và bàn phím. |
| [GOV.UK moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) | Đánh giá bằng tác vụ thực sẽ phát hiện nhãn, bố cục và luồng khó hiểu. | Test có kịch bản với sinh viên và nhân viên, ghi bằng chứng, sửa điểm gây lỗi rồi thử lại. |

Không áp công thức số lượng tab, màu hay animation từ các nghiên cứu này. Chúng là giả thuyết và tiêu chí kiểm tra. “Đẹp nhất” phải được đánh giá qua khả năng hoàn thành tác vụ, khả năng tiếp cận và sự tin cậy, không chỉ cảm nhận của agent.

## Quy trình cho Antigravity

1. Đọc `AGENTS.md`, document control, yêu cầu đã duyệt, tài liệu UX liên quan, task YAML được giao, toàn bộ `inputs` và `traceability`. Kiểm tra `git status --short`, dependency đã `accepted`, task `ready`, approval cần thiết và write lease không giao nhau. Nếu chưa đạt, trả JSON `blocked` theo `tasks/task-output.schema.json`; không code.
2. Thực hiện **một** task ID mỗi lượt. Không mở rộng `write_scope`, không tự đổi requirement, contract, trạng thái tài liệu hay task. Nếu phải đập đi xây lại component trong phạm vi được phép, giữ dữ liệu, quyền, focus, trạng thái lỗi và nghĩa vụ an toàn.
3. Mỗi patch kèm kiểm tra trạng thái trước/sau, test tập trung, lint/typecheck khi thích hợp, bằng chứng ảnh/ghi hình trình duyệt tại desktop và mobile cho thay đổi thị giác. `vitest` jsdom không phải kiểm tra trình duyệt thật. Khi không có trình duyệt, báo `not_verified` cho phần nhìn/interaction cần kiểm tra bằng mắt.
4. Không dùng số điện thoại giả, điểm tin cậy phần trăm không có nghĩa được phê duyệt, token viết cứng hoặc màn hình báo thành công khi API lỗi. Chặn thay đổi nào cần hợp đồng hoặc bản sao nội dung an toàn chưa được phê duyệt.
5. Sau mỗi task, đối chiếu tiêu chí nghiệm thu với bằng chứng và trả đúng một JSON object. Tối đa hai cách sửa khác nhau khi triển khai thất bại.

## Thứ tự và giao việc

Backlog gồm 25 microtask: 4 cổng tài liệu, 20 task triển khai và 1 task bằng chứng trình duyệt.

1. **Cổng tài liệu hai bước:** trước hết, người có thẩm quyền cho phép đúng phạm vi của `TASK-DOC-UX-001` đến `004` được chuẩn bị và orchestrator chuyển từng task sang `ready`. Executor sửa tài liệu thành `reviewed`, cung cấp diff và bằng chứng nhưng không tự ghi `approved`. Sau đó Product/UX/Quality/Security/Accessibility owner duyệt chính nội dung cuối; chỉ khi đó tài liệu mới thành `approved`, task tài liệu được `accepted` và các wave code mới được mở.
2. **Nền tảng:** `TASK-WEB-DESIGN-002` → `TASK-WEB-A11Y-002` → `TASK-WEB-SHELL-002`; `TASK-WEB-STATE-002` có thể bắt đầu sau design và cổng state. Các task sửa cùng CSS hoặc AppShell phải chạy nối tiếp.
3. **Biên phiên và an toàn:** `TASK-WEB-AUTH-002` loại bỏ credential phía client theo boundary được duyệt; `TASK-WEB-SAFE-001` thay liên hệ giả bằng fallback đã được phê duyệt. Hai task này cần human approval riêng.
4. **Luồng sinh viên:** `TASK-WEB-HOME-002`, `TASK-WEB-CHAT-003`, `TASK-WEB-CITE-002`, `TASK-WEB-SCHED-002`, `TASK-WEB-TICK-002`, `TASK-WEB-DOCREQ-002`, `TASK-WEB-ROOM-002`, `TASK-WEB-PRIV-002`; tác vụ viết phải giữ preview/confirm/idempotency.
5. **Luồng nhân viên và quản trị:** `TASK-WEB-STAFF-002`, `TASK-WEB-KNOW-002`, `TASK-WEB-OPS-002`. Có thể chạy song song tối đa bốn task khi đường dẫn ghi và conflict key rời nhau.
6. **Loại bỏ thành công giả:** `TASK-WEB-SCHED-003`, `TASK-WEB-TICK-003`, `TASK-WEB-ROOM-003` sửa page adapter sau khi view và session boundary tương ứng đã sẵn sàng.
7. **QA cuối:** `TASK-TEST-WEB-002` kiểm tra hành trình bằng trình duyệt, bàn phím, 200% zoom và ba viewport; jsdom chỉ là bằng chứng unit/integration bổ trợ.

## Tiêu chuẩn nghiệm thu tổng thể

- Sinh viên hoàn thành ít nhất các tác vụ tìm thông tin có nguồn, xem lịch, tạo/xem yêu cầu, đặt phòng và quản lý quyền riêng tư; nhân viên thao tác hàng đợi đúng quyền; mọi lỗi có bước phục hồi rõ.
- Giao diện nhất quán ở 360/768/1280 CSS px, 200% zoom, bàn phím và công nghệ hỗ trợ; không có tràn ngang ngoài nội dung đặc thù được xử lý.
- Nút/lối đi chính rõ theo ngữ cảnh, không giấu giới hạn AI hoặc trạng thái demo, không tạo cảm giác xác nhận thành công khi chưa có kết quả backend.
- Unit/jsdom test, typecheck và kiểm tra trình duyệt thật có bằng chứng riêng. Các quyết định dựa trên nghiên cứu được ghi là giả thuyết cho đến khi người dùng thử hoàn thành hành trình.

## Vấn đề đã phát hiện và chốt trước khi giao

- Tài liệu UX và ma trận trạng thái còn `draft`, trong khi task cũ `accepted` có tham chiếu chúng. Cần owner rà lại nhất quán; không tự coi chúng là approved.
- UI hiện có số liên hệ mô phỏng trong `HandoverPanel`, thang điểm confidence ở `CitationDrawer`, một chuỗi bearer-like viết cứng trong trang chat và các nhánh thành công giả khi API lỗi ở lịch/phòng/ticket. Cần xử lý bằng task có phạm vi rõ, không in chuỗi token ra báo cáo.
- Route trong screen inventory không hoàn toàn trùng route hiện thực. Giữ route hiện có cho đợt đổi giao diện cho đến khi product/architecture duyệt thay đổi IA.
- Test thư mục `apps/web/e2e` hiện chạy bằng Vitest/jsdom. Không gọi kết quả đó là kiểm tra browser end-to-end.
