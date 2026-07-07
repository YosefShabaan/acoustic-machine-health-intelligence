# AGENTS.md

`CLAUDE.md` is the master project and scientific context. Read the relevant
sections of `CLAUDE.md` before project-level decisions, then prefer newer
verified project docs when they supersede older architecture notes.

Use the repository skills in `D:\IOT\.agents\skills` for complex work:

- Major architecture, research, pivot, new expert/model, new dataset, or ambiguous tasks: use `$project-architect`.
- Paper, dataset paper, research method, reproduction, or paper-based implementation tasks: use `$paper-forensics`.
- Approved bounded implementation tasks: use `$scientific-implementer`.
- Hangs, slow commands, high CPU, slow preprocessing/indexing, memory growth, or unclear runtime bottlenecks: use `$performance-forensics`.

Plan before coding for ambiguous tasks. Never launch expensive full-data
experiments without a small timing run. Never claim paper facts that were not
verified from primary or official sources. Separate paper fact, repository fact,
project choice, and inference.

Preserve Expert A and completed SNR artifacts unless explicitly authorized.
Fan `id_00` is the current reference MVP, but reusable interfaces must remain
machine-aware. The current active architecture is: same machine, same sound,
Expert A detects, Expert B characterizes. RUL and PRONOSTIA are not part of the
active runtime architecture.

Review the actual diff and test output before declaring any task complete.

## Project Execution Workflow

Use the two-stage project workflow.

`plan project` means:

1. Act as `$project-architect`.
2. Read `CLAUDE.md`, `docs/MASTER_PROJECT_ROADMAP.md`, `project_state.json`, and current repository state.
3. Create or revise `docs/MASTER_EXECUTION_PLAN.md`.
4. Show the complete ordered task list.
5. Set `project_state.json` execution mode to `awaiting_approval`.
6. Stop and wait for Yosef to say `start implementation`.

`start implementation` means:

1. Read `docs/MASTER_EXECUTION_PLAN.md` and `project_state.json`.
2. Find the first approved incomplete task whose dependencies are satisfied.
3. Load the task's primary skill.
4. Implement the task, run its tests/smokes/runtime gates, inspect actual outputs, review the diff, perform scientific review, update `docs/TASK_EXECUTION_LOG.md`, and update `project_state.json`.
5. Continue automatically to the next approved task.
6. Stop only for a real blocker, a failed bounded diagnosis, required data/credentials, required architecture change, or completion of the approved task plan.

`continue project` means:

- If `execution_mode` is `awaiting_approval`, show the plan summary and ask Yosef to say `start implementation`.
- If `execution_mode` is `implementing`, resume from the current or next task in `docs/MASTER_EXECUTION_PLAN.md`.
- If `execution_mode` is `blocked`, report the exact blocker.
- If `execution_mode` is `complete`, report completion.
- If no valid execution plan exists, route to planning mode.

Skills support task execution; they are not the scheduler. The execution plan
controls task order. Do not skip scientific blockers, invent labels, thresholds,
equations, or paper facts, or silently change architecture. Unexpected
pathological runtime routes to `$performance-forensics`.
