# Local Artifact Reconciliation

Task: `TASK-00B`

Date: 2026-07-07

Scope: metadata, file counts, file sizes, and hashes only. No audio feature
processing, model training, Expert B indexing, or dataset mutation was run.

## Summary

Repo-local large data/model artifacts were reconciled against the active
external artifact root:

```text
D:\PDM_Data\MIMII
```

After reconciliation, `D:\IOT` contains source, scripts, tests, documentation,
repo-local skills, and small placeholders only. Active large MIMII WAV files,
generated arrays/stat files, and trained model weights are outside the
repository.

## Artifact Groups

### GROUP: MIMII Fan id_00 Raw WAV Mirror

REPO PATH: `D:\IOT\data\raw\mimii\fan\id_00`

EXTERNAL PATH: `D:\PDM_Data\MIMII\fan_minus6dB\id_00`

FILE COUNT: `1418` WAV files

SIZE: `3,630,193,440` bytes

CLASSIFICATION: `VERIFIED_DUPLICATE_EXTERNAL`

EVIDENCE:

- Repo and external WAV counts both equal `1418`.
- Full relative-path size comparison found `0` missing files and `0` size mismatches.
- Representative SHA256 samples matched for:
  - `normal\00000000.wav`
  - `normal\00000505.wav`
  - `normal\00001010.wav`
  - `abnormal\00000000.wav`
  - `abnormal\00000203.wav`
  - `abnormal\00000406.wav`
- The same representative samples differed from `0dB` and `plus6dB`, confirming
  the repo-local mirror matched the external `minus6dB` dataset.

ACTION:

- Removed the repo-local duplicate copy.
- Preserved the external `minus6dB`, `0dB`, and `plus6dB` raw directories.

### GROUP: Expert A Legacy Unsuffixed Processed Arrays

REPO PATH: `D:\IOT\data\processed`

EXTERNAL PATH: `D:\PDM_Data\MIMII\processed`

FILE COUNT: `4` generated artifact files plus local placeholder

SIZE: `36,060,996` bytes for generated artifacts

CLASSIFICATION: `VERIFIED_DUPLICATE_EXTERNAL`

EVIDENCE:

| Repo File | External File | SHA256 |
|---|---|---|
| `ad_norm_stats.npz` | `ad_norm_stats_minus6dB.npz` | `C6897FE3EED11140F880761256EDC033FC1F0B8A1BC70696C8BAC7BD70207755` |
| `X_test_ad.npy` | `X_test_ad_minus6dB.npy` | `C50DAA904568609BD6EF197ABF34835CEA0EB0CE9E4568EE1CE4771434BC41A9` |
| `X_train_ad.npy` | `X_train_ad_minus6dB.npy` | `0727560123B9C46716E2F7FCBCBABE9B2FEC20EAB59EC16058350C148C63E8DB` |
| `y_test_ad.npy` | `y_test_ad_minus6dB.npy` | `523FC16FEDCFF31C90D08AAC88F463D614E01FD9450C82354FE9797E8D152F11` |

ACTION:

- Removed the repo-local duplicate generated arrays/stat file.
- Removed the now-unneeded local `data` placeholder tree.
- Preserved all external per-SNR processed artifacts.

### GROUP: Legacy Unsuffixed Expert A Model

REPO PATH: `D:\IOT\models_store\anomaly_detector.pt`

EXTERNAL PATH:
`D:\PDM_Data\MIMII\models_store\anomaly_detector_legacy_repo_2026-06-29.pt`

FILE COUNT: `1`

SIZE: `13,108,435` bytes

CLASSIFICATION: `UNIQUE_LOCAL_ARTIFACT`

EVIDENCE:

- The file did not match the current external per-SNR model weights by size/hash.
- Active source paths resolve model artifacts under `D:\PDM_Data\MIMII\models_store`.
- Active source did not reference `D:\IOT\models_store\anomaly_detector.pt`.
- Destination did not exist before move.
- SHA256 preserved after move:
  `DF97162D1A3C18FABA6756A80DBE175EC5450C0543C1CB5D5B3DF67E4847A3D3`
- Last write time preserved: `2026-06-29 05:20:17`.

ACTION:

- Moved the unique legacy model to the external model store without overwrite.
- Removed the empty repo-local `models_store` directory.
- Did not update active runtime paths.

## Stale Legacy Artifacts

Only empty repository-local data placeholders were removed as part of removing
the duplicate `data` tree. No scientific result artifact was classified as stale
and deleted.

## Unknown Artifacts

No repo-local large data/model artifact group remained `UNKNOWN`.

## Final Repository Policy

`D:\IOT` must not contain active large MIMII WAV datasets, generated `.npy` or
`.npz` arrays, trained `.pt` weights, or generated Expert B reference indexes.
Those artifacts belong under `D:\PDM_Data\MIMII` or another explicitly approved
external artifact root.
