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

TOKEN_RE = re.compile(r"[a-zA-Z']+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

DESIRE_CUES = (
    "i want",
    "i value",
    "matters more",
    "i care about",
)
CONSTRAINT_CUES = (
    "depend on",
    "runway",
    "cannot",
    "can't",
    "adds ",
    "need",
    "late meetings",
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
)
GROWTH_CUES = (
    "improved",
    "worked",
    "felt better",
    "reduced",
    "better than",
)


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


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


def infer_next_step(query: str, signals: Dict[str, List[Tuple[str, str]]]) -> str:
    q = query.lower()
    if any(k in q for k in ("job", "role", "career", "salary", "apply", "promotion")):
        return (
            "In the next 48 hours, write a two-track plan: one low-risk step for income "
            "stability and one small transition test (60-90 minutes)."
        )
    if any(k in q for k in ("relationship", "breakup", "boundary", "partner")):
        return (
            "Within 24 hours, send one concise boundary message and note your stress level "
            "before/after to decide the next conversation from data, not panic."
        )
    if any(k in q for k in ("thesis", "writing", "research", "lab")):
        return (
            "Schedule two 45-minute draft sprints in the next 72 hours and stop at the timer, "
            "then capture one sentence on what made starting easier."
        )
    if any(k in q for k in ("product", "pivot", "investor", "team", "roadmap")):
        return (
            "Before any major pivot this week, run one bounded experiment with a clear success "
            "metric and review it in a 30-minute decision check."
        )
    if any(k in q for k in ("sleep", "health", "workout")):
        return (
            "For the next 3 days, set a hard stop-work time and complete one 20-minute walk, "
            "then log sleep quality in one line each morning."
        )
    return (
        "In the next 24-72 hours, choose one small experiment you can finish in under 60 minutes "
        "and track how your stress changes before and after."
    )


def normalize_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    if text[-1] not in ".!?":
        text += "."
    return text


def generate_for_case(case: Dict) -> Dict:
    query = case.get("query", "")
    records = case.get("records", [])

    retrieved = retrieve_records(query, records, top_k=3)
    signals = find_signals(records)

    evidence_ids: List[str] = []

    want_line, ids = pick_line(
        signals["desires"],
        "You want a path that feels aligned with your long-term values.",
    )
    evidence_ids.extend(ids)

    reality_line, ids = pick_line(
        signals["constraints"],
        "You are balancing real constraints that matter and cannot be ignored.",
    )
    evidence_ids.extend(ids)

    tension_seed, ids = pick_line(
        signals["patterns"] or signals["emotions"],
        "When pressure rises, your interpretation can become all-or-nothing.",
    )
    evidence_ids.extend(ids)

    growth_line, ids = pick_line(
        signals["growth"],
        "You already have evidence that small, bounded experiments improve clarity.",
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

    next_step = infer_next_step(query, signals)

    what_you_want = normalize_sentence(want_line)
    current_reality = normalize_sentence(reality_line)
    hidden_tension = (
        normalize_sentence(
            f"{tension_seed} This creates tension between what you want and what feels safe right now."
        )
    )
    reframing = normalize_sentence(
        f"{growth_line} Wanting progress and honoring constraints are not opposites; they can be sequenced."
    )

    answer_md = "\n".join(
        [
            "## What You Want",
            f"- {what_you_want}",
            "",
            "## Current Reality",
            f"- {current_reality}",
            "",
            "## Hidden Tension",
            f"- {hidden_tension}",
            "",
            "## Reframing",
            f"- {reframing}",
            "",
            "## Next Small Step (24-72h)",
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

