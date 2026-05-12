#!/usr/bin/env python3
"""Evaluate Hunch self model update quality."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence

from generate_answer import load_jsonl, record_source_type
from update_self_model import MODEL_FIELDS, build_self_models, collect_records, write_json


def flatten_claims(model: Dict) -> List[Dict]:
    return [claim for field in MODEL_FIELDS for claim in model.get(field, [])]


def score_ratio(ratio: float) -> int:
    if ratio >= 0.95:
        return 5
    if ratio >= 0.80:
        return 4
    if ratio >= 0.60:
        return 3
    if ratio >= 0.40:
        return 2
    return 1


def score_field_coverage(fields_with_claims: Sequence[str]) -> int:
    count = len(set(fields_with_claims))
    if count >= 7:
        return 5
    if count >= 5:
        return 4
    if count >= 4:
        return 3
    if count >= 2:
        return 2
    return 1


def score_promotion_safety(claims: Sequence[Dict]) -> int:
    unsafe = 0
    for claim in claims:
        active = claim.get("status") == "active"
        few_sources = len(claim.get("source_types", [])) <= 1
        few_evidence = len(claim.get("evidence_ids", [])) <= 1
        if active and claim.get("field") in {"temporary_state", "identity_statements"}:
            unsafe += 1
        if active and few_sources and few_evidence:
            unsafe += 1
    if unsafe == 0:
        return 5
    if unsafe == 1:
        return 3
    return 1


def score_future_actionability(claims: Sequence[Dict]) -> int:
    active_claims = [claim for claim in claims if claim.get("status") == "active"]
    active_fields = {claim.get("field") for claim in active_claims}
    core_fields = {"core_desires", "constraints", "emotional_patterns", "growth_signals"}
    if len(active_claims) >= 4 and len(active_fields & core_fields) >= 3:
        return 5
    if len(active_claims) >= 3 and len(active_fields & core_fields) >= 2:
        return 4
    if len(active_claims) >= 2:
        return 3
    if len(active_claims) == 1:
        return 2
    return 1


def score_user_model(model: Dict, available_source_types: Sequence[str]) -> Dict:
    claims = flatten_claims(model)
    claim_count = len(claims)
    grounded = [claim for claim in claims if claim.get("evidence_ids")]
    fields_with_claims = [claim.get("field") for claim in claims if claim.get("field")]
    used_source_types = sorted({source for claim in claims for source in claim.get("source_types", [])})

    evidence_grounding = score_ratio(len(grounded) / claim_count) if claim_count else 1
    field_coverage = score_field_coverage(fields_with_claims)
    source_coverage = score_ratio(
        len(set(used_source_types) & set(available_source_types)) / len(set(available_source_types))
    ) if available_source_types else 1
    promotion_safety = score_promotion_safety(claims)
    actionability = score_future_actionability(claims)

    scores = {
        "evidence_grounding": evidence_grounding,
        "field_coverage": field_coverage,
        "source_coverage": source_coverage,
        "promotion_safety": promotion_safety,
        "actionability_for_future_answers": actionability,
    }
    average_score = round(sum(scores.values()) / len(scores), 2)
    return {
        "user_id": model.get("user_id"),
        "scores": scores,
        "average_score": average_score,
        "pass": all(score >= 3 for score in scores.values()) and average_score >= 3.8,
        "claim_count": claim_count,
        "active_claim_count": sum(1 for claim in claims if claim.get("status") == "active"),
        "available_source_types": sorted(set(available_source_types)),
        "used_source_types": used_source_types,
        "fields_with_claims": sorted(set(fields_with_claims)),
    }


def summarize(results: Sequence[Dict]) -> Dict:
    totals = Counter()
    passed = 0
    for result in results:
        for axis, score in result["scores"].items():
            totals[axis] += score
        if result["pass"]:
            passed += 1
    n = len(results) or 1
    average_scores = {axis: round(value / n, 2) for axis, value in totals.items()}
    return {
        "total_users": len(results),
        "passed_users": passed,
        "pass_rate_percent": round((passed / n) * 100, 1),
        "average_scores": average_scores,
        "overall_average_score": round(sum(average_scores.values()) / len(average_scores), 2)
        if average_scores
        else 0.0,
    }


def source_types_by_user(cases: Sequence[Dict]) -> Dict[str, List[str]]:
    source_types = defaultdict(set)
    for user_id, records in collect_records(cases).items():
        for record in records:
            source_types[user_id].add(record_source_type(record))
    return {user_id: sorted(values) for user_id, values in source_types.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run self model update eval.")
    parser.add_argument("--dataset", type=Path, default=Path("eval_dataset_v0_source_types.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("self_model_eval_runs"))
    args = parser.parse_args()

    cases = load_jsonl(args.dataset)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    models, changelog = build_self_models(cases)
    available_by_user = source_types_by_user(cases)
    results = [
        score_user_model(model, available_by_user.get(model.get("user_id"), []))
        for model in models
    ]
    summary = {
        "run_id": run_id,
        "dataset": str(args.dataset),
        **summarize(results),
        "generated_files": {
            "self_models": str(run_dir / "self_models.json"),
            "changelog": str(run_dir / "changelog.jsonl"),
            "results": str(run_dir / "results.json"),
        },
    }

    write_json(run_dir / "self_models.json", models)
    write_json(run_dir / "results.json", results)
    write_json(run_dir / "summary.json", summary)
    with (run_dir / "changelog.jsonl").open("w", encoding="utf-8") as f:
        for row in changelog:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

