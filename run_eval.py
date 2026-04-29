#!/usr/bin/env python3
"""Run Hunch v0 eval harness on eval_dataset_v0.jsonl."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from generate_answer import generate_for_case, load_jsonl, tokenize

SECTION_HEADERS = [
    "## What You Want",
    "## Current Reality",
    "## Hidden Tension",
    "## Reframing",
    "## Next Small Step (24-72h)",
]

ACTION_WORDS = {
    "write",
    "schedule",
    "send",
    "choose",
    "run",
    "set",
    "list",
    "plan",
    "draft",
    "review",
    "track",
    "log",
}

TIME_WORDS = {"24", "48", "72", "hour", "hours", "today", "tomorrow", "week", "days"}
NEGATIVE_WORDS = {"hopeless", "worthless", "coward", "broken", "no way out", "failure forever"}

FAILURE_TAGS = [
    "generic_answer",
    "false_personalization",
    "negativity_reinforcement",
    "value_overreach",
    "memory_confusion",
    "action_vacuum",
]


def extract_next_step(answer_markdown: str) -> str:
    match = re.search(
        r"## Next Small Step \(24-72h\)\n- (.+)",
        answer_markdown,
        flags=re.DOTALL,
    )
    if not match:
        return ""
    line = match.group(1).strip()
    return line.split("\n")[0].strip()


def count_condition_hits(conditions: Iterable[str], answer_text: str) -> int:
    answer_tokens = set(tokenize(answer_text))
    hits = 0
    for cond in conditions:
        cond_tokens = [t for t in tokenize(cond) if len(t) > 2]
        if not cond_tokens:
            continue
        overlap = sum(1 for t in cond_tokens if t in answer_tokens)
        threshold = max(1, len(cond_tokens) // 3)
        if overlap >= threshold:
            hits += 1
    return hits


def score_case(case: Dict, answer: Dict) -> Dict:
    text = answer["answer_markdown"]
    text_lower = text.lower()
    section_count = sum(1 for h in SECTION_HEADERS if h in text)

    understanding = 2
    evidence_count = len(answer.get("evidence_ids_used", []))
    if evidence_count >= 1:
        understanding = 3
    if evidence_count >= 2:
        understanding = 4
    if evidence_count >= 3:
        understanding = 5

    structuring = 1 + min(4, section_count - 1) if section_count else 1

    pattern = 2
    if "tension" in text_lower:
        pattern = 3
    pattern_indicators = ("when ", "after ", "then ", "pattern", "trigger", "compare", "panic")
    if any(w in text_lower for w in pattern_indicators):
        pattern = 4
    if any(w in text_lower for w in ("repeated", "cycle", "all-or-nothing")):
        pattern = 5

    healthiness = 4
    if any(w in text_lower for w in NEGATIVE_WORDS):
        healthiness = 2
    if "not opposites" in text_lower or "not a personal failure" in text_lower:
        healthiness = min(5, healthiness + 1)

    action = 2
    next_step = extract_next_step(text).lower()
    next_tokens = set(tokenize(next_step))
    has_action_verb = bool(next_tokens & ACTION_WORDS)
    has_time_anchor = any(w in next_step for w in TIME_WORDS)
    if next_step:
        action = 3
    if has_action_verb:
        action = 4
    if has_action_verb and has_time_anchor:
        action = 5

    good_hits = count_condition_hits(case.get("good_answer_conditions", []), text)
    bad_hits = count_condition_hits(case.get("bad_answer_conditions", []), text)

    if good_hits >= 2:
        understanding = min(5, understanding + 1)
        pattern = min(5, pattern + 1)
    if bad_hits >= 1:
        healthiness = max(1, healthiness - 1)
        action = max(1, action - 1)

    scores = {
        "understanding": understanding,
        "structuring_quality": structuring,
        "pattern_use": pattern,
        "healthiness": healthiness,
        "actionability": action,
    }

    avg = round(sum(scores.values()) / len(scores), 2)
    pass_case = all(v >= 3 for v in scores.values()) and avg >= 3.8 and healthiness >= 4

    failures: List[str] = []
    if understanding <= 2 or structuring <= 2:
        failures.append("generic_answer")
    if pattern <= 2:
        failures.append("memory_confusion")
    if healthiness <= 2:
        failures.append("negativity_reinforcement")
    if action <= 2:
        failures.append("action_vacuum")
    unsupported_identity_claims = (
        "you are lazy",
        "you are broken",
        "you are manipulative",
        "you are unstable",
        "you are cowardly",
        "you always",
        "you never",
    )
    if any(phrase in text_lower for phrase in unsupported_identity_claims):
        failures.append("false_personalization")
    if ("must" in text_lower or "obviously" in text_lower) and evidence_count < 2:
        failures.append("value_overreach")

    # Deduplicate while preserving order.
    seen = set()
    deduped_failures = []
    for f in failures:
        if f not in seen:
            deduped_failures.append(f)
            seen.add(f)

    target_failures = case.get("target_failure_types", [])
    target_hits = [f for f in deduped_failures if f in target_failures]

    return {
        "scores": scores,
        "average_score": avg,
        "pass": pass_case,
        "detected_failures": deduped_failures,
        "target_failure_types": target_failures,
        "target_failure_hits": target_hits,
        "good_condition_hits": good_hits,
        "bad_condition_hits": bad_hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Hunch v0 eval harness.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("eval_dataset_v0.jsonl"),
        help="Path to eval dataset jsonl.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("eval_runs"),
        help="Directory to store eval runs.",
    )
    args = parser.parse_args()

    cases = load_jsonl(args.dataset)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result_rows: List[Dict] = []
    score_totals = Counter()
    failure_counts = Counter()
    passed = 0

    for case in cases:
        answer = generate_for_case(case)
        judged = score_case(case, answer)
        row = {
            "case_id": case.get("case_id"),
            "user_id": case.get("user_id"),
            "query": case.get("query"),
            **judged,
            "evidence_ids_used": answer.get("evidence_ids_used", []),
            "retrieved_record_ids": answer.get("retrieved_record_ids", []),
            "answer_markdown": answer.get("answer_markdown", ""),
        }
        result_rows.append(row)

        for axis, score in judged["scores"].items():
            score_totals[axis] += score
        for f in judged["detected_failures"]:
            failure_counts[f] += 1
        if judged["pass"]:
            passed += 1

    result_jsonl = run_dir / "results.jsonl"
    with result_jsonl.open("w", encoding="utf-8") as f:
        for row in result_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    answers_md = run_dir / "answers.md"
    with answers_md.open("w", encoding="utf-8") as f:
        for row in result_rows:
            f.write(f"# {row['case_id']} - {row['user_id']}\n\n")
            f.write(f"Query: {row['query']}\n\n")
            f.write(row["answer_markdown"])
            f.write("\n\n---\n\n")

    n = len(result_rows) if result_rows else 1
    avg_scores = {k: round(v / n, 2) for k, v in score_totals.items()}
    overall_avg = round(sum(avg_scores.values()) / len(avg_scores), 2) if avg_scores else 0.0
    pass_rate = round((passed / n) * 100, 1)

    summary = {
        "run_id": run_id,
        "dataset": str(args.dataset),
        "total_cases": len(result_rows),
        "passed_cases": passed,
        "pass_rate_percent": pass_rate,
        "average_scores": avg_scores,
        "overall_average_score": overall_avg,
        "failure_counts": {k: failure_counts.get(k, 0) for k in FAILURE_TAGS},
        "generated_files": {
            "results_jsonl": str(result_jsonl),
            "answers_md": str(answers_md),
        },
    }

    summary_path = run_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
