---
name: paper-forensics
description: Repository-specific paper and dataset method inspection for D:\IOT. Use when a paper, dataset paper, research method, paper-based implementation, reproduction claim, metric, annotation scheme, or public research asset is involved.
---

# Paper Forensics

## Workflow

1. Identify the primary paper and the exact claim or implementation question.
2. Prefer primary and official sources: paper PDF, official dataset docs, author repositories, official code, official pretrained assets, and cited method implementations.
3. Extract the exact method:
   - task
   - input
   - output
   - dataset
   - labels
   - preprocessing
   - architecture
   - equations
   - training
   - inference
   - evaluation
   - public code/assets
   - limitations
4. Inspect exact details instead of substituting generic methods.
5. Compare paper requirements with the current repository, data, artifacts, and active architecture.
6. Separate findings into:
   - directly reproducible
   - adaptation required
   - missing details
   - missing data
   - missing labels
7. Design the minimum scientifically defensible adaptation for this repository.
8. Draft one bounded implementation task with files, functions, dependencies, tests, smoke tests, and guardrails.
9. Stop before implementation unless the user explicitly approves implementation.

## Guardrails

- Never replace a paper metric with a similarly named generic feature without disclosure.
- Never guess an equation, threshold, label definition, preprocessing step, or architecture detail.
- Never turn an undocumented project implementation choice into a paper claim.
- Mark project-specific settings explicitly.
- State whether available data are sufficient for quantitative scientific claims.
- Do not use paper-result metrics as our project-result metrics.
- Do not claim exact reproduction unless primary/official sources support every required detail.
- For Expert B, keep `k=30` as the paper experimental setting and state that Nishida et al. reported similar results around `k=10-40`.
- For current Expert B, remember: current fan data are only integration/qualitative data because five-attribute ground-truth labels are unavailable.

## Required Output

Use this structure:

```text
PAPER VERDICT:
EXACT METHOD:
REPRODUCIBLE:
MISSING:
PROJECT GAP:
ADAPTATION:
EVALUATION LIMIT:
IMPLEMENTATION PLAN:
STOP:
```
