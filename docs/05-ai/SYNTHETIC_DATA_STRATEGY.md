---
document_id: "DOC-RAG-002"
version: "1.0.0"
status: "reviewed"
owner: "Data Engineering Lead"
approvers: ["Knowledge Governance Lead", "Privacy Officer", "AI Quality Lead", "Product Owner"]
last_updated: "2026-09-21"
---

# Chiến lược corpus và dữ liệu tổng hợp

## 1. Quyết định

V1 dùng phương pháp hybrid an toàn:

1. dùng website/tài liệu công khai chính thức chỉ để nghiên cứu taxonomy, vocabulary và provenance;
2. không tuyên bố nội dung công khai là corpus production nếu chưa có quyền sử dụng/phê duyệt;
3. tạo corpus nghiệp vụ tổng hợp lớn bằng generator deterministic;
4. tách gold eval do người review khỏi corpus generation/training;
5. gắn nhãn rõ `HUCE Demo`, `synthetic=true`, không đại diện quy định chính thức.

Phương pháp này dễ tái tạo, không dùng hồ sơ thật, kiểm soát conflict/edge case và tránh phụ thuộc scraping. Nó thực thi `DEC-002`, `DEC-004` và `DEC-012`.

## 2. Data products

| Product | Quy mô baseline | Mục đích | Commit policy |
|---|---:|---|---|
| `synthetic_knowledge_corpus` | 150–300 documents | RAG demo/functional eval | Commit generator spec, manifest, small sample; large output artifact storage |
| `synthetic_students` | 5,000 | auth/schedule/ticket ownership tests | Generator + sample only |
| `synthetic_staff` | 100 | role/queue tests | Generator + sample only |
| `synthetic_schedules` | ≥50,000 class meetings/term | schedule tools | Generator + sample only |
| `synthetic_rooms` | ≥100 rooms | room availability/booking | Generator + sample only |
| `synthetic_tickets` | ≥20,000 lifecycle events | queue/metrics | Generator + sample only |
| `gold_eval` | quotas in `EVALUATION_PLAN.md` | release gates | Versioned reviewed cases; commit permitted |
| `stress_corpus` | up to 100,000 chunks/pages equivalent | performance | artifact storage, not Git |

## 3. Provenance and license rules

- Public HUCE pages MAY inform category names and organizational vocabulary; every research input MUST reference `SRC-HUCE-*` or a reviewed source record.
- Generator MUST NOT copy substantial protected text verbatim. Synthetic documents use original wording and fictitious numbers/dates/forms.
- Robots/terms/license MUST được review trước bất kỳ automated collection nào. Nếu không rõ, chỉ dùng manual taxonomy notes và synthetic text.
- Public source inclusion vào demo corpus cần `usage_basis`, `source_owner`, checksum, review và takedown mechanism.
- Không dùng social media, forum, leaked file hoặc search-result snippet làm authoritative source.
- Không dùng real names/student IDs/emails/phone numbers. Synthetic identifiers MUST không match known institutional formats nếu có nguy cơ gửi nhầm; email dùng reserved domains như `example.edu`/`example.com`.

## 4. Deterministic generation

Mỗi dataset run MUST có manifest:

```yaml
dataset_id: "DATASET-SYNTH-..."
version: "semver"
generator_version: "git-or-artifact-ref"
seed: 2472026
locale: "vi-VN"
record_counts: {}
scenario_distribution: {}
source_taxonomy_refs: []
output_artifacts:
  - uri: "artifact://..."
    sha256: "sha256:..."
generated_at: "RFC3339"
simulation_label: true
```

Cùng generator version + seed + config MUST tạo cùng logical records và hashes, trừ fields timestamp được freeze bằng virtual clock. Faker/random library MUST nhận explicit seed; UUID/time MUST được inject, không gọi ambient randomness/clock trong deterministic mode.

## 5. Knowledge corpus taxonomy

Baseline distribution:

| Category | Tỷ lệ mục tiêu | Nội dung synthetic |
|---|---:|---|
| Academic regulations | 20% | đăng ký học, học lại, điều kiện, deadline |
| Administrative procedures | 20% | xác nhận, biểu mẫu, tiếp nhận, SLA giả lập |
| Schedule/exam guidance | 12% | đọc lịch, thay đổi, xung đột |
| Student services | 12% | thẻ, thư viện, hỗ trợ học tập |
| Facilities/room booking | 10% | điều kiện, capacity, thiết bị |
| IT/account/security | 10% | reset, MFA, phishing, acceptable use |
| Complaints/handover | 8% | route và escalation mô phỏng |
| Privacy/safety | 8% | quyền dữ liệu, kênh hỗ trợ mô phỏng |

Corpus MUST chứa edge cases có kiểm soát:

- phiên bản cũ/mới và ngày hiệu lực;
- document number/form code gần giống;
- exception theo cohort/faculty;
- table dài và heading lồng nhau;
- OCR noise variants;
- Vietnamese có dấu/không dấu/typo;
- conflict được đánh dấu để hệ thống abstain;
- malicious instructions trong document để test indirect prompt injection;
- missing metadata để test quarantine;
- withdrawn source.

Malicious content MUST ở test namespace, không publish vào normal demo index.

## 6. Referential integrity

Generators MUST đảm bảo:

- mọi schedule references tồn tại student/course/section/room;
- không booking confirmed trùng room/time trừ scenario conflict cố ý được label;
- ticket owner và queue hợp lệ;
- lifecycle transition hợp lệ;
- document request type nằm registry;
- source version chain không cycle;
- effective intervals hợp lệ;
- citation gold locator match exact text span/hash;
- synthetic PII không trùng canary/real fixtures.

Một validation report MUST liệt kê record count, duplicate, orphan, invalid transition, overlap ngoài scenario, distribution drift và checksum. Bất kỳ critical integrity error nào làm dataset run fail.

## 7. Gold eval separation

- Gold cases MUST không được dùng làm prompt examples hoặc generator template trực tiếp.
- Split theo scenario family/source version để tránh gần-duplicate leakage.
- Test set giữ sealed; coding agent chỉ thấy schema và sample/dev subset.
- Human reviewer xác nhận expected answer/evidence/tool/safety labels.
- Generated candidate case không trở thành gold trước independent review.
- Mỗi case ghi `provenance`, `review_status`, `reviewers`, `source_snapshot_hash`.

## 8. Large artifact handling

- Repository MUST không chứa hàng nghìn generated files hoặc binary lớn.
- Large corpus được đóng gói versioned artifact với manifest/checksum và retention policy.
- Sample nhỏ đủ chạy smoke tests được commit dưới `evals/datasets/samples/`.
- CI fast suite dùng sample; nightly/performance suite fetch artifact qua approved immutable URI và verify checksum.
- Artifact missing/checksum mismatch MUST fail, không tự regenerate bằng version khác.

## 9. Privacy and misuse controls

- Dữ liệu tổng hợp vẫn được classification `internal_test` vì có thể mô phỏng tình huống nhạy cảm.
- Không dùng real transcript để “làm giống thật”.
- Không publish scenario self-harm/harassment chi tiết ra public demo logs.
- Synthetic label phải xuất hiện trong UI/export và source metadata.
- Tạo canary records để detect cross-user leakage; canary values không được xuất hiện ngoài authorized test.

## 10. Acceptance evidence

- manifest schema pass và reproducibility hash pass trên hai clean runs;
- zero real-PII detector finding sau review false positives;
- referential-integrity report;
- distribution report so với target;
- duplicate/near-duplicate report giữa train/dev/test;
- license/provenance review log;
- sample RAG citations resolve exact source span;
- stress-corpus benchmark manifest;
- simulation disclaimer snapshot.

## 11. Blocking conditions

Không dùng dữ liệu thật hoặc publish corpus như tài liệu HUCE chính thức cho đến khi `OQ-001`, `OQ-002`, `OQ-005`, `OQ-006`, `OQ-007` được giải quyết và có approval tương ứng.

## 12. Nguồn taxonomy ban đầu

- [HUCE Phòng Quản lý đào tạo](https://huce.edu.vn/phong-quan-ly-dao-tao) (`SRC-HUCE-001`).
- [HUCE danh mục quy chế/quy định sinh viên](https://sinhvien.huce.edu.vn/sinh-vien/dm-tin-tuc/quy-che-quy-dinh.html) (`SRC-HUCE-002`).
- [Khoa Công nghệ Thông tin HUCE](https://fit.huce.edu.vn/) (`SRC-HUCE-003`).

Các nguồn trên chỉ là research input; không tạo endorsement hoặc quyền redistribution.

