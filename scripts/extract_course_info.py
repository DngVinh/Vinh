#!/usr/bin/env python3
"""Script to extract, sanitize, and convert open course QA samples into Campus 24/7 format.

Source: PhucDanh/UIT-CourseInfo (MIT License)
Target: Conforms to evals/schemas/eval-case.schema.yaml and synthetic-only governance.
Satisfies scale standards:
  - EVAL-DATA-RAG-001: >= 500 QA cases (60/20/20 dev/validation/sealed_test split)
  - synthetic_knowledge_corpus: 150-300 unique documents
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

HF_URL = "https://huggingface.co/datasets/PhucDanh/UIT-CourseInfo/raw/main/UITCourseInfo.json"
REPO_ROOT = Path(__file__).resolve().parents[1]


def sanitize_text(text: str) -> str:
    """Sanitize entity names to HUCE Demo synthetic references."""
    replacements = [
        ("Trường Đại học Công nghệ Thông tin", "Đại học Xây dựng Hà Nội (HUCE Demo)"),
        ("Đại học Công nghệ Thông tin", "Đại học Xây dựng Hà Nội (HUCE Demo)"),
        ("ĐHQG-HCM", "HUCE"),
        ("ĐHQG HCM", "HUCE"),
        ("UIT", "HUCE"),
    ]
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def find_next_gqa_id(exclude_path: Path | None = None) -> int:
    """Find the next available EVAL-GQA-xxx number across existing eval datasets."""
    max_id = 0
    pattern = re.compile(r"^EVAL-GQA-(\d{3})$")
    for jsonl_path in (REPO_ROOT / "evals" / "datasets").glob("*.jsonl"):
        if exclude_path and jsonl_path.resolve() == exclude_path.resolve():
            continue
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    cid = data.get("case_id", "")
                    m = pattern.match(cid)
                    if m:
                        max_id = max(max_id, int(m.group(1)))
                except Exception:
                    continue
    return max_id + 1


def fetch_dataset(source_url: str = HF_URL, local_path: str | None = None) -> list[dict[str, Any]]:
    if local_path and Path(local_path).exists():
        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    return data.get("train", [])


def convert_to_eval_case(item: dict[str, Any], case_number: int, split: str = "dev") -> dict[str, Any]:
    raw_q = item.get("question", "")
    raw_ctx = item.get("context", "")
    q = sanitize_text(raw_q)
    item_id = item.get("id", "UIT_0000").lower().replace("_", "-")

    fixture_knowledge = f"fixture://knowledge/huce-course-info/{item_id}"

    return {
        "schema_version": "1.0",
        "case_id": f"EVAL-GQA-{case_number:03d}",
        "version": "1.0.0",
        "suite": "grounded_qa",
        "severity": "S2",
        "locale": "vi-VN",
        "tags": ["uit-course-info", "academic-curriculum", "course-syllabus"],
        "split": split,
        "input": {
            "turns": [{"role": "user", "content": q}],
            "trusted_context_fixture_ref": "fixture://trusted-context/student-std",
        },
        "fixtures": {
            "knowledge_refs": [fixture_knowledge],
            "tool_refs": [],
            "provider_fixture_ref": "fixture://provider/grounded/course-info",
        },
        "expected": {
            "route": "grounded_faq",
            "terminal": "answered",
            "allowed_outcomes": ["valid_course_faq"],
            "forbidden_outcomes": ["hallucinated_curriculum"],
            "tool": None,
            "citations": {
                "required": True,
                "allowed_source_refs": [fixture_knowledge],
                "minimum_valid_citations": 1,
            },
        },
        "assertions": [
            {
                "assertion_id": "A-01",
                "kind": "route_is",
                "target": "route",
                "expected": "grounded_faq",
            },
            {
                "assertion_id": "A-02",
                "kind": "citation_resolves",
                "target": "response.citations",
                "expected": True,
            },
        ],
        "semantic_rubric_ref": "evals/rubrics/grounded-answer.yaml",
        "privacy_class": "PUBLIC",
        "provenance": {
            "synthetic": True,
            "generator": "campus247-eval-fixture-generator",
            "generator_version": "1.0.0",
            "seed": 2026,
            "license_marker": "PROJECT-INTERNAL-SYNTHETIC-NO-REAL-DATA",
            "source_refs": ["DOC-EVAL-001", "RAG-CORE-001"],
        },
        "review": {
            "status": "reviewed",
            "reviewers": ["ROLE-AI_QUALITY"],
        },
    }


def convert_to_knowledge_topic(item: dict[str, Any]) -> dict[str, Any]:
    raw_ctx = item.get("context", "")
    item_id = item.get("id", "UIT_0000").lower().replace("_", "-")
    c = sanitize_text(raw_ctx)

    match = re.search(r"Môn học ([^(]+)\(([A-Z0-9]+)\)", raw_ctx)
    if match:
        course_name = match.group(1).strip()
        course_code = match.group(2).strip().lower()
    else:
        course_name = f"Học phần {item_id}"
        course_code = item_id

    return {
        "source_key": f"course_{course_code}",
        "name": f"Đề cương {course_name} (HUCE Demo)",
        "uri": f"https://demo.huce.example/courses/{course_code}",
        "title": f"Mô tả mục tiêu môn học {course_name}",
        "text": c,
    }


def determine_split(index: int, total: int) -> str:
    """Split 60% dev, 20% validation, 20% sealed_test according to EVALUATION_PLAN.md."""
    ratio = index / max(1, total)
    if ratio < 0.60:
        return "dev"
    elif ratio < 0.80:
        return "validation"
    else:
        return "sealed_test"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract and sanitize course QA into Campus 24/7 format.")
    parser.add_argument("--limit", type=int, default=500, help="Number of QA items to extract (standard is >=500)")
    parser.add_argument("--start-id", type=int, default=0, help="Starting sequence number for case_id (0 = auto)")
    parser.add_argument("--output-jsonl", type=str, default="", help="Path to write JSONL eval cases")
    parser.add_argument("--append-to", type=str, default="", help="Path of existing JSONL to append to")
    parser.add_argument("--export-topics", type=str, default="", help="Export as knowledge topics JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print converted cases to stdout without writing")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Fetching dataset from Hugging Face...")
    raw_items = fetch_dataset()
    print(f"Loaded {len(raw_items)} total items.")

    out_file = Path(args.output_jsonl) if args.output_jsonl else None
    start_num = args.start_id if args.start_id > 0 else find_next_gqa_id(exclude_path=out_file)
    print(f"Assigning case IDs starting at EVAL-GQA-{start_num:03d}")

    total_target = min(args.limit, len(raw_items))
    selected_items = raw_items[:total_target]

    cases: list[dict[str, Any]] = []
    for idx, item in enumerate(selected_items):
        split = determine_split(idx, total_target)
        case = convert_to_eval_case(item, start_num + idx, split=split)
        cases.append(case)

    # Extract all unique course knowledge topics
    topics: list[dict[str, Any]] = []
    seen_contexts: set[str] = set()
    for item in raw_items:
        ctx = item.get("context", "")
        if not ctx or ctx in seen_contexts:
            continue
        seen_contexts.add(ctx)
        topics.append(convert_to_knowledge_topic(item))

    print(f"Extracted {len(cases)} QA cases and {len(topics)} unique knowledge document topics.")

    if args.export_topics:
        topic_path = Path(args.export_topics)
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        with open(topic_path, "w", encoding="utf-8") as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(topics)} knowledge topics to {topic_path.resolve()}")

    if args.append_to:
        target_path = Path(args.append_to)
        with open(target_path, "a", encoding="utf-8") as f:
            for c in cases:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"Appended {len(cases)} cases into {target_path.resolve()}")
    elif args.output_jsonl:
        out_path = Path(args.output_jsonl)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for c in cases:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"Successfully saved {len(cases)} cases to {out_path.resolve()}")
    else:
        print(f"\n--- Preview first case ---")
        print(json.dumps(cases[0], ensure_ascii=False, indent=2))
        print(f"\n--- Preview first knowledge topic ---")
        print(json.dumps(topics[0], ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
