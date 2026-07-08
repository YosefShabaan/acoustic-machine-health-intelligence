# Contributing

This repository is a bounded research and engineering project for acoustic machine health intelligence.

## Issue-First Workflow

Use a GitHub issue for meaningful work before opening a pull request. The issue should define the context, scope, dependencies, runtime gate, scientific guardrails, definition of done, expected artifacts, and claim impact.

Small typo fixes may skip the issue when they do not affect behavior, data, scientific claims, or documentation meaning.

## Branch Workflow

Create a short-lived branch from `main` for each issue. Keep changes focused on the linked issue. Avoid unrelated refactors, metadata churn, or generated artifacts.

Pull requests should use the repository template and include the actual commands run, inspected outputs, runtime gate result, and scientific review.

## Bounded Runtime Ladder

Data and model work must follow this ladder:

```text
unit test
-> one-sample smoke
-> three-sample timing
-> small bounded run
-> runtime estimate
-> full run only when justified and approved
```

Do not start full-data training, indexing, or evaluation without small-run timing evidence. Unexpected slow jobs should stop and be routed to performance forensics.

## External Artifact Policy

Do not commit raw datasets, WAV files, NumPy arrays, model weights, generated indexes, generated reports, or generated scientific artifacts.

Large and generated artifacts belong outside Git, currently under external paths such as:

```text
D:\PDM_Data\MIMII
```

Small documentation, manifests, and source code are acceptable when they do not embed large data or generated scientific outputs.

## Scientific Claim Policy

Keep claims tied to verified evidence. Separate paper facts, repository facts, project choices, and inferences.

Do not claim:

- Remaining Useful Life or exact time-to-failure prediction.
- Confirmed physical root cause.
- Expert B rank score as confidence, probability, or severity percentage.
- Production maintenance grounding without approved production documents and retrieval validation.
- Pump, Valve, Slide Rail, MIMII DG, or multi-machine generalization without bounded evaluation.
- Exact paper reproduction unless explicitly validated.

## Pull Request Review Expectations

Reviewers should check:

- The change matches the linked issue.
- Tests and smokes are appropriate for risk.
- Actual output was inspected.
- Runtime gates were followed.
- Artifact paths are safe.
- Scientific wording stays within supported claims.
- No large/generated scientific artifacts are committed.
