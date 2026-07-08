# Approved Maintenance Manuals

This folder contains the tracked, small AMHI Fan maintenance corpus notes for
`AMHI-FAN-MAINT-KB-v1`.

The retriever indexes only documents listed in `approved_sources.json` with
`approved: true`; loose files in this directory are ignored.

The original public PDFs are stored externally under:

```text
D:\PDM_Data\MIMII\manuals\sources
```

Do not commit full manuals when file size, copyright discipline, or source
format makes external storage more appropriate.

Minimal manifest shape:

```json
{
  "sources": [
    {
      "source_id": "fan_manual_v1",
      "title": "Fan Maintenance Manual",
      "version": "v1",
      "path": "fan_manual.md",
      "approved": true
    }
  ]
}
```

Use only local approved manuals, procedures, checklists, or troubleshooting
guides. Do not paste random web snippets into the production knowledge base.

The current approved corpus is public-source evidence for cautious Fan
inspection communication only. It does not validate production maintenance
recommendations, root-cause diagnosis, RUL, confidence, or probability claims.
