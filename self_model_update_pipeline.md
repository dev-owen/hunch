# Self Model Update Pipeline v0

## Goal
Hunch should improve its understanding of a user after every answer and every new input.
The self model is not a fixed profile. It is a living set of evidence-backed claims with confidence, recency, and review state.

## Core Principle
Never store "the user is X" as an unsupported conclusion.
Store "records A, B, and C suggest X with confidence Y" instead.

## Memory Layers

### 1. Raw Evidence
Raw evidence is the user's original input.

Examples:
- `note`: short self-report, quick thought, saved memory
- `chat`: conversational turn or reflection
- `writing`: long journal, essay, memo, decision note
- `video_transcript`: transcript from video/audio input
- `photo_context`: user-provided caption or explanation for a photo

Raw evidence should preserve:
- `id`
- `user_id`
- `source_type`
- `date`
- `text`
- optional metadata, such as `caption`, `tags`, `media_id`

### 2. Self Model
Self model is a structured set of claims extracted from raw evidence.

Each claim must include:
```json
{
  "id": "core_desires:stable-creative-career",
  "field": "core_desires",
  "label": "Wants product influence without losing financial stability",
  "evidence_ids": ["note_001", "chat_004"],
  "source_types": ["note", "chat"],
  "confidence": 0.72,
  "first_seen": "2026-04-21",
  "last_seen": "2026-05-12",
  "stability": "recurring",
  "status": "active"
}
```

## Update Flow
```text
New user input
  -> normalize source_type
  -> create evidence chunk
  -> extract self model candidates
  -> compare with existing claims
  -> merge, promote, lower confidence, or keep candidate
  -> write changelog
  -> use self model + raw evidence in future answers
```

## Candidate Extraction
Extract candidates into these fields:
- `core_desires`: what the user repeatedly wants or moves toward
- `values`: decision criteria the user explicitly names
- `constraints`: time, money, health, family, role, or energy limits
- `recurring_conflicts`: repeated tension between two poles
- `emotional_patterns`: repeated trigger -> emotion -> behavior loop
- `growth_signals`: healthier behavior or improved response
- `temporary_state`: short-lived mood or context that should not become identity
- `identity_statements`: user-authored "I am / I want to be" statements
- `open_questions`: unresolved questions Hunch should keep asking gently

## Promotion Rules
Claims start as `candidate`.

Promote to `active` only when:
- evidence appears in at least 2 records, or
- evidence appears across at least 2 source types, and
- confidence is at least `0.60`.

Set `stability`:
- `temporary`: one recent record or mood-like state
- `recurring`: repeated across records or sources
- `stable`: repeated across time and source types

## Confidence Rules
Initial confidence:
- `0.45` for one weak cue
- `0.55` for one explicit statement
- `0.65` for two supporting records
- `0.75` for two source types
- `0.85` for repeated evidence across time and source types

Contradiction handling:
- Do not delete claims immediately.
- If opposite evidence appears, lower confidence and mark `under_review`.
- Keep both the claim and the contradiction evidence visible in the changelog.

## Safety Rules
- Photo or video-derived claims need user-provided text or transcript.
- Sensitive identity claims should remain `candidate` until user confirmation.
- Temporary emotions should not be promoted into stable traits.
- Answers should say "your recent records suggest..." rather than "you are..."

## Eval Criteria
Self model update quality is evaluated separately from answer quality.

Five axes:
- `evidence_grounding`: every claim has concrete evidence ids
- `field_coverage`: claims appear in relevant self model fields
- `source_coverage`: multiple source types are represented when available
- `promotion_safety`: temporary states are not over-promoted
- `actionability_for_future_answers`: claims are useful for future personalization

