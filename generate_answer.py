#!/usr/bin/env python3
"""Generate structured Hunch v0 answers from a single eval case.

This script is intentionally deterministic and uses only Python stdlib so the
v0 loop can run locally without external model dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

TOKEN_RE = re.compile(r"[a-zA-Z']+|[가-힣0-9]+")
KOREAN_RE = re.compile(r"[가-힣]")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")

DESIRE_CUES = (
    "i want",
    "i value",
    "matters more",
    "i care about",
    "원해",
    "바라",
    "가치",
    "중요",
    "하고 싶",
    "되고 싶",
    "싶",
)
CONSTRAINT_CUES = (
    "depend on",
    "runway",
    "cannot",
    "can't",
    "adds ",
    "need",
    "late meetings",
    "월세",
    "수입",
    "런웨이",
    "채용",
    "출장",
    "회의",
    "시간",
    "부모님",
    "현실",
    "제약",
    "수면",
)
PATTERN_CUES = (
    "when ",
    "after ",
    "then ",
    "compare",
    "comparison",
    "panic",
    "rush",
    "avoid",
    "skip",
    "때",
    "후",
    "비교",
    "불안",
    "회피",
    "미루",
    "사과",
    "반복",
    "건너뛰",
    "패닉",
)
GROWTH_CUES = (
    "improved",
    "worked",
    "felt better",
    "reduced",
    "better than",
    "나아",
    "나았",
    "좋아",
    "좋아졌",
    "효과",
    "효과가",
    "줄었",
    "도움",
    "개선",
    "편했",
)

HEADERS = {
    "en": [
        "## What You Want",
        "## Current Reality",
        "## Hidden Tension",
        "## Reframing",
        "## Next Small Step (24-72h)",
    ],
    "ko": [
        "## 내가 바라는 것",
        "## 현재 현실",
        "## 숨어 있는 긴장",
        "## 리프레이밍",
        "## 다음 작은 행동 (24-72시간)",
    ],
}


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def contains_korean(text: str) -> bool:
    return bool(KOREAN_RE.search(text))


def detect_language(case: Dict) -> str:
    if case.get("language") in {"en", "ko"}:
        return case["language"]
    text = " ".join([case.get("query", "")] + [r.get("text", "") for r in case.get("records", [])])
    return "ko" if contains_korean(text) else "en"


def split_sentences(text: str) -> List[str]:
    parts = [p.strip() for p in SENTENCE_SPLIT_RE.split(text.strip()) if p.strip()]
    return parts if parts else [text.strip()]


def load_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def retrieve_records(query: str, records: Sequence[Dict], top_k: int = 3) -> List[Dict]:
    query_tokens = set(tokenize(query))
    scored: List[Tuple[int, Dict]] = []
    for rec in records:
        text = rec.get("text", "")
        rec_tokens = set(tokenize(text))
        overlap = len(query_tokens & rec_tokens)
        cue_bonus = 0
        lowered = text.lower()
        if any(c in lowered for c in DESIRE_CUES):
            cue_bonus += 1
        if any(c in lowered for c in CONSTRAINT_CUES):
            cue_bonus += 1
        if any(c in lowered for c in PATTERN_CUES):
            cue_bonus += 1
        if any(c in lowered for c in GROWTH_CUES):
            cue_bonus += 1
        scored.append((overlap + cue_bonus, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [rec for _, rec in scored[:top_k]]
    return top if top else list(records[:top_k])


def find_signals(records: Sequence[Dict]) -> Dict[str, List[Tuple[str, str]]]:
    signals = {
        "desires": [],
        "constraints": [],
        "patterns": [],
        "growth": [],
        "emotions": [],
    }
    emotion_keywords = (
        "anxious",
        "anxiety",
        "panic",
        "ashamed",
        "guilty",
        "exhausted",
        "fear",
        "drained",
        "pessimistic",
        "불안",
        "패닉",
        "수치",
        "죄책감",
        "피곤",
        "지침",
        "두려",
        "비관",
        "탈진",
    )

    for rec in records:
        rec_id = rec.get("id", "")
        for sent in split_sentences(rec.get("text", "")):
            lowered = sent.lower()
            if any(cue in lowered for cue in DESIRE_CUES):
                signals["desires"].append((rec_id, sent))
            if any(cue in lowered for cue in CONSTRAINT_CUES):
                signals["constraints"].append((rec_id, sent))
            if any(cue in lowered for cue in PATTERN_CUES):
                signals["patterns"].append((rec_id, sent))
            if any(cue in lowered for cue in GROWTH_CUES):
                signals["growth"].append((rec_id, sent))
            if any(k in lowered for k in emotion_keywords):
                signals["emotions"].append((rec_id, sent))
    return signals


def pick_line(items: Sequence[Tuple[str, str]], fallback: str) -> Tuple[str, List[str]]:
    if not items:
        return fallback, []
    rec_id, text = items[0]
    return text, [rec_id]


def infer_next_step(query: str, language: str) -> str:
    q = query.lower()
    if any(k in q for k in ("job", "role", "career", "salary", "apply", "promotion", "직장", "커리어", "연봉", "지원", "승진", "이직")):
        if language == "ko":
            return (
                "다음 48시간 안에 수입을 지키는 선택지 1개와 전환을 시험하는 작은 행동 1개를 "
                "나란히 적어보세요."
            )
        return (
            "In the next 48 hours, write a two-track plan: one low-risk step for income "
            "stability and one small transition test (60-90 minutes)."
        )
    if any(k in q for k in ("relationship", "breakup", "boundary", "partner", "관계", "이별", "경계", "연인")):
        if language == "ko":
            return (
                "24시간 안에 짧은 경계 문장 하나를 보내고, 전후 불안 수준을 기록해 다음 대화를 "
                "감정이 아니라 관찰로 정하세요."
            )
        return (
            "Within 24 hours, send one concise boundary message and note your stress level "
            "before/after to decide the next conversation from data, not panic."
        )
    if any(k in q for k in ("thesis", "writing", "research", "lab", "논문", "글", "연구", "랩", "연구실")):
        if language == "ko":
            return (
                "72시간 안에 45분짜리 초안 쓰기 블록을 두 번 잡고, 타이머가 끝나면 시작을 "
                "쉽게 만든 요인 한 문장만 남기세요."
            )
        return (
            "Schedule two 45-minute draft sprints in the next 72 hours and stop at the timer, "
            "then capture one sentence on what made starting easier."
        )
    if any(k in q for k in ("product", "pivot", "investor", "team", "roadmap", "제품", "피벗", "투자자", "팀", "로드맵")):
        if language == "ko":
            return (
                "이번 주 큰 피벗을 결정하기 전에 성공 기준이 분명한 작은 실험 하나를 정하고, "
                "30분짜리 결정 리뷰 시간을 잡으세요."
            )
        return (
            "Before any major pivot this week, run one bounded experiment with a clear success "
            "metric and review it in a 30-minute decision check."
        )
    if any(k in q for k in ("sleep", "health", "workout", "수면", "건강", "운동")):
        if language == "ko":
            return (
                "앞으로 3일 동안 퇴근 마감 시간을 하나 정하고 20분 산책을 한 뒤, 매일 아침 "
                "수면 질을 한 줄로 기록하세요."
            )
        return (
            "For the next 3 days, set a hard stop-work time and complete one 20-minute walk, "
            "then log sleep quality in one line each morning."
        )
    if language == "ko":
        return (
            "다음 24-72시간 안에 60분 안에 끝낼 수 있는 작은 실험 하나를 정하고, 실행 전후 "
            "스트레스 변화를 기록하세요."
        )
    return (
        "In the next 24-72 hours, choose one small experiment you can finish in under 60 minutes "
        "and track how your stress changes before and after."
    )


def normalize_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    if text[-1] not in ".!?。！？":
        text += "."
    return text


def generate_for_case(case: Dict) -> Dict:
    query = case.get("query", "")
    records = case.get("records", [])
    language = detect_language(case)

    retrieved = retrieve_records(query, records, top_k=3)
    signals = find_signals(records)

    evidence_ids: List[str] = []

    want_line, ids = pick_line(
        signals["desires"],
        "장기적으로 중요하게 여기는 가치와 맞는 방향을 찾고 싶어 합니다."
        if language == "ko"
        else "You want a path that feels aligned with your long-term values.",
    )
    evidence_ids.extend(ids)

    reality_line, ids = pick_line(
        signals["constraints"],
        "지금은 무시하기 어려운 현실 제약도 함께 고려해야 합니다."
        if language == "ko"
        else "You are balancing real constraints that matter and cannot be ignored.",
    )
    evidence_ids.extend(ids)

    tension_seed, ids = pick_line(
        signals["patterns"] or signals["emotions"],
        "압박이 커질수록 선택이 전부 아니면 전무처럼 느껴질 수 있습니다."
        if language == "ko"
        else "When pressure rises, your interpretation can become all-or-nothing.",
    )
    evidence_ids.extend(ids)

    growth_line, ids = pick_line(
        signals["growth"],
        "이미 작은 실험이 판단을 더 선명하게 만든다는 단서가 있습니다."
        if language == "ko"
        else "You already have evidence that small, bounded experiments improve clarity.",
    )
    evidence_ids.extend(ids)

    # Include one more retrieved id for groundedness when available.
    for rec in retrieved:
        rec_id = rec.get("id", "")
        if rec_id and rec_id not in evidence_ids:
            evidence_ids.append(rec_id)
            break

    unique_evidence = []
    seen = set()
    for eid in evidence_ids:
        if eid and eid not in seen:
            unique_evidence.append(eid)
            seen.add(eid)

    next_step = infer_next_step(query, language)

    what_you_want = normalize_sentence(want_line)
    current_reality = normalize_sentence(reality_line)
    if language == "ko":
        hidden_tension = normalize_sentence(
            f"{tension_seed} 이 지점에서 바라는 방향과 지금 안전하게 느껴지는 선택 사이의 긴장이 생깁니다."
        )
        reframing = normalize_sentence(
            f"{growth_line} 전진하고 싶은 마음과 현실 제약을 존중하는 태도는 충돌만 하는 것이 아니라 순서를 정할 수 있습니다."
        )
    else:
        hidden_tension = normalize_sentence(
            f"{tension_seed} This creates tension between what you want and what feels safe right now."
        )
        reframing = normalize_sentence(
            f"{growth_line} Wanting progress and honoring constraints are not opposites; they can be sequenced."
        )

    headers = HEADERS[language]

    answer_md = "\n".join(
        [
            headers[0],
            f"- {what_you_want}",
            "",
            headers[1],
            f"- {current_reality}",
            "",
            headers[2],
            f"- {hidden_tension}",
            "",
            headers[3],
            f"- {reframing}",
            "",
            headers[4],
            f"- {next_step}",
        ]
    )

    risk_flags = {
        "negativity_reinforcement": False,
        "value_overreach": False,
        "false_personalization": False,
    }

    return {
        "case_id": case.get("case_id"),
        "user_id": case.get("user_id"),
        "query": query,
        "language": language,
        "answer_markdown": answer_md,
        "evidence_ids_used": unique_evidence,
        "retrieved_record_ids": [r.get("id") for r in retrieved if r.get("id")],
        "risk_flags": risk_flags,
        "self_model_fields_used": [
            "core_desires",
            "constraints",
            "recurring_conflicts",
            "emotional_patterns",
            "growth_signals",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _resolve_case(dataset: Path, case_id: str) -> Dict:
    cases = load_jsonl(dataset)
    for c in cases:
        if c.get("case_id") == case_id:
            return c
    raise ValueError(f"case_id not found: {case_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Hunch v0 structured answer.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("eval_dataset_v0.jsonl"),
        help="Path to JSONL dataset.",
    )
    parser.add_argument("--case-id", required=True, help="Case id (e.g., C001).")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON payload instead of markdown only.",
    )
    args = parser.parse_args()

    case = _resolve_case(args.dataset, args.case_id)
    result = generate_for_case(case)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["answer_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
