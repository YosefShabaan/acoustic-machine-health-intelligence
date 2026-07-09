"""Static dashboard renderer for upgraded Fan intelligence evidence."""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402


DEFAULT_INPUT = (
    cfg.PROCESSED_DIR
    / "real_intelligence_end_to_end_fan_id_00_minus6dB_task_fan_13.json"
)
DEFAULT_EVALUATION = (
    cfg.PROCESSED_DIR / "fan_system_evaluation_fan_id_00_minus6dB_task_fan_14.json"
)
DEFAULT_OUTPUT = (
    cfg.PROCESSED_DIR / "dashboard_real_intelligence_fan_id_00_minus6dB_task_dash_02.html"
)


def load_output(path: Path | str = DEFAULT_INPUT) -> dict[str, Any]:
    """Load one end-to-end output JSON artifact."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_dashboard_html(
    data: dict[str, Any],
    evaluation: dict[str, Any] | None = None,
) -> str:
    """Render the dashboard as a standalone HTML document."""
    context = data["structured_context"]
    technician = data["technician_output"]
    event = context["event"]
    expert_a = context["expert_a"]
    expert_b = context["expert_b"]
    recommendation = technician["recommendation"]
    analysis = context.get("analysis", {})
    llm = analysis.get("llm", {})
    rag = analysis.get("rag", {})
    maintenance = analysis.get("maintenance", {})
    source_note = _source_note(data)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fan Intelligence Evidence Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1c2430;
      --muted: #526170;
      --line: #d8dee8;
      --panel: #f7f9fb;
      --accent: #1f6f78;
      --warn: #8a5a00;
      --good: #146c43;
    }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #eef2f5;
    }}
    header {{
      background: #13212b;
      color: white;
      padding: 22px 28px;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 22px;
    }}
    h1, h2, h3 {{
      margin: 0;
      letter-spacing: 0;
    }}
    h1 {{
      font-size: 26px;
      line-height: 1.2;
    }}
    h2 {{
      font-size: 18px;
      margin-bottom: 12px;
    }}
    h3 {{
      font-size: 15px;
      margin-bottom: 8px;
    }}
    .subtle {{
      color: #c9d4df;
      margin-top: 6px;
      font-size: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 14px;
    }}
    section {{
      background: white;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 16px;
      margin-bottom: 14px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
    }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    .value {{
      font-size: 18px;
      margin-top: 4px;
      overflow-wrap: anywhere;
    }}
    .flag {{
      display: inline-block;
      border-radius: 4px;
      padding: 4px 8px;
      background: #e7f4f1;
      color: var(--accent);
      font-size: 13px;
      margin-top: 8px;
    }}
    .warning {{
      background: #fff7df;
      color: var(--warn);
      border-color: #efd38a;
    }}
    .rank-row {{
      display: grid;
      grid-template-columns: 120px 1fr 72px;
      gap: 10px;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--line);
    }}
    .rank-row:last-child {{
      border-bottom: 0;
    }}
    progress {{
      display: block;
      inline-size: auto;
      block-size: 12px;
      accent-color: var(--accent);
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
    }}
    li {{
      margin: 7px 0;
    }}
    .source {{
      border-left: 4px solid var(--accent);
      padding-left: 12px;
      margin: 10px 0;
    }}
    table {{
      border-collapse: collapse;
      margin-top: 8px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    code {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 2px 4px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Fan Intelligence Evidence Dashboard</h1>
    <div class="subtle">{_e(event["event_id"])} | {_e(event["machine_type"])} {_e(event["machine_id"])} | {_e(event["snr_tag"])}</div>
  </header>
  <main>
    <section>
      <h2>Event</h2>
      <div class="grid">
        {_metric("Task", data.get("task", "not recorded"))}
        {_metric("Asset", event["asset_id"])}
        {_metric("Audio", Path(event["audio_path"]).name)}
        {_metric("Context Schema", context.get("schema_version", "unknown"))}
        {_metric("Analysis Run", analysis.get("analysis_run_id", "not recorded"))}
        {_metric("Pipeline Version", analysis.get("pipeline_version", "not recorded"))}
        {_metric("Runtime Seconds", _fmt(data["timings"]["total_seconds"]))}
      </div>
      <span class="flag warning">{_e(source_note)}</span>
    </section>

    <section>
      <h2>Expert A</h2>
      <div class="grid">
        {_metric("Anomaly Score", _fmt(expert_a["anomaly_score"]))}
        {_metric("Threshold", _fmt(expert_a["threshold"]))}
        {_metric("Decision", "Anomaly detected" if expert_a["is_anomaly"] else "Normal")}
      </div>
    </section>

    <section>
      <h2>Expert B Timbre Ranks</h2>
      <div class="flag">Selected references: {_e(expert_b["references"]["selected_count"])} of {_e(expert_b["references"]["pool_size"])}</div>
      {_rank_rows(expert_b["timbre_rank_scores"])}
    </section>

    <section>
      <h2>LLM</h2>
      <div class="grid">
        {_metric("Provider", llm.get("provider", data["guarded_explanation"].get("metadata", {}).get("provider", "not recorded")))}
        {_metric("Model", llm.get("model", data["guarded_explanation"].get("metadata", {}).get("model", "not recorded")))}
        {_metric("Prompt Version", llm.get("prompt_version", "not recorded"))}
        {_metric("Generation Mode", llm.get("generation_mode", "not recorded"))}
        {_metric("Fallback Used", llm.get("fallback_used", "not recorded"))}
      </div>
      {_fallback_flag(llm.get("fallback_used"))}
    </section>

    <section>
      <h2>Explanation</h2>
      <p>{_e(technician["technician_explanation"]["summary"])}</p>
      <div class="grid">
        <div>
          <h3>Observations</h3>
          {_list(technician["technician_explanation"]["observations"])}
        </div>
        <div>
          <h3>Hypotheses</h3>
          {_list(technician["technician_explanation"]["hypotheses"])}
        </div>
      </div>
    </section>

    <section>
      <h2>RAG</h2>
      <div class="grid">
        {_metric("Retriever", rag.get("retriever_type", "not recorded"))}
        {_metric("Corpus", rag.get("corpus_version", "not recorded"))}
        {_metric("Retrieval Query", rag.get("retrieval_query", data.get("retrieval_query", "not recorded")))}
      </div>
      <h3>Retrieved Sources</h3>
      {_sources(technician["retrieved_maintenance_guidance"])}
    </section>

    <section>
      <h2>Maintenance Actions</h2>
      <div class="grid">
        {_metric("Provider", maintenance.get("provider", technician.get("metadata", {}).get("provider", "not recorded")))}
        {_metric("Model", maintenance.get("model", technician.get("metadata", {}).get("model", "not recorded")))}
        {_metric("Prompt Version", maintenance.get("prompt_version", technician.get("metadata", {}).get("prompt_version", "not recorded")))}
        {_metric("Generation Mode", maintenance.get("generation_mode", technician.get("metadata", {}).get("generation_mode", "not recorded")))}
        {_metric("Fallback Used", maintenance.get("fallback_used", technician.get("metadata", {}).get("fallback_used", "not recorded")))}
      </div>
      {_fallback_flag(maintenance.get("fallback_used", technician.get("metadata", {}).get("fallback_used")))}
      <div class="flag {'warning' if not recommendation['available'] else ''}">{'Source-grounded' if recommendation['available'] else 'Unavailable'}</div>
      <p>{_e(recommendation["text"])}</p>
      {_actions(recommendation.get("recommended_next_actions", []))}
    </section>

    <section>
      <h2>Pipeline Timings</h2>
      {_timings_table(data.get("timings", {}))}
    </section>

    {_evaluation_section(evaluation)}

    <section>
      <h2>Scientific Limits</h2>
      {_limit_rows(data)}
    </section>

    <section>
      <h2>Limitations</h2>
      {_list(technician["limitations"])}
    </section>
  </main>
</body>
</html>
"""


def write_dashboard(
    data: dict[str, Any],
    output_path: Path | str = DEFAULT_OUTPUT,
    evaluation: dict[str, Any] | None = None,
) -> Path:
    """Write a standalone HTML dashboard."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard_html(data, evaluation=evaluation), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--evaluation", type=Path, default=DEFAULT_EVALUATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    data = load_output(args.input)
    evaluation = load_output(args.evaluation) if args.evaluation and args.evaluation.is_file() else None
    output = write_dashboard(data, args.output, evaluation=evaluation)
    print(f"DASHBOARD_RENDER=OK")
    print(f"INPUT={args.input}")
    print(f"OUTPUT={output}")
    print(f"EVENT_ID={data['structured_context']['event']['event_id']}")
    print(f"RECOMMENDATION_AVAILABLE={data['technician_output']['recommendation']['available']}")
    if evaluation is not None:
        print(f"EVALUATION_EVENTS={evaluation['summary']['total_events']}")


def _metric(label: str, value: Any) -> str:
    return (
        '<div class="metric">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e(value)}</div>'
        "</div>"
    )


def _rank_rows(rows: dict[str, dict[str, Any]]) -> str:
    rendered = []
    for name, values in rows.items():
        score = float(values["rank_score"])
        rendered.append(
            '<div class="rank-row">'
            f"<div>{_e(name)}</div>"
            f'<progress value="{score:.6f}" max="1"></progress>'
            f"<div>{score:.3f}</div>"
            "</div>"
        )
    return "\n".join(rendered)


def _sources(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No approved source was retrieved.</p>"
    rendered = []
    for row in rows:
        rendered.append(
            '<div class="source">'
            f'<div><strong>{_e(row["title"])}</strong></div>'
            f'<div>Source: <code>{_e(row["source_id"])}</code></div>'
            f'<div>Chunk: <code>{_e(row["chunk_id"])}</code></div>'
            f'<div>Version: {_e(row["version"])}</div>'
            f"<p>{_e(row['snippet'])}</p>"
            "</div>"
        )
    return "\n".join(rendered)


def _actions(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p>No maintenance actions are available.</p>"
    rendered = []
    for row in rows:
        rendered.append(
            '<div class="source">'
            f'<div><strong>{_e(row["action"])}</strong></div>'
            f'<p>{_e(row["reason"])}</p>'
            f'<div>Source: <code>{_e(row["source_id"])}</code></div>'
            f'<div>Chunk: <code>{_e(row["chunk_id"])}</code></div>'
            "</div>"
        )
    return "\n".join(rendered)


def _timings_table(timings: dict[str, Any]) -> str:
    if not timings:
        return "<p>No timing metadata is available.</p>"
    rows = []
    for key, value in timings.items():
        if isinstance(value, (int, float)):
            rows.append(
                "<tr>"
                f"<td>{_e(key)}</td>"
                f"<td>{_e(_fmt(value))}</td>"
                "</tr>"
            )
    return "<table><tbody>" + "".join(rows) + "</tbody></table>"


def _evaluation_section(evaluation: dict[str, Any] | None) -> str:
    if not evaluation:
        return ""
    summary = evaluation["summary"]
    latency = summary.get("per_stage_latency_seconds", {}).get("total_seconds", {})
    return f"""
    <section>
      <h2>Bounded Fan Evaluation</h2>
      <div class="grid">
        {_metric("Events", summary["total_events"])}
        {_metric("Expert B Runs", summary["expert_b_execution_count"])}
        {_metric("Pipeline Failures", summary["pipeline_failures"])}
        {_metric("Explanation Fallbacks", summary["gemini_explanation_fallback_count"])}
        {_metric("Maintenance Fallbacks", summary["maintenance_fallback_count"])}
        {_metric("Citation Failures", summary["citation_validation_failures"])}
        {_metric("Mean Completed Runtime", _fmt(latency.get("mean", "not recorded")))}
      </div>
      <span class="flag warning">Bounded integration stress set; not diagnostic accuracy or production validation.</span>
    </section>
    """


def _limit_rows(data: dict[str, Any]) -> str:
    limits = data.get("limits", {})
    rows = {
        "Same machine, same audio": limits.get("same_machine_same_audio", True),
        "Rank scores are probabilities": limits.get("rank_scores_are_probabilities", False),
        "Physical cause confirmed": limits.get("physical_root_cause_confirmed", False),
        "Lifetime estimate available": limits.get("remaining_life_prediction_available", False),
        "Production maintenance validation complete": limits.get(
            "production_maintenance_validation_complete",
            False,
        ),
        "Multi-machine generalization enabled": limits.get(
            "multi_machine_generalization_enabled",
            False,
        ),
    }
    return "<table><tbody>" + "".join(
        "<tr>"
        f"<td>{_e(key)}</td>"
        f"<td>{_e(value)}</td>"
        "</tr>"
        for key, value in rows.items()
    ) + "</tbody></table>"


def _fallback_flag(value: Any) -> str:
    if value is True:
        return '<span class="flag warning">Fallback used</span>'
    return ""


def _source_note(data: dict[str, Any]) -> str:
    source_mode = str(data.get("maintenance_source_mode", "approved_public_corpus"))
    if "fixture" in source_mode:
        return "Maintenance source is a smoke fixture, not production maintenance validation."
    return "Maintenance source is an approved public Fan corpus, not production maintenance validation."


def _list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul>"


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


if __name__ == "__main__":
    main()
