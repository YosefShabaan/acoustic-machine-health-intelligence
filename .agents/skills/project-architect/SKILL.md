---
name: project-architect
description: Repository-specific architecture planning for D:\IOT. Use for major architecture decisions, project pivots, new experts or models, new datasets, ambiguous tasks, scientific risk review, and when Codex must plan before implementing in this predictive-maintenance project.
---

# Project Architect

## Workflow

1. Read the relevant sections of `CLAUDE.md`, then inspect current repository state and recent project docs such as `REPORT_PHASE1_2.md` and `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md` when relevant.
2. Identify the user's actual goal and whether the request is planning, review, implementation, or performance forensics.
3. Inspect relevant existing code and docs before deciding.
4. Challenge assumptions when the request conflicts with verified project facts, paper facts, available labels, available data, or completed experiments.
5. Identify scientific risks and engineering risks separately.
6. Classify statements explicitly as:
   - `PAPER FACT`
   - `VERIFIED REPOSITORY FACT`
   - `PROJECT DECISION`
   - `INFERENCE`
   - `UNKNOWN`
7. Produce the smallest coherent plan that preserves the active architecture.
8. Define a concrete stop condition.
9. Do not implement unless the user explicitly approves implementation.

## Project Guardrails

- Treat `CLAUDE.md` as master project and scientific context, but prefer newer verified docs when they supersede legacy architecture.
- Expert A is complete; preserve its architecture, training logic, and completed SNR artifacts unless explicitly authorized.
- Fan `id_00` is the current MVP/reference implementation, but reusable interfaces must remain machine-aware.
- Current active architecture: same machine, same sound, Expert A detects anomaly, Expert B characterizes acoustic difference.
- RUL and PRONOSTIA are not part of the active runtime architecture.
- Do not invent dataset capabilities, labels, thresholds, or paper details.
- Do not claim exact paper reproduction without primary/official proof.
- Prefer one coherent same-system architecture over parallel inconsistent branches.
- Avoid unrelated refactors and preserve verified experiments.

## Required Output

Use this structure:

```text
STATE:
FACTS:
GAPS:
DECISION:
PLAN:
STOP CONDITION:
NEXT:
```

Keep commentary concise. Make technical specs detailed enough for a later bounded implementation task.
