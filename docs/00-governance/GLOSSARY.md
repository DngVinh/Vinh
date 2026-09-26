---
document_id: "DOC-GOV-GLOSSARY-001"
version: "1.0.0"
status: "approved"
owner: "Documentation Chief Editor"
approvers: ["Product Owner", "Architecture Owner", "AI Quality Owner"]
last_updated: "2026-09-21"
---

# Glossary

| Term | Normative meaning in Campus 24/7 |
|---|---|
| Answer coverage | Percentage of eligible user questions for which the system returns a substantive answer instead of abstaining or handing over. It is not an accuracy metric. |
| Citation | A machine-resolvable reference to a specific approved source version, section/page and effective period that supports a claim. |
| Commercial product | Software intended to become a sellable and supportable product. It does not mean the HUCE Demo is an authorized university service. |
| Confirmation | Explicit user approval of an immutable action preview. General conversational agreement is not confirmation. |
| Controlled agent | A state-machine workflow with typed state, allowlisted transitions, bounded tools and deterministic policy gates. |
| Critical case | A configured situation with potential immediate risk to life, safety or severe harm. Official classification and contacts remain a launch dependency. |
| Evidence gate | Deterministic validation that retrieved evidence is sufficient, current, authorized and citation-ready before an answer is emitted. |
| Gold dataset | Human-reviewed evaluation cases containing input, expected behavior, authoritative evidence and scoring criteria. |
| Grounded correctness | Degree to which the answer is both factually correct and supported by the retrieved approved evidence. |
| Handover | Transfer of a conversation or case to an accountable human queue with bounded context, reason, priority and audit event. |
| HITL | Human-in-the-loop pause, approval, review or intervention within an otherwise automated workflow. |
| HUCE Demo | Unofficial simulated configuration referencing Hanoi University of Civil Engineering for realistic design and testing. |
| Idempotency key | Stable key that ensures retrying the same logical write action does not create duplicate side effects. |
| Knowledge source | Approved, versioned material used by retrieval. Conversation memory and model pretraining are not knowledge sources. |
| Memory | Stored conversation state or explicitly approved user preference. Memory MUST NOT override official knowledge or authorization. |
| Personal data | Information relating to an identified or identifiable person, including identifiers, schedules, tickets and behavioral records. |
| PII minimization | Removing, tokenizing or generalizing identity data before external model processing while preserving only necessary task context. |
| Public-source reference | Publicly accessible material used to understand taxonomy or provenance. Public availability does not automatically grant redistribution rights or production approval. |
| RAG | Retrieval-augmented generation using approved external evidence supplied to a model at inference time. |
| Reranker | A model or deterministic method that reorders retrieved candidates for relevance after initial lexical/vector retrieval. |
| Sensitive case | A configured case involving mental health, harassment, discipline, legal/financial rights, protected data or other high-impact context requiring constrained behavior or handover. |
| Synthetic data | Artificial records that do not correspond to real persons and are generated with documented distributions, seeds and validation rules. |
| Tool | Typed, allowlisted application capability exposed to the controlled agent. A tool never grants arbitrary code, SQL or network execution. |
| Unofficial simulation | A demonstration that must visibly disclaim institutional operation, authorization or endorsement. |
| Write action | Any operation that creates, updates, submits, cancels or otherwise changes persistent state or triggers an external effect. |

