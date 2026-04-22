# Hunch v0 Use Case

## Core Product Question
Can Hunch use a user's notes and conversation history to produce a response that:
1. shows real understanding of that user, and
2. guides them to a healthier, realistic next choice?

## Narrow Scope (v0)
Hunch v0 focuses on one job:
"Structure an ideal-vs-reality dilemma using a small set of user notes and chat history."

## Inputs
- 10 to 20 user notes/journal entries
- 5 to 10 recent conversation snippets
- 1 user question about an ongoing dilemma

## Output Contract
One structured response that includes:
- what the user wants (ideal)
- what current reality looks like (constraints)
- hidden emotional tension and repeated pattern
- a healthier reframing
- one small actionable next step

## Success Criteria (v0)
- The response is personalized with explicit evidence.
- The structure is complete and readable.
- The tone avoids reinforcing self-blame or hopelessness.
- The response leads to an actionable next step.

## Out of Scope (v0)
- Full mobile app and production UI
- External social platform ingestion
- High-stakes life decisions with definitive advice
- Deep clinical interpretation or diagnosis

## Known Failure Types To Catch Early
- `generic_answer`: could apply to anyone
- `false_personalization`: makes unsupported claims about the user
- `negativity_reinforcement`: amplifies self-blame, despair, or extremes
- `value_overreach`: imposes values the user did not express
- `memory_confusion`: treats temporary mood as long-term trait
- `action_vacuum`: gives reflection without a concrete next step

## First Build Target
Build product + eval together:
1. small end-to-end response pipeline
2. repeatable eval harness that scores response quality on every run

