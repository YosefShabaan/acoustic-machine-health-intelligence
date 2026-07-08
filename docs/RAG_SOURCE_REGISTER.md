# AMHI RAG Source Register

Corpus version: `AMHI-FAN-MAINT-KB-v1`

Created: 2026-07-09

Purpose: record the public source provenance for the bounded Fan maintenance
knowledge base used by AMHI retrieval. This register approves sources for
retrieval evidence only. It does not validate production maintenance decisions,
physical root cause, Remaining Useful Life, or multi-machine generalization.

## Selection Policy

- Use authoritative public sources from DOE, DOE-associated publication records,
  national laboratories, or similarly primary maintenance authorities.
- Reject random blogs, SEO pages, forum posts, AI-generated pages, anonymous
  advice, and third-party mirrors when an official source is available.
- Do not treat research papers as maintenance manuals.
- Do not commit original large PDFs or generated scientific artifacts to Git.
- Store original public PDFs externally when file size or document policy makes
  repository tracking unsuitable.
- Keep repository RAG text small, source-preserving, and inspection-oriented.

## Approved Source: DOE Fan Sourcebook

### SOURCE ID

`doe_fan_sourcebook_2003`

### TITLE

Improving Fan System Performance: A Sourcebook for Industry

### PUBLISHER

U.S. Department of Energy, Energy Efficiency and Renewable Energy, Industrial
Technologies Program. Developed with AMCA International; prepared by Lawrence
Berkeley National Laboratory and Resource Dynamics Corporation.

### VERSION / DATE

Program document dated 2003-04-01 in the OSTI record.

### OFFICIAL SOURCE

- DOE PDF: https://www.energy.gov/sites/prod/files/2014/05/f16/fan_sourcebook.pdf
- OSTI record: https://www.osti.gov/biblio/1215862

### DOCUMENT TYPE

DOE industrial fan system sourcebook.

### FAN-RELEVANT SECTIONS

- Quick Start Guide and system approach.
- Section 2 fact sheet 3, Basic Maintenance.
- Section 2 fact sheet 4, Common Fan Systems Problems.
- Section 2 fact sheet 5, Indications of Oversized Fans.

### WHY APPROVED OR REJECTED

Approved. The document is a DOE fan-system sourcebook and the OSTI record
identifies it as a reference for industrial fan system users. The DOE PDF
contains explicit fan maintenance and inspection guidance, including basic
maintenance, vibration monitoring, records, belt-drive issues, and noise or
vibration indications.

### RAG ROLE

Primary fan-specific maintenance and inspection source for abnormal acoustic
noise, vibration, belt-drive, fan cleaning, records, and system-performance
context.

### LIMITATIONS

The sourcebook is system-performance guidance, not an AMHI-specific diagnostic
protocol. It can support cautious inspection-oriented recommendations only when
retrieved and cited. It does not enable component-fault confirmation, RUL, or
fault probability claims.

### LOCAL / EXTERNAL PATHS

- Tracked RAG text: `data/manuals/doe_fan_sourcebook_2003_fan_maintenance.md`
- External original PDF:
  `D:\PDM_Data\MIMII\manuals\sources\doe_fan_sourcebook_2003.pdf`

## Approved Source: DOE/FEMP O&M Best Practices

### SOURCE ID

`doe_om_best_practices_release_3_fans`

### TITLE

Operations & Maintenance Best Practices - A Guide to Achieving Operational
Efficiency Release 3.0

### PUBLISHER

U.S. Department of Energy Federal Energy Management Program, with Pacific
Northwest National Laboratory participation documented in the guide.

### VERSION / DATE

Release 3.0. OSTI record date: 2010-08.

### OFFICIAL SOURCE

- DOE PDF:
  https://www.energy.gov/sites/prod/files/2020/04/f74/omguide_complete_w-eo-disclaimer.pdf
- OSTI record: https://www.osti.gov/biblio/1220381
- PNNL project page: https://www.pnnl.gov/projects/om-best-practices

### DOCUMENT TYPE

DOE/FEMP operations and maintenance best-practices guide.

### FAN-RELEVANT SECTIONS

- Chapter 5, maintenance program types.
- Chapter 6, predictive maintenance technologies.
- Chapter 9.7, air handling system checklist.
- Chapter 9.8, fans, including the fans checklist.

### WHY APPROVED OR REJECTED

Approved. The guide is an official DOE/FEMP O&M guide and the OSTI record
identifies Release 3.0. The selected sections include air-handling/fan
inspection checklists and predictive maintenance context relevant to fan
maintenance communication.

### RAG ROLE

Secondary O&M checklist and maintenance-program source for visual inspection,
belts, pulleys, dampers, fan blades, filters, wiring, ductwork, vibration
monitoring context, and recordkeeping.

### LIMITATIONS

This is broad facility O&M guidance, not an AMHI validated maintenance protocol.
It can ground inspection context and checklist-style recommendations only. It
does not enable production readiness, root-cause confirmation, RUL, or
quantified fault confidence claims.

### LOCAL / EXTERNAL PATHS

- Tracked RAG text:
  `data/manuals/doe_om_best_practices_release_3_fans.md`
- External original PDF:
  `D:\PDM_Data\MIMII\manuals\sources\doe_om_best_practices_release_3_2010.pdf`

## Rejected / Not Ingested

Third-party mirrors and redistributions found during search were not ingested
because official DOE or OSTI sources were available. Blogs, forum posts, SEO
pages, and AI-generated maintenance text were not used.

## PAPER VERDICT

This task is maintenance-source provenance, not a paper reproduction task. The
approved sources are public DOE maintenance and fan-system documents. They are
sufficient to create a small, source-preserving Fan RAG corpus, but not
sufficient to claim production validation or physical fault diagnosis.

## EXACT METHOD

Use the two official public sources above as approved retrieval evidence. Store
large PDFs externally, track only small curated maintenance notes, and index only
documents explicitly listed in `data/manuals/approved_sources.json` with
`approved: true`.

## REPRODUCIBLE

- Source URLs are recorded.
- OSTI records are recorded.
- External PDF paths are recorded.
- Tracked RAG text paths are recorded.
- Corpus version is fixed as `AMHI-FAN-MAINT-KB-v1`.

## MISSING

- No source-specific extraction/chunking evaluation yet.
- No lexical vs semantic retrieval evaluation yet.
- No Gemini maintenance-action validation against this corpus yet.

## PROJECT GAP

TASK-RAG-01 supplies approved public source material. Later tasks must review
chunking, add semantic retrieval, evaluate retrieval quality, and upgrade the
maintenance agent before claiming a real evaluated RAG path.

## ADAPTATION

The repository stores concise, source-preserving markdown notes derived from the
official documents instead of committing entire PDFs. This is a project choice
for inspectability, file size, and copyright discipline.

## EVALUATION LIMIT

Successful retrieval from this corpus will show source-grounded communication
mechanics only. It will not prove maintenance correctness, root cause, or
production readiness.

## IMPLEMENTATION PLAN

1. Add tracked markdown source notes under `data/manuals`.
2. Add `data/manuals/approved_sources.json` with corpus/source provenance.
3. Load the manifest with the existing knowledge base.
4. Run a small retrieval smoke and inspect returned source IDs/snippets.

## STOP

Stop TASK-RAG-01 after provenance, manifest, local corpus files, tests, and one
bounded retrieval smoke are complete.
