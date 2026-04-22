# Hunch Eval Rubric v0

## Scoring Scale
Each axis is scored from 1 to 5.

- `1`: poor / harmful / missing
- `2`: weak and mostly generic
- `3`: acceptable baseline
- `4`: strong and clearly useful
- `5`: excellent and consistently personalized

## Axes

### 1) Understanding
Measures whether the response reflects real user context.
- 1: ignores user history
- 3: references at least one relevant context item
- 5: uses multiple accurate context signals with no invented claims

### 2) Structuring Quality
Measures whether ideal, reality, emotion/tension, and options are clearly separated.
- 1: unstructured advice blob
- 3: most sections present but mixed
- 5: all sections present, distinct, and coherent

### 3) Pattern Use
Measures whether repeated patterns are recognized and used correctly.
- 1: no pattern use
- 3: mentions pattern with weak grounding
- 5: correctly links repeated pattern to current dilemma with evidence

### 4) Healthiness
Measures whether the response avoids harmful framing.
- 1: reinforces blame, hopelessness, or extremes
- 3: neutral and non-harmful
- 5: actively reduces self-blame and promotes grounded hope

### 5) Actionability
Measures whether user can act immediately with realistic effort.
- 1: no action
- 3: action exists but vague or too large
- 5: one concrete, small, time-bounded next step

## Pass Criteria (v0)
- No axis below 3
- Average score >= 3.8
- Healthiness must be >= 4 for release candidates

## Mandatory Failure Tags
Every low-scoring response must include one or more tags:
- `generic_answer`
- `false_personalization`
- `negativity_reinforcement`
- `value_overreach`
- `memory_confusion`
- `action_vacuum`

