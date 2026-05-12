#!/usr/bin/env python3
"""Build and update Hunch self models from evidence records.

The v0 implementation is deterministic and stdlib-only. It treats self model
items as evidence-backed claims, not permanent personality labels.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple, Union

from generate_answer import contains_korean, load_jsonl, record_source_type, split_sentences, tokenize

MODEL_FIELDS = [
    "core_desires",
    "values",
    "constraints",
    "recurring_conflicts",
    "emotional_patterns",
    "growth_signals",
    "temporary_state",
    "identity_statements",
    "open_questions",
]

FIELD_CUES = {
    "core_desires": (
        "i want",
        "i hope",
        "i care",
        "want to",
        "move toward",
        "원해",
        "원하",
        "원한다",
        "원하는",
        "원했",
        "싶",
        "바라",
    ),
    "values": (
        "i value",
        "matters more",
        "important",
        "decision criteria",
        "가치",
        "중요",
        "소중",
    ),
    "constraints": (
        "runway",
        "cannot",
        "can't",
        "need",
        "depend",
        "mortgage",
        "rent",
        "deadline",
        "travel",
        "late meeting",
        "sleep",
        "budget",
        "월세",
        "수입",
        "런웨이",
        "채용",
        "마감",
        "출장",
        "회의",
        "수면",
        "부모님",
        "가족",
        "예산",
        "비용",
    ),
    "recurring_conflicts": (
        "but",
        "between",
        "tension",
        "all-or-nothing",
        "versus",
        "vs",
        "하지만",
        "그런데",
        "긴장",
        "전부 아니면 전무",
        "사이",
    ),
    "emotional_patterns": (
        "when",
        "after",
        "then",
        "compare",
        "avoid",
        "freeze",
        "panic",
        "anxiety",
        "guilty",
        "ashamed",
        "criticize",
        "때",
        "후",
        "비교",
        "회피",
        "미루",
        "불안",
        "패닉",
        "죄책감",
        "수치",
        "비난",
    ),
    "growth_signals": (
        "improved",
        "worked",
        "felt better",
        "reduced",
        "clearer",
        "steadier",
        "small experiment",
        "bounded experiment",
        "learning experiment",
        "나아",
        "나았",
        "좋아",
        "줄었",
        "효과",
        "도움",
        "선명",
        "편했",
        "작은 실험",
        "학습",
    ),
    "temporary_state": (
        "today",
        "this week",
        "right now",
        "exhausted",
        "tired",
        "bad sleep",
        "panic",
        "오늘",
        "이번 주",
        "지금",
        "지쳐",
        "피곤",
        "수면이 나쁘",
        "패닉",
    ),
    "identity_statements": (
        "i am",
        "i'm",
        "i feel like",
        "나는",
        "내가",
        "처럼 느껴",
    ),
    "open_questions": (
        "?",
        "should i",
        "how do i",
        "what is",
        "뭘까",
        "어떻게",
        "해야 할까",
    ),
}

CONCEPT_RULES = (
    ("career_product_influence", ("product influence", "product design", "portfolio", "role", "제품 결정", "프로덕트", "포트폴리오", "이직")),
    ("financial_stability", ("rent", "parents", "salary", "income", "mortgage", "월세", "부모님", "수입", "연봉")),
    ("comparison_avoidance", ("compare", "friends", "peers", "freeze", "avoid", "비교", "동료", "친구", "얼어붙", "회피")),
    ("relationship_boundaries", ("boundary", "breakup", "relationship", "abandonment", "경계", "이별", "관계", "버려질")),
    ("sustainable_company", ("sustainable company", "runway", "pivot", "roadmap", "customer", "investor", "feedback", "지속 가능한 회사", "런웨이", "피벗", "로드맵", "고객", "투자자", "피드백", "팀")),
    ("research_depth", ("research", "thesis", "writing sprint", "lab", "depth", "연구", "논문", "글쓰기", "연구실", "깊이")),
    ("health_family_presence", ("health", "family", "sleep", "workout", "walk", "promotion", "건강", "가족", "수면", "운동", "산책", "승진")),
    ("small_bounded_experiment", ("small experiment", "bounded", "sprint", "45 minute", "작은 실험", "스프린트", "45분")),
)

SENSITIVE_FIELDS = {"identity_statements", "temporary_state"}


def normalize_text(text: str) -> str:
    tokens = tokenize(text)
    if not tokens:
        return re.sub(r"\s+", "-", text.strip().lower())[:48]
    return "-".join(tokens[:8])


def concept_key(field: str, text: str) -> str:
    lowered = text.lower()
    for concept, cues in CONCEPT_RULES:
        if any(cue in lowered for cue in cues):
            return f"{field}:{concept}"
    return f"{field}:{normalize_text(text)}"


def claim_id(field: str, key: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9가-힣:_-]+", "-", key).strip("-")
    return safe[:96] or f"{field}:unknown"


def clean_label(sentence: str) -> str:
    sentence = sentence.strip()
    sentence = re.sub(r"^(Journal|Reflection|Voice memo transcript|Call transcript|영상 전사|음성 메모 전사|긴 글|회고 글|고객 인터뷰 전사|고객 통화 전사|상담 메모 전사):\s*", "", sentence)
    return sentence[:220]


def date_span_days(dates: Iterable[str]) -> int:
    parsed = []
    for value in dates:
        try:
            parsed.append(datetime.fromisoformat(value).date())
        except ValueError:
            continue
    if len(parsed) < 2:
        return 0
    return (max(parsed) - min(parsed)).days


def source_record(case: Dict, record: Dict) -> Dict:
    return {
        "id": record.get("id"),
        "user_id": case.get("user_id"),
        "source_type": record_source_type(record),
        "date": record.get("date"),
        "text": record.get("text", ""),
        "case_id": case.get("case_id"),
        "language": case.get("language") or ("ko" if contains_korean(record.get("text", "")) else "en"),
    }


def collect_records(cases: Sequence[Dict]) -> Dict[str, List[Dict]]:
    records_by_user: Dict[str, List[Dict]] = defaultdict(list)
    seen_record_ids = set()
    for case in cases:
        user_id = case.get("user_id")
        if not user_id:
            continue
        for record in case.get("records", []):
            record_id = record.get("id")
            if record_id in seen_record_ids:
                continue
            seen_record_ids.add(record_id)
            records_by_user[user_id].append(source_record(case, record))
    return records_by_user


def fields_for_sentence(sentence: str) -> List[str]:
    lowered = sentence.lower()
    fields = []
    for field, cues in FIELD_CUES.items():
        if any(cue in lowered for cue in cues):
            fields.append(field)
    return fields


def extract_candidates(records: Sequence[Dict]) -> List[Dict]:
    candidates: List[Dict] = []
    for record in records:
        for sentence in split_sentences(record.get("text", "")):
            fields = fields_for_sentence(sentence)
            if not fields:
                continue
            label = clean_label(sentence)
            for field in fields:
                key = concept_key(field, label)
                candidates.append(
                    {
                        "field": field,
                        "key": key,
                        "label": label,
                        "evidence_id": record["id"],
                        "source_type": record["source_type"],
                        "date": record.get("date"),
                        "language": record.get("language"),
                    }
                )
    return candidates


def confidence_for(evidence_ids: Sequence[str], source_types: Sequence[str], span_days: int, explicit: bool) -> float:
    confidence = 0.45
    if explicit:
        confidence += 0.10
    if len(evidence_ids) >= 2:
        confidence += 0.10
    if len(source_types) >= 2:
        confidence += 0.10
    if span_days >= 7 and len(evidence_ids) >= 2:
        confidence += 0.10
    return round(min(confidence, 0.90), 2)


def stability_for(field: str, evidence_ids: Sequence[str], source_types: Sequence[str], span_days: int) -> str:
    if field == "temporary_state":
        return "temporary"
    if len(evidence_ids) >= 2 and len(source_types) >= 2 and span_days >= 7:
        return "stable"
    if len(evidence_ids) >= 2 or len(source_types) >= 2:
        return "recurring"
    return "temporary"


def status_for(field: str, confidence: float, evidence_ids: Sequence[str], source_types: Sequence[str]) -> str:
    if field in SENSITIVE_FIELDS:
        return "candidate"
    if (len(evidence_ids) >= 2 or len(source_types) >= 2) and confidence >= 0.60:
        return "active"
    return "candidate"


def merge_candidates(user_id: str, candidates: Sequence[Dict]) -> Tuple[Dict, List[Dict]]:
    grouped: Dict[Tuple[str, str], List[Dict]] = defaultdict(list)
    for candidate in candidates:
        grouped[(candidate["field"], candidate["key"])].append(candidate)

    model = {
        "user_id": user_id,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        **{field: [] for field in MODEL_FIELDS},
    }
    changelog = []

    for (field, key), items in sorted(grouped.items()):
        evidence_ids = sorted({item["evidence_id"] for item in items if item.get("evidence_id")})
        source_types = sorted({item["source_type"] for item in items if item.get("source_type")})
        dates = sorted({item["date"] for item in items if item.get("date")})
        labels = [item["label"] for item in items if item.get("label")]
        label = labels[0] if labels else key
        span_days = date_span_days(dates)
        explicit = field in {"core_desires", "values", "identity_statements"}
        confidence = confidence_for(evidence_ids, source_types, span_days, explicit)
        stability = stability_for(field, evidence_ids, source_types, span_days)
        status = status_for(field, confidence, evidence_ids, source_types)

        claim = {
            "id": claim_id(field, key),
            "field": field,
            "label": label,
            "evidence_ids": evidence_ids,
            "source_types": source_types,
            "confidence": confidence,
            "first_seen": dates[0] if dates else None,
            "last_seen": dates[-1] if dates else None,
            "stability": stability,
            "status": status,
        }
        model[field].append(claim)
        changelog.append(
            {
                "user_id": user_id,
                "claim_id": claim["id"],
                "field": field,
                "action": "promote" if status == "active" else "create_candidate",
                "confidence": confidence,
                "evidence_ids": evidence_ids,
                "source_types": source_types,
                "reason": "repeated evidence/source support" if status == "active" else "needs more support or user confirmation",
            }
        )

    return model, changelog


def build_self_models(cases: Sequence[Dict]) -> Tuple[List[Dict], List[Dict]]:
    records_by_user = collect_records(cases)
    models = []
    changelog = []
    for user_id, records in sorted(records_by_user.items()):
        candidates = extract_candidates(records)
        model, user_changelog = merge_candidates(user_id, candidates)
        models.append(model)
        changelog.extend(user_changelog)
    return models, changelog


def write_json(path: Path, payload: Union[Dict, List[Dict]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build evidence-backed Hunch self models.")
    parser.add_argument("--dataset", type=Path, default=Path("eval_dataset_v0_source_types.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("self_model_runs"))
    args = parser.parse_args()

    cases = load_jsonl(args.dataset)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    models, changelog = build_self_models(cases)
    write_json(run_dir / "self_models.json", models)
    with (run_dir / "changelog.jsonl").open("w", encoding="utf-8") as f:
        for row in changelog:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "run_id": run_id,
        "dataset": str(args.dataset),
        "total_users": len(models),
        "total_claims": sum(len(model[field]) for model in models for field in MODEL_FIELDS),
        "active_claims": sum(
            1
            for model in models
            for field in MODEL_FIELDS
            for claim in model[field]
            if claim["status"] == "active"
        ),
        "generated_files": {
            "self_models": str(run_dir / "self_models.json"),
            "changelog": str(run_dir / "changelog.jsonl"),
        },
    }
    write_json(run_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
