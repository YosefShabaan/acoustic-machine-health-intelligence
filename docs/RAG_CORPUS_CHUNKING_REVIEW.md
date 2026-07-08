# RAG Corpus Chunking Review

Task: `TASK-RAG-02`

Corpus version: `AMHI-FAN-MAINT-KB-v1`

Date: 2026-07-09

## Scope

Review and implement source-preserving chunking for the approved public Fan
maintenance corpus created in `TASK-RAG-01`.

This review covers the tracked markdown corpus notes under `data/manuals`.
Original public PDFs remain external under:

```text
D:\PDM_Data\MIMII\manuals\sources
```

## Source Formats

The selected corpus sources are small markdown notes derived from official DOE
documents. They use stable second-level headings:

```text
## DOE-FAN-2003-...
## DOE-OM-R3-...
```

These headings are intentional citation anchors. The chunker should preserve the
heading and body together instead of slicing on arbitrary character boundaries.

## Implemented Chunking Strategy

- Parse approved `.md` or `.txt` files listed in `approved_sources.json`.
- Use markdown `##` sections as primary chunks.
- Derive `section_id` from the first heading token when it is already a stable
  uppercase identifier.
- Preserve `section_heading` separately from `chunk_id`.
- Include the heading text inside each chunk so retrieval snippets keep section
  context.
- Split only oversized sections by paragraph, with the heading preserved in
  each split part.

Every chunk now preserves:

- `source_id`
- `title`
- `publisher`
- `version`
- `corpus_version`
- `chunk_id`
- `section_id`
- `section_heading`
- `text`
- `source_url`
- `path`

## Corpus Statistics

```text
source_count=2
chunk_count=15
min_chars=324
max_chars=491
mean_chars=402.2
```

By source:

```text
doe_fan_sourcebook_2003: chunks=8 min_chars=324 max_chars=491
doe_om_best_practices_release_3_fans: chunks=7 min_chars=335 max_chars=430
```

No section exceeded the configured chunk-size ceiling during this review, so no
section was split into multiple parts.

## Chunk Inventory

```text
doe_fan_sourcebook_2003#DOE-FAN-2003-SYSTEM-APPROACH
doe_fan_sourcebook_2003#DOE-FAN-2003-BASIC-MAINTENANCE
doe_fan_sourcebook_2003#DOE-FAN-2003-VIBRATION-MONITORING
doe_fan_sourcebook_2003#DOE-FAN-2003-RECORDS
doe_fan_sourcebook_2003#DOE-FAN-2003-COMMON-FAN-PROBLEMS
doe_fan_sourcebook_2003#DOE-FAN-2003-BELT-DRIVES
doe_fan_sourcebook_2003#DOE-FAN-2003-NOISE-VIBRATION-INDICATORS
doe_fan_sourcebook_2003#limits-for-amhi-use
doe_om_best_practices_release_3_fans#DOE-OM-R3-MAINTENANCE-PROGRAMS
doe_om_best_practices_release_3_fans#DOE-OM-R3-PREDICTIVE-MAINTENANCE
doe_om_best_practices_release_3_fans#DOE-OM-R3-AIR-HANDLING-CHECKLIST
doe_om_best_practices_release_3_fans#DOE-OM-R3-FAN-CHECKLIST-VISUAL
doe_om_best_practices_release_3_fans#DOE-OM-R3-FAN-CHECKLIST-MECHANICAL
doe_om_best_practices_release_3_fans#DOE-OM-R3-FAN-CHECKLIST-DUCT-ELECTRICAL
doe_om_best_practices_release_3_fans#limits-for-amhi-use
```

## Manual Inspection

Checked retrieval query:

```text
fan visual inspection belts pulley dampers fan blades wiring ductwork
```

Top retrieved chunks:

```text
1. doe_om_best_practices_release_3_fans#DOE-OM-R3-FAN-CHECKLIST-MECHANICAL
2. doe_om_best_practices_release_3_fans#DOE-OM-R3-FAN-CHECKLIST-VISUAL
3. doe_fan_sourcebook_2003#DOE-FAN-2003-COMMON-FAN-PROBLEMS
```

Inspection result:

- The mechanical checklist chunk keeps belts, pulley wheels, dampers, actuator
  linkage, fan blades, cleaning, and lubrication in one section.
- The visual checklist chunk remains separate and does not merge with unrelated
  duct/electrical checks.
- The common fan problems chunk preserves fan/motor assembly context and does
  not claim a confirmed component fault.

Checked retrieval query:

```text
fan abnormal acoustic noise vibration belt inspection records
```

Inspection result:

- The returned chunks preserve acoustic noise, vibration, belt-drive, and
  recordkeeping context with explicit source/section identity.
- Headings remain associated with body text.
- No maintenance procedure was split into misleading fragments.
- No duplicate chunk IDs were observed.

## Claim Guardrails

This chunking review enables better source traceability for retrieval. It does
not enable:

- root-cause diagnosis,
- RUL or time-to-failure prediction,
- confidence or probability claims,
- Expert B timbre-direction accuracy,
- production maintenance validation.

## Next

`TASK-RAG-03` should add a Gemini semantic retriever while retaining the lexical
retriever as the baseline. The semantic embedding artifact must be generated
outside Git.
