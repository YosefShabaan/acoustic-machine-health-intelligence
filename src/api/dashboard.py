"""API-backed technician dashboard routes."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from application import (
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PROCESSING,
    EVENT_STATUS_QUEUED,
    AnalysisResultRecord,
    AnalysisRunRecord,
    EventRecord,
)


dashboard_router = APIRouter()


@dashboard_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_index(
    request: Request,
    status: str | None = Query(default=None),
) -> HTMLResponse:
    """Render an event list from persisted application state."""
    deps = request.app.state.dependencies
    if status not in {
        None,
        EVENT_STATUS_QUEUED,
        EVENT_STATUS_PROCESSING,
        EVENT_STATUS_COMPLETED,
        EVENT_STATUS_FAILED,
    }:
        status = None
    events = deps.event_repository.list_events(limit=100, offset=0, status=status)
    return HTMLResponse(_layout("AMHI Fan Events", _event_table(events)))


@dashboard_router.get("/dashboard/events/{event_id}", response_class=HTMLResponse)
async def dashboard_event_detail(event_id: str, request: Request) -> HTMLResponse:
    """Render one event detail from persisted application state."""
    deps = request.app.state.dependencies
    event = deps.event_repository.get_event(event_id)
    if event is None:
        return HTMLResponse(
            _layout("Event Not Found", f"<section><h1>Event not found</h1><p>{_e(event_id)}</p></section>"),
            status_code=404,
        )
    run = deps.analysis_repository.get_latest_run_for_event(event_id)
    result = deps.analysis_repository.get_result(run.analysis_run_id) if run else None
    return HTMLResponse(_layout(f"Event {event.event_id}", _event_detail(event, run, result)))


def _layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(title)}</title>
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f3f6f8; color: #17202a; }}
    header {{ background: #142433; color: white; padding: 18px 24px; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 20px; }}
    section {{ background: white; border: 1px solid #d8e0e8; border-radius: 6px; padding: 16px; margin-bottom: 14px; }}
    h1, h2, h3 {{ margin: 0 0 10px; letter-spacing: 0; }}
    h1 {{ font-size: 24px; }}
    h2 {{ font-size: 18px; }}
    h3 {{ font-size: 15px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #d8e0e8; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ color: #526170; font-size: 12px; text-transform: uppercase; }}
    a {{ color: #155e68; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }}
    .metric {{ background: #f7f9fb; border: 1px solid #d8e0e8; border-radius: 6px; padding: 10px; }}
    .label {{ color: #526170; font-size: 12px; text-transform: uppercase; }}
    .value {{ margin-top: 4px; overflow-wrap: anywhere; }}
    .flag {{ display: inline-block; border-radius: 4px; padding: 4px 8px; background: #e7f4f1; color: #155e68; margin: 4px 4px 4px 0; }}
    .warning {{ background: #fff7df; color: #7a5200; }}
    .failed {{ background: #fdecec; color: #8a1f17; }}
    code {{ background: #f7f9fb; border: 1px solid #d8e0e8; border-radius: 4px; padding: 2px 4px; }}
  </style>
</head>
<body>
  <header><h1>{_e(title)}</h1><div>Fan id_00 bounded application state</div></header>
  <main>{body}</main>
</body>
</html>"""


def _event_table(events: list[EventRecord]) -> str:
    rows = []
    for event in events:
        rows.append(
            "<tr>"
            f'<td><a href="/dashboard/events/{_e(event.event_id)}">{_e(event.event_id)}</a></td>'
            f"<td>{_e(event.machine_type)}/{_e(event.machine_id)}</td>"
            f"<td>{_e(event.snr_tag)}</td>"
            f"<td>{_status_flag(event.status)}</td>"
            f"<td>{_e(_audio_label(event.audio_reference))}</td>"
            f"<td>{_e(event.created_at)}</td>"
            "</tr>",
        )
    if not rows:
        rows.append('<tr><td colspan="6">No events available.</td></tr>')
    return (
        "<section><h2>Event List</h2>"
        "<table><thead><tr><th>Event</th><th>Machine</th><th>SNR</th><th>Status</th>"
        "<th>Audio</th><th>Created</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _event_detail(
    event: EventRecord,
    run: AnalysisRunRecord | None,
    result: AnalysisResultRecord | None,
) -> str:
    body = [
        "<section><h2>Event</h2><div class=\"grid\">",
        _metric("Event ID", event.event_id),
        _metric("Machine", f"{event.machine_type}/{event.machine_id}"),
        _metric("SNR", event.snr_tag),
        _metric("Status", event.status),
        _metric("Audio", _audio_label(event.audio_reference)),
        _metric("Created", event.created_at),
        "</div>",
        "<span class=\"flag warning\">Fan-only scope; not production maintenance validation.</span>",
        "</section>",
    ]
    if event.error_code:
        body.append(
            "<section><h2>Failure</h2>"
            f"<p><code>{_e(event.error_code)}</code> {_e(event.error_summary or '')}</p></section>",
        )
    body.append(_run_section(run))
    if result is None:
        body.append("<section><h2>Analysis Result</h2><p>No analysis result available yet.</p></section>")
    else:
        body.extend(
            [
                _expert_a_section(result.expert_a_result),
                _expert_b_section(result.expert_b_evidence),
                _context_section(result.structured_context),
                _retrieval_section(result.retrieval_metadata),
                _explanation_section(result.explanation_output),
                _maintenance_section(result.maintenance_output),
                _timing_section(result.timing_metadata),
                _limits_section(),
            ],
        )
    return "".join(body)


def _run_section(run: AnalysisRunRecord | None) -> str:
    if run is None:
        return "<section><h2>Analysis Run</h2><p>No worker has claimed this event.</p></section>"
    return (
        "<section><h2>Analysis Run</h2><div class=\"grid\">"
        + _metric("Run ID", run.analysis_run_id)
        + _metric("Pipeline Version", run.pipeline_version)
        + _metric("Status", run.status)
        + _metric("Started", run.started_at)
        + _metric("Completed", run.completed_at or "not completed")
        + _metric("Total Duration", run.total_duration if run.total_duration is not None else "not recorded")
        + "</div>"
        + _artifact_flags(run.artifact_metadata)
        + "</section>"
    )


def _expert_a_section(expert_a: dict[str, Any]) -> str:
    return (
        "<section><h2>Expert A</h2><div class=\"grid\">"
        + _metric("Anomaly Score", expert_a.get("anomaly_score", "not recorded"))
        + _metric("Threshold", expert_a.get("threshold", "not recorded"))
        + _metric("Decision", expert_a.get("is_anomaly", "not recorded"))
        + "</div></section>"
    )


def _expert_b_section(expert_b: dict[str, Any] | None) -> str:
    if not expert_b:
        return "<section><h2>Expert B</h2><p>No Expert B evidence available.</p></section>"
    rows = []
    for key in ("k", "distance", "rank_threshold", "directions"):
        if key in expert_b:
            rows.append(_metric(key, expert_b.get(key)))
    if expert_b.get("skipped"):
        rows.append(_metric("Skipped", expert_b.get("reason", "not recorded")))
    return (
        "<section><h2>Expert B</h2><div class=\"grid\">"
        + "".join(rows)
        + "</div><span class=\"flag warning\">Qualitative rank evidence, not confidence or probability.</span></section>"
    )


def _context_section(context: dict[str, Any] | None) -> str:
    if not context:
        return "<section><h2>Structured Health Context</h2><p>No context available.</p></section>"
    return (
        "<section><h2>Structured Health Context</h2>"
        + _metric("Schema Version", context.get("schema_version", "not recorded"))
        + "</section>"
    )


def _retrieval_section(retrieval: dict[str, Any] | None) -> str:
    if not retrieval:
        return "<section><h2>RAG Retrieval</h2><p>No retrieval metadata available.</p></section>"
    source_rows = []
    for source in retrieval.get("sources", []) or []:
        source_rows.append(
            "<li>"
            f"{_e(source.get('title', 'source'))} "
            f"<code>{_e(source.get('source_id', ''))}</code> "
            f"<code>{_e(source.get('chunk_id', ''))}</code>"
            "</li>",
        )
    return (
        "<section><h2>RAG Retrieval</h2><div class=\"grid\">"
        + _metric("Retriever", retrieval.get("retriever_type", "not recorded"))
        + _metric("Corpus", retrieval.get("corpus_version", "not recorded"))
        + _metric("Query", retrieval.get("query", retrieval.get("retrieval_query", "not recorded")))
        + "</div><h3>Sources</h3><ul>"
        + ("".join(source_rows) if source_rows else "<li>No retrieved source rows available.</li>")
        + "</ul></section>"
    )


def _explanation_section(explanation: dict[str, Any] | None) -> str:
    if not explanation:
        return "<section><h2>Explanation</h2><p>No explanation output available.</p></section>"
    metadata = explanation.get("metadata", {})
    return (
        "<section><h2>Explanation</h2>"
        + _fallback_flag(metadata.get("fallback_used"))
        + f"<p>{_e(explanation.get('summary', 'No summary recorded.'))}</p>"
        + "</section>"
    )


def _maintenance_section(maintenance: dict[str, Any] | None) -> str:
    if not maintenance:
        return "<section><h2>Maintenance</h2><p>No maintenance output available.</p></section>"
    metadata = maintenance.get("metadata", {})
    recommendation = maintenance.get("recommendation", maintenance)
    actions = recommendation.get("recommended_next_actions", []) or maintenance.get(
        "recommended_next_actions",
        [],
    )
    rendered_actions = []
    for action in actions:
        rendered_actions.append(
            "<li>"
            f"{_e(action.get('action', 'action'))} "
            f"<code>{_e(action.get('source_id', ''))}</code> "
            f"<code>{_e(action.get('chunk_id', ''))}</code>"
            "</li>",
        )
    return (
        "<section><h2>Maintenance</h2>"
        + _fallback_flag(metadata.get("fallback_used"))
        + f"<p>{_e(recommendation.get('text', maintenance.get('text', 'No recommendation text recorded.')))}</p>"
        + "<h3>Actions And Citations</h3><ul>"
        + ("".join(rendered_actions) if rendered_actions else "<li>No cited maintenance actions available.</li>")
        + "</ul></section>"
    )


def _timing_section(timings: dict[str, Any]) -> str:
    if not timings:
        return "<section><h2>Stage Timings</h2><p>No timing metadata available.</p></section>"
    return (
        "<section><h2>Stage Timings</h2><div class=\"grid\">"
        + "".join(_metric(key, value) for key, value in timings.items())
        + "</div></section>"
    )


def _limits_section() -> str:
    return (
        "<section><h2>Scientific Limits</h2>"
        "<span class=\"flag warning\">No RUL</span>"
        "<span class=\"flag warning\">No confirmed root cause</span>"
        "<span class=\"flag warning\">No confidence percentage</span>"
        "<span class=\"flag warning\">No multi-machine generalization</span>"
        "</section>"
    )


def _artifact_flags(metadata: dict[str, Any]) -> str:
    if not metadata:
        return ""
    keys = ("k", "distance", "rank_threshold", "rag_retriever_type", "rag_corpus_version")
    return "<div class=\"grid\">" + "".join(
        _metric(key, metadata[key]) for key in keys if key in metadata
    ) + "</div>"


def _metric(label: str, value: Any) -> str:
    return (
        '<div class="metric">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e(value)}</div>'
        "</div>"
    )


def _status_flag(status: str) -> str:
    css = "failed" if status == EVENT_STATUS_FAILED else "warning" if status == EVENT_STATUS_PROCESSING else ""
    return f'<span class="flag {css}">{_e(status)}</span>'


def _fallback_flag(value: Any) -> str:
    if value is True:
        return '<span class="flag warning">Fallback used</span>'
    if value is False:
        return '<span class="flag">Fallback not used</span>'
    return '<span class="flag warning">Fallback state not recorded</span>'


def _audio_label(audio_reference: str) -> str:
    if "://" in audio_reference:
        return audio_reference.rstrip("/").split("/")[-1]
    return Path(audio_reference).name


def _e(value: Any) -> str:
    return escape(str(value), quote=True)
