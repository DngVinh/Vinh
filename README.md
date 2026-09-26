# Campus 24/7

Campus 24/7 is a documentation-first commercial product for a single university. The initial reference deployment is an unofficial, simulated pilot for the Faculty of Information Technology at Hanoi University of Civil Engineering (HUCE).

This repository is a documentation package with machine-readable contracts, evaluation fixtures, infrastructure specifications and a draft delivery catalog. Its status is mixed: governance and selected product documents are approved, many design/contract/quality documents are reviewed, and service, UX, architecture, security and platform documents remain draft. It intentionally contains no production application code yet, and this package does not approve implementation, a real-data pilot, or production.

## Read first

1. `docs/00-governance/DOCUMENT_CONTROL.md`
2. `docs/00-governance/DECISION_REGISTER.md`
3. `docs/00-governance/DOCUMENT_MANIFEST.yaml`
4. `docs/00-governance/MASTER_TRACEABILITY_MATRIX.md`
5. `docs/00-governance/CONSISTENCY_REPORT.md`
6. `docs/README.md`
7. `tasks/README.md` before working on a task

## Important status

- Product intent: commercial, production-grade design.
- Initial institution: one university only; no SaaS or multi-tenant scope in V1.
- Data: public-source references plus deterministic synthetic data; no real student data.
- Coding executor: Gemini 3.8 Flash, operating only through reviewed atomic tasks.
- Production LLM provider: DeepSeek behind a provider-neutral gateway.
- Hosting preference: AWS.
- This is not an official HUCE service and must not be presented as one.
- The repository is synthetic-only. Do not use real student/staff data, university credentials, live institutional integrations, or paid provider calls without the separate approvals required by governance.

## Local validation

Run only offline, synthetic-safe checks from the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python tasks/tools/validate_catalog.py
python contracts/tools/validate_openapi.py
python evals/validate_contracts.py
```

Validation output is structural evidence only; it is not implementation, release, real-data, pilot, or production approval. Do not automatically commit, push, deploy, or change task/document approval states.
