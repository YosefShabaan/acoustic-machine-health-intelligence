---
name: performance-forensics
description: Repository-specific runtime and bottleneck diagnosis for D:\IOT. Use for hangs, unexpectedly long commands, high CPU usage, slow indexing, slow preprocessing, memory growth, unclear runtime bottlenecks, or expensive scientific loops.
---

# Performance Forensics

## Workflow

1. Do not immediately rewrite code.
2. Identify the exact process and command. Stop only the relevant runaway process when requested or necessary.
3. Determine whether the run is frozen, I/O-bound, CPU-bound, memory-bound, or waiting on a child process.
4. Trace the exact call path for one representative sample.
5. Profile one representative sample with major stages separated.
6. Profile three representative samples.
7. Check scaling behavior and estimate larger-run runtime.
8. Inspect dependency/source APIs for repeated loading, model initialization, resampling, FFT/STFT work, or serialization.
9. Identify verified redundant computation.
10. Optimize only verified redundancy.
11. Benchmark before and after.
12. Run the full bounded job only if measured runtime is reasonable or approved.
13. Stop at the requested benchmark checkpoint.

## Required Timing Categories

Report applicable timings using these labels:

```text
AUDIO LOAD:
PREPROCESSING:
EMBEDDING:
METRIC/MODEL STAGES:
SERIALIZATION:
TOTAL:
```

## Rules

- Do not guess the bottleneck from CPU usage alone.
- Do not replace scientific algorithms merely to make code faster.
- Do not silently reduce dataset size.
- Do not change output semantics during optimization.
- Prefer cache, reuse, batching, and moving initialization outside loops only when scientifically equivalent.
- Add progress and ETA for long loops.
- Stop pathological runs early after measured evidence.
- For Expert B timbre work, do not replace AudioCommons metrics with librosa approximations.
- Preserve Expert A, SNR artifacts, and scientific output semantics.

## Required Final Output

Use this structure:

```text
PROCESS:
CALL GRAPH:
ROOT CAUSE:
ONE-SAMPLE:
THREE-SAMPLE:
SCALING:
CHANGE:
BEFORE:
AFTER:
ESTIMATED FULL RUNTIME:
SCIENTIFIC BEHAVIOR CHANGED:
STOP:
```
