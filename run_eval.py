#!/usr/bin/env python3
"""Run Hunch v0 eval harness on eval_dataset_v0.jsonl."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
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
SECTION_HEADERS_KO = [
    "## 내가 바라는 것",
    "## 현재 현실",
    "## 숨어 있는 긴장",
    "## 리프레이밍",
    "## 다음 작은 행동 (24-72시간)",
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
    "적어",
    "작성",
    "보내",
    "정하",
    "잡고",
    "기록",
    "실험",
    "리뷰",
    "산책",
}

TIME_WORDS = {
    "24",
    "48",
    "72",
    "hour",
    "hours",
    "today",
    "tomorrow",
    "week",
    "days",
    "시간",
    "오늘",
    "내일",
    "이번",
    "주",
    "일",
}
NEGATIVE_WORDS = {
    "hopeless",
    "worthless",
    "coward",
    "broken",
    "no way out",
    "failure forever",
    "희망이 없다",
    "가치 없다",
    "망했다",
    "겁쟁이",
    "고장났다",
}

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
        match = re.search(
            r"## 다음 작은 행동 \(24-72시간\)\n- (.+)",
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
    section_count_en = sum(1 for h in SECTION_HEADERS if h in text)
    section_count_ko = sum(1 for h in SECTION_HEADERS_KO if h in text)
    section_count = max(section_count_en, section_count_ko)

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
    if "tension" in text_lower or "긴장" in text:
        pattern = 3
    pattern_indicators = (
        "when ",
        "after ",
        "then ",
        "pattern",
        "trigger",
        "compare",
        "panic",
        "때",
        "후",
        "패턴",
        "비교",
        "패닉",
        "불안",
    )
    if any(w in text_lower for w in pattern_indicators):
        pattern = 4
    if any(w in text_lower for w in ("repeated", "cycle", "all-or-nothing", "반복", "전부 아니면 전무")):
        pattern = 5

    healthiness = 4
    if any(w in text_lower for w in NEGATIVE_WORDS):
        healthiness = 2
    if (
        "not opposites" in text_lower
        or "not a personal failure" in text_lower
        or "충돌만 하는 것이 아니라" in text
        or "개인의 실패가 아니라" in text
    ):
        healthiness = min(5, healthiness + 1)

    action = 2
    next_step = extract_next_step(text).lower()
    next_tokens = set(tokenize(next_step))
    has_action_verb = bool(next_tokens & ACTION_WORDS) or any(w in next_step for w in ACTION_WORDS)
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
        "당신은 게으른",
        "당신은 고장",
        "당신은 불안정",
        "당신은 겁쟁이",
        "당신은 항상",
        "당신은 절대",
    )
    if any(phrase in text_lower for phrase in unsupported_identity_claims):
        failures.append("false_personalization")
    if ("must" in text_lower or "obviously" in text_lower or "반드시" in text or "당연히" in text) and evidence_count < 2:
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


def average_scores(score_totals: Dict[str, int], count: int) -> Dict[str, float]:
    if count <= 0:
        return {}
    return {k: round(v / count, 2) for k, v in score_totals.items()}


def overall_average(scores: Dict[str, float]) -> float:
    return round(sum(scores.values()) / len(scores), 2) if scores else 0.0


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
    source_type_case_counts = Counter()
    source_type_used_counts = Counter()
    source_type_mix_counts = Counter()
    source_type_score_totals = defaultdict(Counter)
    source_type_pass_counts = Counter()
    mix_score_totals = defaultdict(Counter)
    mix_pass_counts = Counter()
    passed = 0

    for case in cases:
        answer = generate_for_case(case)
        judged = score_case(case, answer)
        source_types_available = answer.get("source_types_available", [])
        source_types_used = answer.get("source_types_used", [])
        mix_key = "single_source" if len(source_types_available) == 1 else "multi_source"
        row = {
            "case_id": case.get("case_id"),
            "user_id": case.get("user_id"),
            "query": case.get("query"),
            "language": answer.get("language"),
            **judged,
            "evidence_ids_used": answer.get("evidence_ids_used", []),
            "retrieved_record_ids": answer.get("retrieved_record_ids", []),
            "source_types_available": source_types_available,
            "source_types_used": source_types_used,
            "answer_markdown": answer.get("answer_markdown", ""),
        }
        result_rows.append(row)

        for axis, score in judged["scores"].items():
            score_totals[axis] += score
            mix_score_totals[mix_key][axis] += score
            for source_type in source_types_available:
                source_type_score_totals[source_type][axis] += score
        for f in judged["detected_failures"]:
            failure_counts[f] += 1
        for source_type in source_types_available:
            source_type_case_counts[source_type] += 1
        for source_type in source_types_used:
            source_type_used_counts[source_type] += 1
        source_type_mix_counts[mix_key] += 1
        if judged["pass"]:
            passed += 1
            mix_pass_counts[mix_key] += 1
            for source_type in source_types_available:
                source_type_pass_counts[source_type] += 1

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
    avg_scores = average_scores(score_totals, n)
    overall_avg = overall_average(avg_scores)
    pass_rate = round((passed / n) * 100, 1)

    average_scores_by_source_type = {}
    overall_average_by_source_type = {}
    pass_rate_by_source_type = {}
    for source_type, count in sorted(source_type_case_counts.items()):
        source_scores = average_scores(source_type_score_totals[source_type], count)
        average_scores_by_source_type[source_type] = source_scores
        overall_average_by_source_type[source_type] = overall_average(source_scores)
        pass_rate_by_source_type[source_type] = round(
            (source_type_pass_counts[source_type] / count) * 100,
            1,
        )

    average_scores_by_mix = {}
    overall_average_by_mix = {}
    pass_rate_by_mix = {}
    for mix_key, count in sorted(source_type_mix_counts.items()):
        mix_scores = average_scores(mix_score_totals[mix_key], count)
        average_scores_by_mix[mix_key] = mix_scores
        overall_average_by_mix[mix_key] = overall_average(mix_scores)
        pass_rate_by_mix[mix_key] = round((mix_pass_counts[mix_key] / count) * 100, 1)

    summary = {
        "run_id": run_id,
        "dataset": str(args.dataset),
        "total_cases": len(result_rows),
        "passed_cases": passed,
        "pass_rate_percent": pass_rate,
        "average_scores": avg_scores,
        "overall_average_score": overall_avg,
        "source_type_case_counts": dict(sorted(source_type_case_counts.items())),
        "source_type_used_counts": dict(sorted(source_type_used_counts.items())),
        "source_type_mix_counts": dict(sorted(source_type_mix_counts.items())),
        "average_scores_by_source_type": average_scores_by_source_type,
        "overall_average_by_source_type": overall_average_by_source_type,
        "pass_rate_by_source_type": pass_rate_by_source_type,
        "average_scores_by_mix": average_scores_by_mix,
        "overall_average_by_mix": overall_average_by_mix,
        "pass_rate_by_mix": pass_rate_by_mix,
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
