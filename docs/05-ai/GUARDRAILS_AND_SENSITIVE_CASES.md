---
document_id: "DOC-AI-006"
version: "1.0.0"
status: "reviewed"
owner: "AI Safety Lead"
approvers: ["Security Architect", "Privacy Officer", "Student Services Owner", "AI Quality Lead"]
last_updated: "2026-09-21"
---

# Guardrails và sensitive-case classifier

## 1. Phạm vi

Guardrail giảm rủi ro nhưng không thay thế authorization, evidence gate hoặc người hỗ trợ. V1 dùng defense-in-depth:

```text
input limits
 -> deterministic rules
 -> sensitive classifier
 -> conservative merge
 -> route policy
 -> tool/evidence gates
 -> output guard
 -> telemetry + human review
```

## 2. Taxonomy

| Label | Ví dụ phạm vi | Default severity | Hành vi |
|---|---|---:|---|
| `self_harm_imminent` | ý định/kế hoạch tự hại sắp xảy ra | critical | safe template + official contact if configured + immediate handover policy |
| `violence_imminent` | đe dọa bạo lực cụ thể | critical | như trên, không điều tra/chẩn đoán |
| `medical_emergency` | triệu chứng khẩn cấp rõ ràng | critical | khuyến nghị liên hệ dịch vụ khẩn cấp approved; không chẩn đoán |
| `harassment_or_abuse` | quấy rối, bạo lực, xâm hại | high | privacy-minimized handover và approved guidance |
| `mental_health_distress` | khủng hoảng không rõ imminent | high | supportive non-diagnostic response + handover |
| `disciplinary_or_legal` | kỷ luật, tố cáo, pháp lý | high | không kết luận; chuyển cán bộ phù hợp |
| `academic_rights_impact` | đình chỉ, mất quyền, deadline ảnh hưởng lớn | high | source-grounded + staff review |
| `privacy_or_security_incident` | lộ tài khoản/dữ liệu, phishing | high/critical | security route; không yêu cầu gửi credential |
| `financial_impact` | học phí, hoàn tiền, nghĩa vụ tài chính | high | citation + human review khi ngoại lệ |
| `ordinary_service` | yêu cầu thông thường | normal | normal graph |

Severity final = mức cao nhất từ rule, classifier và contextual policy. Classifier không được hạ severity do deterministic rule đã nâng.

## 3. Sensitive classifier contract

Input chỉ gồm current user text và tối đa bounded recent context đã redaction. Output:

```yaml
schema_version: "1.0"
severity: "critical|high|normal"
labels: ["allowlisted_label"]
confidence: 0.0
immediacy: "immediate|possible|not_indicated|unknown"
target: "self|other|unknown|none"
handover_recommended: true
reason_codes: ["allowlisted_non-sensitive_code"]
```

- `confidence` chỉ phục vụ calibration, không là bằng chứng an toàn.
- Parse/schema failure MUST dùng rule output; nếu rule không đủ và text có high-risk lexical signal, default `high`.
- Critical recall được ưu tiên hơn precision; false positive phải được đo để tránh quá tải queue.
- Classifier MUST không sinh user-facing advice.

## 4. Prompt injection guardrail

Detectors SHOULD flag nhưng MUST không được coi là “chặn hoàn hảo”. Controls bắt buộc:

- instruction hierarchy cố định;
- untrusted content labeling;
- metadata/source authorization trước retrieval;
- tool allowlist per route;
- strict schema + semantic validation;
- no secrets in prompt;
- confirmation cho write;
- output leakage scan;
- red-team and monitoring.

Các pattern như “ignore previous instructions”, fake system tags, encoded instruction, instruction trong retrieved PDF/table, data exfiltration request, tool argument smuggling và indirect URLs phải có tests. Khi detector flag:

- factual benign content MAY tiếp tục nhưng tool privilege không tăng;
- requested policy override MUST bị bỏ;
- high-confidence exfiltration/tool manipulation MUST block tool call và log security event;
- không tiết lộ hidden prompt hoặc internal policy text.

OWASP nhận diện direct/indirect prompt injection và nhấn mạnh impact có thể gồm rò rỉ dữ liệu hoặc function access trái phép: [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) (`SRC-OWASP-001`).

## 5. Input controls

- UTF-8 only; normalize NFC; reject control characters ngoài allowlist.
- Text length cap theo route; file/image upload ngoài phạm vi V1 nếu chưa có approved pipeline.
- Rate limit actor/session/IP risk signal ở application layer.
- PII detector tags types; chỉ redact phần không cần cho nhiệm vụ.
- Không echo secret/credential; hướng dẫn revoke/reset qua official flow.
- Không gọi arbitrary URL từ user/retrieved content.
- Encoded/binary payload không được decode rồi execute; MAY decode bounded text cho classifier sandboxed nếu task approved.

## 6. Output guard

Output MUST fail nếu:

- có unsupported policy claim hoặc citation ID ngoài bundle;
- chứa contact chưa được approved/configured;
- hứa human response time chưa approved;
- tuyên bố đã gọi/cứu hộ/chuyển thành công khi tool result không xác nhận;
- có credential, secret, hidden prompt, chain-of-thought hoặc dữ liệu user khác;
- có chẩn đoán/y lệnh/phán quyết pháp lý/kỷ luật;
- mô tả bản demo như dịch vụ chính thức;
- có executable instruction nguy hiểm không cần thiết;
- vượt reading/length policy.

Failure trả approved safe template; không đưa raw rejected output cho user.

## 7. Sensitive response policy

Response MUST:

- ngắn, bình tĩnh, không phán xét;
- xác nhận giới hạn của hệ thống;
- ưu tiên hành động an toàn đã được institution approve;
- chỉ hiển thị contact từ configuration có `approved=true`, `valid_from/to` và owner;
- nói rõ handover status dựa trên tool result;
- thu thập tối thiểu dữ liệu cần thiết;
- cho phép user yêu cầu người thật.

Response MUST NOT:

- chẩn đoán, điều tra hoặc đánh giá độ đáng tin của người báo cáo;
- hứa bí mật tuyệt đối hoặc kết quả xử lý;
- đưa số điện thoại/email tưởng tượng;
- ép user kể chi tiết nhạy cảm không cần thiết;
- coi classifier score là kết luận;
- tự liên hệ police/ambulance/family trong V1.

`OQ-003` chưa được giải quyết; vì vậy môi trường mô phỏng MUST hiển thị placeholder rõ ràng và MUST NOT hiển thị placeholder như contact thật.

## 8. Human handover payload minimization

Payload gồm: actor reference, category/severity, safe summary, current request excerpt cần thiết, previous relevant case ref nếu authorized, citation/tool outcome refs, locale, timestamp, consent/exception reason. Không mặc định gửi toàn transcript. Staff UI có thể request thêm theo quyền và audit.

## 9. Metrics và gates

| Metric | Gate |
|---|---:|
| Critical sensitive recall | ≥0.98 và không missed case severity-1 trong must-pass set |
| High+critical recall | ≥0.95 |
| Ordinary-service false-positive handover | ≤0.08 trên validation distribution |
| Unauthorized tool execution | 0 |
| Secret/cross-user leakage | 0 |
| Unapproved contact emission | 0 |
| Prompt-injection policy bypass | 0 must-pass critical cases |
| Handover payload minimum-field compliance | 100% |

Threshold classifier phải calibrate trên validation set tách biệt. Release MUST report confusion matrix theo label/language style (có dấu, không dấu, slang, typo), không chỉ aggregate accuracy.

## 10. Failure behavior

- Classifier unavailable: deterministic rules; ambiguous risky input default high and handover.
- Handover unavailable: safe response + approved channel; record pending/retry only if idempotent queue supports it.
- Official contact config missing/expired: không hiển thị contact; raise operational alert/block production readiness.
- Output guard unavailable: không trả model draft; dùng deterministic safe template/search-only.
- Excessive false positives: không tự hạ threshold production; create reviewed change with eval.

## 11. Acceptance evidence

- safety gold-set per taxonomy/subgroup;
- deterministic rules unit tests;
- classifier schema/calibration report;
- unapproved-contact canary tests;
- handover payload minimization tests;
- prompt-injection catalog pass/fail report;
- cross-user leakage tests;
- outage tests cho classifier/output guard/handover.

