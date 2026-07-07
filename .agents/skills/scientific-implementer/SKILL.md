---
name: scientific-implementer
description: Repository-specific implementation workflow for approved scientific specs in D:\IOT. Use only after architecture or paper-forensics planning has been approved and the user asks Codex to implement a bounded change, tests, or smoke run.
---

# Scientific Implementer

## Workflow

1. Read the approved specification and the relevant project context.
2. Inspect every affected file before editing.
3. Restate scope internally and create a bounded file impact list.
4. Implement the smallest change satisfying the approved specification.
5. Avoid unrelated refactors.
6. Add tests for scientific guardrails and engineering behavior.
7. Run cheap unit tests first.
8. Run a tiny smoke test before expensive jobs.
9. Inspect actual outputs, not just command exit codes.
10. Review the diff.
11. Compare implementation against the approved specification.
12. Stop at the defined checkpoint.

## Execution Ladder

Use this order unless the user explicitly narrows it further:

```text
UNIT TEST
-> 1-SAMPLE SMOKE
-> 3-SAMPLE SMOKE
-> SMALL BOUNDED RUN
-> FULL RUN ONLY WHEN RUNTIME IS ESTIMATED AND APPROVED
```

## Rules

- Never launch an expensive full-data command before timing a tiny representative sample.
- After at least 3 representative samples, estimate runtime for the requested full job.
- If estimated runtime is unexpectedly large, stop and report.
- Add visible progress for long loops.
- Preserve existing verified artifacts.
- Do not overwrite machine/SNR-specific artifacts.
- Do not change Expert A architecture or training logic unless the approved task explicitly says so.
- Do not change SNR experiment behavior unless explicitly approved.
- Do not remove or refactor legacy RUL/PRONOSTIA files unless explicitly approved.
- Report actual results, warnings, failures, and skipped checks.
- Review git diff before declaring completion.

## Required Final Output

Use this structure:

```text
CHANGED:
TESTS:
SMOKE:
ACTUAL OUTPUT:
DIFF REVIEW:
ADAPTATIONS:
WARNINGS:
STOPPED AT:
NEXT:
```
