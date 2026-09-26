---
document_id: "DOC-PRIV-005"
version: "0.1.0"
status: "draft"
owner: "Vendor and Privacy Owner"
approvers: ["Privacy/Legal Owner", "Security Architect", "Data Owner", "University Sponsor"]
last_updated: "2026-09-22"
---

# Vendor and cross-border governance

## 1. Quyết định hiện tại và giới hạn tuyên bố

Tài liệu này là contract quản trị và checklist evidence cho DeepSeek, Amazon Web Services (AWS) và Microsoft Entra ID. Nó **không phải ý kiến pháp lý**, không xác nhận vendor nào tuân thủ pháp luật Việt Nam, không xác nhận data residency và không cho phép xử lý dữ liệu cá nhân thật.

Quyết định mặc định:

- V1 development, test và demo chỉ dùng dữ liệu tổng hợp theo `DEC-004` và `PRIV-DATA-001`.
- Không gửi C2/C3, secret, credential, raw ticket, raw transcript hoặc identity thật tới DeepSeek.
- Không đưa dữ liệu thật lên AWS `ap-southeast-1`, Entra tenant hoặc bất kỳ hệ thống ngoài Việt Nam trước khi `OQ-002`, `OQ-004`, `OQ-005`, `OQ-006` được đóng và các approval trong tài liệu này có evidence.
- Automated test dùng fake provider. Demo gọi DeepSeek thật chỉ được phép khi có phê duyệt paid-service riêng theo `DEC-020`, outbound payload là C0 hoặc C1 tổng hợp đã duyệt, và egress gate fail closed.
- Tên vùng cloud, endpoint, hợp đồng mẫu hoặc tài liệu marketing không được dùng như bằng chứng độc lập cho vị trí của mọi bản sao dữ liệu, support access, telemetry, backup hoặc subprocessor.
- Legal Owner phải đối chiếu văn bản, hợp đồng và luồng thực tế tại thời điểm phê duyệt. Không implementation agent nào được tự kết luận lawful basis, transfer legality hoặc controller/processor role.

Status chung hiện tại:

```yaml
vendor_governance_status:
  deepseek: "not_approved_for_real_data"
  aws: "not_approved_for_real_data"
  microsoft_entra_id: "not_configured_not_approved_for_real_data"
  cross_border_transfer: "prohibited_pending_approval"
  synthetic_demo: "conditional"
```

## 2. Vai trò và phạm vi vendor dự kiến

| Vendor/service | Mục đích dự kiến | Dữ liệu V1 được phép | Dữ liệu bị cấm hiện tại | Vị trí/transfer phải xác minh | Trạng thái |
|---|---|---|---|---|---|
| DeepSeek API | Sinh câu trả lời grounded qua provider-neutral gateway | C0 đã duyệt; C1 tổng hợp tối thiểu nếu egress policy cho phép | Mọi C2/C3, secret, raw identity/session/ticket/transcript | Endpoint xử lý, log, abuse monitoring, support, backup, subprocessor và remote access | Chưa duyệt dữ liệu thật |
| AWS | Hosting container, database, cache, queue, object, observability, key/secret và backup theo ADR | Synthetic dataset, artifact và telemetry đã redaction | Dữ liệu thật cho tới privacy/legal/vendor gate; secret ngoài Secrets Manager/KMS contract | Region từng service, global control plane, support path, replicated backup/log, subprocessor | Reference architecture only |
| Microsoft Entra ID | Future OIDC authentication và workforce/student identity federation | Test tenant và synthetic users | Production student/staff identity trước `OQ-004` và approval | Tenant location, sign-in/audit log, support/diagnostic flow, directory replication và subprocessor | Future, chưa cấu hình |

Nhà trường có thể là Controller và vendor có thể là Processor/subprocessor, nhưng vai trò pháp lý phụ thuộc hợp đồng và quyền quyết định mục đích/phương tiện. Mọi bảng trong tài liệu này chỉ là giả định thiết kế cho tới khi `PRIV-VEND-003` có approval.

## 3. Vendor due-diligence controls

| ID | Requirement bắt buộc | Minimum evidence | Owner | Failure behavior |
|---|---|---|---|---|
| `PRIV-VEND-001` | Mỗi vendor/service MUST có business owner, technical owner, privacy owner, purpose, data class, environment và criticality. | Signed vendor inventory record. | Vendor Owner | Không tạo credential hoặc route production traffic. |
| `PRIV-VEND-002` | Data Owner MUST phê duyệt field-level data inventory, purpose, necessity và recipient trước khi vendor nhận dữ liệu thật. | Processing inventory gắn `PRIV-FLOW-*`, schema và classification. | Data Owner | Egress và ingestion bị deny. |
| `PRIV-VEND-003` | Legal Owner MUST xác định bằng văn bản controller/processor/subprocessor roles cho từng service và purpose. | Legal memorandum hoặc contract schedule đã duyệt. | Privacy/Legal Owner | Real-data use bị block. |
| `PRIV-VEND-004` | DPA/processing terms MUST bao phủ instruction scope, confidentiality, security, incident notice, rights support, deletion/return, audit/assurance và termination. | Executed DPA + obligation matrix + contract owner. | Legal/Vendor Owner | Không ký production enablement. |
| `PRIV-VEND-005` | Subprocessor register MUST liệt kê legal entity, service, purpose, country/location, data class và notification/change right. | Dated register, source copies và review record. | Vendor Owner | New/unknown subprocessor làm egress gate fail. |
| `PRIV-VEND-006` | Vendor MUST cung cấp đủ evidence về security program, access control, encryption, vulnerability/incident management, resilience và independent assurance phù hợp risk. | Due-diligence questionnaire, assurance reports/extracts, exception register. | Security Architect | Risk remains open; no real data. |
| `PRIV-VEND-007` | Data-use terms MUST xác nhận retention, logging, human review, abuse monitoring, model training/fine-tuning, derived data và deletion behavior. | Contract/term extracts with version/date and negotiated restrictions. | Privacy Owner | Field stays prohibited if behavior is unknown. |
| `PRIV-VEND-008` | Vendor MUST support incident escalation and evidence preservation with named channels, notification obligations and testable contacts. | Contract terms, contact matrix, tabletop evidence. | Incident Commander | Production gate blocked. |
| `PRIV-VEND-009` | Vendor access MUST use least privilege, named service identity, MFA/step-up where applicable, short-lived credentials and auditable actions. | IAM design, access review and negative tests. | Security/Platform Owner | Integration disabled. |
| `PRIV-VEND-010` | Availability, quota, rate, cost, suspension and dependency-failure behavior MUST have degraded mode and exit strategy. | SLA/limit inventory, circuit-breaker test, export/restore/exit drill. | Product/Operations Owner | Capability disabled or safe mode. |
| `PRIV-VEND-011` | Terms, privacy notice, DPA, subprocessor and location evidence MUST be versioned and reassessed after material change and at least annually. | Immutable snapshot/hash, review date, next review date. | Vendor Owner | Approval expires; real-data gate closes. |
| `PRIV-VEND-012` | Marketing claims, self-attestation or console region selector MUST NOT alone close a due-diligence item. | Independent reviewer sign-off against primary contractual/technical evidence. | Security/Privacy Owner | Status remains `evidence_pending`. |

## 4. DPA and contract minimum schedule

Mỗi production vendor record MUST có một obligation matrix với ít nhất:

```yaml
vendor_contract_record:
  vendor_id: "VEND-..."
  legal_entity: "unresolved"
  service_names: []
  agreement_versions: []
  effective_at: null
  expires_at: null
  controller: "unresolved"
  processors: []
  subprocessors: []
  approved_purposes: []
  prohibited_purposes: []
  data_subjects: []
  data_categories: []
  highest_classification: "C0|C1|C2|C3"
  processing_locations: []
  storage_locations: []
  support_access_locations: []
  retention_and_deletion_terms: "unresolved"
  training_and_derived_data_terms: "unresolved"
  incident_notification_terms: "unresolved"
  rights_assistance_terms: "unresolved"
  audit_and_assurance_terms: "unresolved"
  termination_return_deletion_terms: "unresolved"
  subprocessor_change_terms: "unresolved"
  transfer_record_ids: []
  security_control_ids: []
  residual_risks: []
  approved_by: []
  evidence_refs: []
  status: "draft|evidence_pending|approved|suspended|expired"
```

Missing legal entity, approved purpose, data category, location, retention/deletion, subprocessor terms, transfer record hoặc approver MUST keep status outside `approved`.

## 5. Provider-specific due diligence

### 5.1 DeepSeek

Trước mọi use case có dữ liệu thật, evidence MUST trả lời rõ:

1. Contracting legal entity và endpoint/service version nào thực sự nhận request.
2. Quốc gia/vùng của processing, transient queue, request/response log, abuse monitoring, support access, backup và disaster recovery.
3. Prompt, response, tool schema, metadata, request ID và derived telemetry được giữ trong bao lâu; deletion có áp dụng cho backup/log hay không.
4. Dữ liệu có được dùng để train, fine-tune, evaluate hoặc cải thiện model/service không; opt-out có tính contract hay chỉ configuration.
5. Human access, privileged support access, government/law-enforcement request process và notification terms.
6. Danh sách subprocessor, purpose/location và cơ chế thông báo thay đổi.
7. Incident notification, security assurance, vulnerability handling, tenant isolation và API-key protection.
8. Cơ chế export/termination/deletion và bằng chứng hoàn tất.
9. Model/version lifecycle, deprecation notice, quota/rate/cost limits và kill switch.
10. DPA và transfer mechanism được Legal Owner chấp thuận cho đúng luồng dữ liệu.

Runtime requirements:

- Chỉ provider gateway được gọi endpoint allowlisted; domain và model không được tạo outbound URL.
- Pre-egress deterministic DLP/minimizer MUST chặn C2/C3, secret và field ngoài allowlist theo `SEC-CTRL-016`/`PRIV-FLOW-016`.
- Payload không có identity, session, IP, email, student number, ticket ID, raw schedule hoặc internal authorization metadata.
- Prompt/response raw không vào general logs; provider request ID chỉ được giữ khi purpose/retention đã duyệt.
- Response phải qua schema, citation/evidence, output DLP và untrusted-content handling trước khi render hoặc gọi tool.
- Unknown term/location/subprocessor hoặc DLP uncertainty -> call bị deny; deterministic search, abstention hoặc HITL được dùng làm fallback.

Official API behavior sources hiện được đăng ký tại `SRC-DEEPSEEK-001` và `SRC-DEEPSEEK-002`; chúng không thay DPA, privacy terms hoặc transfer assessment.

### 5.2 AWS

AWS due diligence MUST đánh giá theo từng service và luồng, không gán một kết luận chung cho cả cloud:

- Region/resource inventory cho ECS/Fargate, RDS PostgreSQL/pgvector, ElastiCache, SQS/DLQ, S3, CloudFront/WAF/ALB, KMS, Secrets Manager, observability và backup.
- Data-plane, control-plane, support, billing, threat detection, log aggregation, backup/copy, artifact registry và DNS/certificate flow.
- Shared-responsibility matrix: AWS responsibility, project responsibility, university responsibility và verification owner.
- DPA/service terms, subprocessor list, incident terms, deletion/return, assurance artifacts và customer audit/assessment rights.
- Cross-region replication bị tắt mặc định; mọi replica, backup copy, log destination hoặc support export cần record riêng.
- Public access blocks, private networking, egress allowlist, customer-managed key policy khi classification yêu cầu, least-privilege IAM và immutable audit evidence.
- Exit plan phải chứng minh export, restore sang target thay thế, credential/key revoke, object/version/backup deletion reconciliation và DNS/certificate handover.

`ap-southeast-1` trong `DEC-010` chỉ là reference region cho mô phỏng. Nó không tự đóng residency/transfer gate. `SRC-AWS-001` đến `SRC-AWS-003` là technical design sources, không phải legal approval.

### 5.3 Microsoft Entra ID

Entra chỉ được kích hoạt production sau `OQ-004` và các evidence sau:

- Named university tenant, approved issuer/audience, app registrations, redirect URI, claim/app-role mapping và accountable Identity Administrator.
- DPA/licensing/service terms, legal entity, processing/support locations, subprocessor và transfer assessment.
- Inventory cho directory attributes, group/app roles, ID/access token, sign-in/audit logs, Conditional Access signals, support diagnostic và retention.
- Data minimization: application chỉ nhận stable subject, issuer, account state và approved roles/attributes; không yêu cầu directory profile ngoài purpose.
- MFA/Conditional Access cho staff/admin, revocation target, disabled-account test, break-glass control và quarterly access review.
- Staging dùng test tenant/synthetic identities; không copy production directory hoặc student roster.
- Logout/revocation, incident, rights/deletion and offboarding responsibilities được phân chia rõ giữa university, application operator và Microsoft.

Entra chứng minh authentication; authorization vẫn do application áp dụng theo `SEC-AUTHN-*` và `SEC-AUTHZ-*`.

## 6. Cross-border transfer controls

| ID | Requirement bắt buộc | Minimum evidence | Owner | Failure behavior |
|---|---|---|---|---|
| `PRIV-XFER-001` | Mọi transfer MUST có source, destination legal entity/service, country/region, purpose, data subjects/categories, volume/frequency và onward-transfer inventory. | Signed transfer map linked to `PRIV-FLOW-*`. | Privacy Owner | Route absent from allowlist; deny egress. |
| `PRIV-XFER-002` | Transfer MUST có necessity/proportionality analysis và chứng minh không có phương án ít xâm phạm hơn đáp ứng purpose. | Approved assessment and architecture alternatives. | Data Owner/Privacy Owner | Use deterministic/local path or disable feature. |
| `PRIV-XFER-003` | Legal Owner MUST xác định legal condition, required assessment/filing/contract và timing cho đúng transfer. | Dated legal memorandum and filing/record evidence where applicable. | Legal Owner | No real-data transfer. |
| `PRIV-XFER-004` | DPA, transfer terms và subprocessor/onward-transfer controls MUST được ký và gắn đúng vendor/service/version. | Executed documents and obligation matrix. | Legal/Vendor Owner | Egress gate remains closed. |
| `PRIV-XFER-005` | Technical controls MUST minimize/pseudonymize, encrypt, allowlist destination, prevent C2/C3/secret egress and log only safe metadata. | DLP tests, network-policy test, schema diff and sample telemetry. | Security/Platform Owner | Deny request and alert without echoing data. |
| `PRIV-XFER-006` | Runtime policy MUST bind approved transfer record, vendor version, data class, purpose, environment and expiry. | Policy-as-code test and immutable approval reference. | Security Architect | Unknown/mismatch/expired = deny. |
| `PRIV-XFER-007` | Onward transfer, remote support and new location/subprocessor MUST trigger reassessment before activation. | Change notification, impact assessment and approval. | Vendor/Privacy Owner | Suspend affected route. |
| `PRIV-XFER-008` | Transfer inventory MUST reconcile with logs, billing, DNS/network egress and vendor records without storing payload. | Periodic reconciliation report and anomaly test. | SecOps/Privacy Owner | Alert; disable unexplained destination. |
| `PRIV-XFER-009` | Incident, rights request, deletion, legal hold and termination MUST coordinate across every recipient/subprocessor. | End-to-end exercise and signed completion evidence. | Privacy/Incident Owner | Do not claim completion; production gate fails. |
| `PRIV-XFER-010` | Approval MUST expire on material change and have an explicit next-review date no later than the vendor risk cycle. | Approval record, trigger list and review date. | Privacy Owner | Expired record closes egress gate. |

## 7. Egress minimization and enforcement

```text
request intent
  -> classify fields
  -> select approved purpose/schema
  -> remove direct/quasi identifiers and internal metadata
  -> deterministic C2/C3/secret DLP
  -> bind PRIV-XFER record + vendor/model version + environment
  -> destination allowlist and TLS
  -> provider call
  -> validate response schema/citation/link
  -> output DLP
  -> store only safe telemetry
```

Mandatory controls:

1. Outbound schema uses allowlist and rejects additional fields.
2. Identity-derived attributes are not forwarded merely because they exist in `IdentityContext`.
3. Tokenization/pseudonymization is not sufficient when vendor can readily relink the value; Data Owner must document residual linkage risk.
4. Free text that cannot be deterministically classified within policy is not sent externally.
5. URL, header, query string, trace baggage và analytics MUST not carry C2/C3 or secret.
6. Destination is an exact configured endpoint; redirects, user-supplied URL and arbitrary tool network access are denied.
7. Provider timeout/rate/error body is normalized; raw provider response is not surfaced to user or broad logs.
8. A kill switch can stop one provider/transfer without disabling deterministic service paths.
9. Egress test fixtures include direct identifier, quasi-identifier, Vietnamese sensitive text, encoded secret, prompt-injection and unexpected JSON property.
10. Metrics record decision/reason code and payload-size bucket only; no content hash that enables dictionary recovery for low-entropy identifiers.

## 8. Approval workflow and status model

```text
proposed
  -> inventory_complete
  -> security_reviewed
  -> privacy_legal_reviewed
  -> contract_executed
  -> technical_controls_verified
  -> approved_for_named_scope
  -> monitored

Any material change or expired evidence -> suspended_pending_reassessment
```

Approvals are scope-bound. Approval for AWS synthetic demo does not approve AWS real student data; approval for Entra authentication does not approve DeepSeek transfer; approval for one model/region/subprocessor does not approve another.

Material changes include vendor legal entity, purpose, data field/class, model/service, endpoint, region/location, subprocessor, retention, training use, security term, incident term, auth method, encryption, onward transfer or exit capability.

## 9. Evidence pack and review cadence

Required evidence bundle:

```yaml
vendor_approval_evidence:
  vendor_id: "VEND-..."
  scope_id: "immutable-scope-id"
  environments: []
  purposes: []
  data_classes: []
  flow_ids: []
  vendor_contract_record_ref: "artifact-ref"
  dpa_ref: "artifact-ref"
  subprocessor_register_ref: "artifact-ref"
  transfer_record_ids: []
  security_assessment_ref: "artifact-ref"
  dpi_a_ref: "artifact-ref"
  technical_test_refs: []
  incident_contact_test_ref: "artifact-ref"
  exit_plan_test_ref: "artifact-ref"
  approved_by: []
  approved_at: null
  expires_at: null
  residual_risks: []
  status: "evidence_pending"
```

- High-risk vendor owner MUST not be sole verifier (`SEC-CTRL-029`).
- Evidence is immutable/versioned and contains no secret or personal payload (`SEC-CTRL-030`).
- Review occurs after material change/incident and at least annually; a shorter contract/regulatory cycle wins.
- Automated monitoring MAY detect term/subprocessor/location drift, but a human Privacy/Vendor Owner closes the reassessment.

## 10. Exit, suspension and failure behavior

Trigger suspension when: unknown destination/subprocessor, material term drift, expired approval, DLP bypass, data incident, unapproved training use, inability to honor deletion/rights, assurance withdrawal, critical vulnerability without treatment, or contract termination.

Suspension sequence:

1. deny new egress or identity enablement;
2. preserve minimal audit/security evidence;
3. switch to deterministic search/form/safe mode or abstain;
4. revoke/rotate credentials and stop scheduled transfers;
5. inventory affected data and recipients;
6. execute incident/privacy/legal assessment;
7. export required business data in approved format;
8. request and reconcile deletion/return across active, log, backup and subprocessors;
9. re-enable only with new scope-bound approval and test evidence.

No UI or operator may claim data was deleted everywhere until evidence for vendor, backup and subprocessor copies satisfies approved policy.

## 11. Traceability

- Decisions: `DEC-004`, `DEC-007`, `DEC-008`, `DEC-009`, `DEC-010`, `DEC-014`, `DEC-020`.
- Open questions: `OQ-002`, `OQ-004`, `OQ-005`, `OQ-006`, `OQ-008`.
- Data/privacy: `SEC-DATA-001` đến `SEC-DATA-006`, `PRIV-DATA-001` đến `PRIV-DATA-004`, `PRIV-FLOW-002`, `PRIV-FLOW-006`, `PRIV-FLOW-008`, `PRIV-FLOW-009`, `PRIV-FLOW-016` đến `PRIV-FLOW-018`.
- DPIA: `PRIV-DPIA-001`, `PRIV-DPIA-003`, `PRIV-DPIA-005`, `PRIV-DPIA-009`, `PRIV-DPIA-013` đến `PRIV-DPIA-020`.
- Controls: `SEC-CTRL-001`, `SEC-CTRL-005`, `SEC-CTRL-009`, `SEC-CTRL-010`, `SEC-CTRL-015`, `SEC-CTRL-016`, `SEC-CTRL-018`, `SEC-CTRL-021`, `SEC-CTRL-022`, `SEC-CTRL-024`, `SEC-CTRL-026` đến `SEC-CTRL-030`.
- Launch gates: `PRIV-LAUNCH-001` đến `PRIV-LAUNCH-010`, `SEC-LAUNCH-002`, `SEC-LAUNCH-005`, `SEC-LAUNCH-009`, `SEC-LAUNCH-014`.

## 12. Nguồn và giới hạn cập nhật

- Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP được liệt kê trong `docs/06-security/README.md` và `docs/06-security/04_PRELIMINARY_DPIA.md`; Legal Owner phải kiểm tra bản có hiệu lực và cách áp dụng tại thời điểm review.
- DeepSeek API sources: `SRC-DEEPSEEK-001`, `SRC-DEEPSEEK-002`.
- AWS technical design sources: `SRC-AWS-001`, `SRC-AWS-002`, `SRC-AWS-003`.
- Entra protocol/configuration source phải được bổ sung vào source register trong một governance change riêng trước khi phê duyệt production.

Không nguồn kỹ thuật nào ở trên tự chứng minh DPA, subprocessor, residency, transfer legality hoặc compliance. Những kết luận đó phải dựa trên evidence hiện hành, đúng contracting entity và được owner có thẩm quyền phê duyệt.
