"""Unit tests for eval case and result schema validation (TASK-EVAL-SCHEMA-001)."""

import pytest
from packages.evals.src.validate import validate_case, validate_result, SchemaValidationError


def test_valid_eval_case():
    case = {
        "schema_version": "1.0",
        "case_id": "EVAL-RAG-001",
        "version": "1.0.0",
        "suite": "grounded_qa",
        "severity": "S2",
        "locale": "vi-VN",
        "tags": ["hoc-vu"],
        "split": "dev",
        "input": {
            "turns": [{"role": "user", "content": "Điều kiện tốt nghiệp HUCE là gì?"}],
            "trusted_context_fixture_ref": "fixture://trusted-context/student-std",
        },
        "fixtures": {
            "knowledge_refs": ["fixture://knowledge/huce-handbook-2024"],
            "tool_refs": [],
            "provider_fixture_ref": "fixture://provider/fake-llm",
        },
        "expected": {
            "route": "grounded_faq",
            "terminal": "answered",
            "allowed_outcomes": ["valid_faq_answer"],
            "forbidden_outcomes": ["hallucinated_policy"],
            "tool": None,
            "citations": {
                "required": True,
                "allowed_source_refs": ["fixture://knowledge/huce-handbook-2024"],
                "minimum_valid_citations": 1,
            },
        },
        "assertions": [
            {
                "assertion_id": "A-01",
                "kind": "route_is",
                "target": "route",
                "expected": "grounded_faq",
            }
        ],
        "semantic_rubric_ref": None,
        "privacy_class": "PUBLIC",
        "provenance": {
            "synthetic": True,
            "generator": "campus247-eval-fixture-generator",
            "generator_version": "1.0.0",
            "seed": 42,
            "license_marker": "PROJECT-INTERNAL-SYNTHETIC-NO-REAL-DATA",
            "source_refs": ["DOC-EVAL-001"],
        },
        "review": {
            "status": "reviewed",
            "reviewers": ["ROLE-AI-QUALITY-LEAD"],
        },
    }
    assert validate_case(case) is True


def test_invalid_eval_case_missing_field():
    invalid_case = {
        "schema_version": "1.0",
        "case_id": "INVALID-ID",
    }
    with pytest.raises(SchemaValidationError):
        validate_case(invalid_case)


def test_valid_eval_result():
    result = {
        "schema_version": "1.0",
        "run_id": "018f6e4a-5b12-7000-8000-000000000001",
        "case_id": "EVAL-RAG-001",
        "case_version": "1.0.0",
        "attempt": 1,
        "started_at": "2026-09-22T20:00:00Z",
        "completed_at": "2026-09-22T20:00:01Z",
        "environment": "local_fake",
        "versions": {
            "git_ref": "main@a1b2c3d",
            "dataset_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "provider_id": "fake_provider",
            "model_id": "fake-v1",
            "prompt_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "retrieval_profile": "hybrid_rrf",
            "index_version": "v1.0.0",
            "tool_registry_version": "1.0.0",
            "policy_version": "v1.0.0",
            "temperature": 0.0,
            "seed": 42,
        },
        "status": "passed",
        "actual": {
            "route": "grounded_faq",
            "terminal": "answered",
            "tool_id": None,
            "tool_status": None,
            "citation_ids": ["fixture://knowledge/huce-handbook-2024"],
            "output_disposition": "released",
        },
        "assertion_results": [
            {
                "assertion_id": "A-01",
                "passed": True,
                "evidence_ref": "route_match",
            }
        ],
        "rubric_result": None,
        "sanitized_input_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "actual_output_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "side_effect_diff": {
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "external_calls": 0,
        },
        "audit_event_refs": [],
        "failure_codes": [],
    }
    assert validate_result(result) is True


def test_invalid_eval_result_invalid_hash():
    invalid_result = {
        "schema_version": "1.0",
        "run_id": "018f6e4a-5b12-7000-8000-000000000001",
        "sanitized_input_hash": "invalid_hash",
    }
    with pytest.raises(SchemaValidationError):
        validate_result(invalid_result)
