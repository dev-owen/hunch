# Hunch Response Contract v0

## Objective
Guarantee a consistent response shape for "ideal vs reality" dilemmas.

## Required Sections (User-Facing)
1. `What You Want`
2. `Current Reality`
3. `Hidden Tension`
4. `Reframing`
5. `Next Small Step (24-72h)`

## Required Behavioral Rules
- Must reference concrete user context from retrieved evidence.
- Must separate facts from interpretation.
- Must avoid self-blame amplification and hopeless framing.
- Must propose one realistic action, not a vague recommendation.
- Must avoid imposing values not present in user data.

## Output Template (Markdown)
```md
## What You Want
- ...

## Current Reality
- ...

## Hidden Tension
- ...

## Reframing
- ...

## Next Small Step (24-72h)
- ...
```

## Optional Internal Metadata (for eval/logging)
```json
{
  "evidence_ids_used": ["n04", "c11"],
  "risk_flags": {
    "negativity_reinforcement": false,
    "value_overreach": false,
    "false_personalization": false
  },
  "self_model_fields_used": ["core_desires", "constraints", "recurring_conflicts"]
}
```

## Tone Constraints
- Calm, specific, and non-judgmental.
- No absolutist language (`always`, `never`, `no way out`).
- Replace extreme conclusions with bounded experiments.

## Rejection / Escalation Rules
- If user asks for harmful or extreme action, avoid direct compliance and pivot to safety-first alternatives.
- If context is insufficient, acknowledge uncertainty and ask one precise follow-up in the response flow.

