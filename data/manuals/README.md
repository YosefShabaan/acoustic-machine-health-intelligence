# Approved Maintenance Manuals

This folder is intentionally empty until Yosef adds approved maintenance
documents. The retriever indexes only documents listed in
`approved_sources.json` with `approved: true`; loose files in this directory are
ignored.

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
