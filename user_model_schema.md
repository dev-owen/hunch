# Hunch User Model Schema v0

## Design Goal
Separate retrieval memory (raw records) from self memory (long-term user model).
This schema is for long-term self memory only.

## Canonical Shape
```json
{
  "user_id": "string",
  "snapshot_at": "ISO-8601 datetime",
  "core_desires": [],
  "constraints": [],
  "recurring_conflicts": [],
  "emotional_patterns": [],
  "values": [],
  "growth_signals": [],
  "temporary_state": []
}
```

## Field Specs

### `core_desires`
- Purpose: stable wants and preferred future direction
- Item shape:
```json
{
  "label": "Build a stable creative career",
  "evidence_ids": ["n12", "c07"],
  "confidence": 0.78,
  "first_seen": "2026-04-02",
  "last_seen": "2026-04-16"
}
```

### `constraints`
- Purpose: realistic limits (time, money, family, health, role obligations)
- Item shape:
```json
{
  "label": "Needs predictable monthly income",
  "type": "financial",
  "evidence_ids": ["n03", "c04"],
  "confidence": 0.83
}
```

### `recurring_conflicts`
- Purpose: repeated tension between two poles
- Item shape:
```json
{
  "side_a": "creative autonomy",
  "side_b": "financial stability",
  "trigger_context": "job-switch decisions",
  "evidence_ids": ["n03", "n12", "c05"],
  "confidence": 0.81
}
```

### `emotional_patterns`
- Purpose: recurring emotional cycles and triggers
- Item shape:
```json
{
  "trigger": "peer comparison after social media",
  "emotion": "anxiety",
  "default_behavior": "overplanning and avoidance",
  "evidence_ids": ["n08", "c09"],
  "confidence": 0.73
}
```

### `values`
- Purpose: user-declared decision criteria
- Item shape:
```json
{
  "label": "integrity in relationships",
  "strength": 0.9,
  "evidence_ids": ["n02", "c10"],
  "confidence": 0.86
}
```

### `growth_signals`
- Purpose: positive directional change to reinforce
- Item shape:
```json
{
  "signal": "asks for small experiments instead of all-or-nothing decisions",
  "trend": "up",
  "evidence_ids": ["c12", "c14"],
  "confidence": 0.68
}
```

### `temporary_state`
- Purpose: short-lived states that should not be over-generalized
- Item shape:
```json
{
  "state": "sleep-deprived and pessimistic",
  "valid_until": "2026-04-23",
  "evidence_ids": ["n17"],
  "confidence": 0.64
}
```

## Update Rules (v0)
1. Promote a candidate to long-term memory only if:
- observed in at least 2 independent records
- separated by at least 7 days
- confidence >= 0.60
2. Keep potentially transient signals in `temporary_state`.
3. Decay confidence by 0.05 per 30 days with no supporting evidence.
4. If contradictory evidence appears, do not delete immediately:
- lower confidence first
- mark as `under_review` in pipeline state (implementation detail)
5. Never store unsupported personality claims.

## Guardrails
- Evidence-first: each claim must map to `evidence_ids`.
- No hard labels like "you are always X."
- Long-term traits must be stable across time, not mood snapshots.

