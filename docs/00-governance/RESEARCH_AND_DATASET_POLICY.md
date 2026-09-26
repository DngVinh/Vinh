---
document_id: "DOC-GOV-DATASET-001"
version: "1.0.0"
status: "approved"
owner: "Knowledge Governance"
approvers: ["Product Owner", "Privacy Owner", "AI Quality Owner"]
last_updated: "2026-09-21"
---

# Research and dataset policy

## Goals

The project needs realistic scale and domain variation without collecting real student records, misrepresenting HUCE or redistributing content without a valid basis. The approved strategy combines public-source research with deterministic synthetic generation.

## Dataset tiers

### Tier 0 — Metadata-only research

Store URL, title, issuing organization, publication/effective date, document type, checksum and access date. Use this tier to design taxonomy and source manifests.

### Tier 1 — Licensed or explicitly reusable public content

Content may enter a local research corpus only after recording license/permission, provenance and integrity. Publication into a demo knowledge base requires knowledge-owner review.

### Tier 2 — Synthetic institutional knowledge

Generate original policies, procedures, forms, schedules, rooms and service catalogs inspired by common university operations but not copied from a specific protected source. Every document MUST carry:

- `synthetic: true`;
- deterministic generator version and seed;
- fictitious document number;
- explicit demo disclaimer;
- effective and expiry dates;
- owner department and audience;
- expected questions and gold citations.

### Tier 3 — Synthetic personal and operational records

Generate fictitious identities, schedules, tickets, bookings and conversations. Names, identifiers, emails and phones MUST be obviously synthetic and MUST NOT be derived from scraped people lists.

## Prohibited inputs

- leaked, private or paywalled datasets;
- real student profiles, transcripts, schedules or support tickets;
- copied credentials, identifiers or contact lists;
- scraped content when robots/terms prohibit collection;
- documents whose redistribution rights are unknown when full content would be committed;
- public text containing hidden instructions that has not passed ingestion safety checks.

## Repository policy

The repository stores generators, schemas, manifests, small reviewed fixtures and checksums. Large generated corpora and downloaded binaries MUST stay outside Git and be reproducible from a documented command. Generated output directories MUST be ignored before generation begins.

## Reproducibility

Each generator run MUST record:

```yaml
generator_version: "semver"
seed: 0
schema_version: "semver"
locale: "vi-VN"
record_counts: {}
source_manifest_hash: "sha256"
generated_at: "RFC3339 timestamp"
```

Re-running the same released generator version, schema and seed MUST produce semantically identical fixtures. Timestamps and random IDs use deterministic derivation when they participate in expected tests.

## Quality controls

- Referential integrity across users, schedules, rooms, tickets and departments.
- No collision with known real student identifiers in any optional comparison set.
- Distribution checks for intent, priority, status, language variation and edge cases.
- At least 20% of AI evaluation cases are adversarial or failure-path cases.
- Gold answers are produced or approved independently from the system being evaluated.
- Synthetic documents include superseded and conflicting versions to test effective-date filtering.
- Vietnamese inputs include diacritics, no-diacritic variants, abbreviations and common typing errors.

## Public-source ingestion gate

Before any source content is downloaded or embedded, the ingestion owner MUST record:

1. canonical URL and issuing authority;
2. access and reuse basis;
3. intended use and environment;
4. personal/sensitive data classification;
5. integrity checksum;
6. malware/content-safety result;
7. approval status and expiry/review date.

If the reuse basis is uncertain, keep metadata and generate an original synthetic analogue instead of copying the content.

