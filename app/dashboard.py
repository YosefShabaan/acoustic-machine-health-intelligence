"""Static dashboard renderer for one Fan MVP end-to-end output."""

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


DEFAULT_INPUT = cfg.PROCESSED_DIR / "end_to_end_fan_id_00_minus6dB_task10.json"
DEFAULT_OUTPUT = cfg.PROCESSED_DIR / "dashboard_fan_id_00_minus6dB_task11.html"


def load_output(path: Path | str = DEFAULT_INPUT) -> dict[str, Any]:
    """Load one end-to-end output JSON artifact."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_dashboard_html(data: dict[str, Any]) -> str:
    """Render the dashboard as a standalone HTML document."""
    context = data["structured_context"]
    technician = data["technician_output"]
    event = context["event"]
    expert_a = context["expert_a"]
    expert_b = context["expert_b"]
    recommendation = technician["recommendation"]
    source_mode = str(data.get("maintenance_source_mode", "unknown"))
    source_note = (
        "Maintenance source is a smoke fixture, not a production manual."
        if source_mode != "production_manuals"
        else "Maintenance source is production manual directory."
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fan MVP Evidence Dashboard</title>
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
    <h1>Fan MVP Evidence Dashboard</h1>
    <div class="subtle">{_e(event["event_id"])} | {_e(event["machine_type"])} {_e(event["machine_id"])} | {_e(event["snr_tag"])}</div>
  </header>
  <main>
    <section>
      <h2>Event</h2>
      <div class="grid">
        {_metric("Asset", event["asset_id"])}
        {_metric("Audio", Path(event["audio_path"]).name)}
        {_metric("Source Mode", source_mode)}
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
      <h2>Retrieved Sources</h2>
      {_sources(technician["retrieved_maintenance_guidance"])}
    </section>

    <section>
      <h2>Recommendation</h2>
      <div class="flag {'warning' if not recommendation['available'] else ''}">{'Source-grounded' if recommendation['available'] else 'Unavailable'}</div>
      <p>{_e(recommendation["text"])}</p>
      <div><strong>Citations:</strong> {_e(", ".join(recommendation["citations"]) or "none")}</div>
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
) -> Path:
    """Write a standalone HTML dashboard."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard_html(data), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    data = load_output(args.input)
    output = write_dashboard(data, args.output)
    print(f"DASHBOARD_RENDER=OK")
    print(f"INPUT={args.input}")
    print(f"OUTPUT={output}")
    print(f"EVENT_ID={data['structured_context']['event']['event_id']}")
    print(f"RECOMMENDATION_AVAILABLE={data['technician_output']['recommendation']['available']}")


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
            f'<div><strong>{_e(row["source_id"])}</strong> | {_e(row["title"])} | {_e(row["version"])}</div>'
            f'<div><code>{_e(row["chunk_id"])}</code></div>'
            f"<p>{_e(row['snippet'])}</p>"
            "</div>"
        )
    return "\n".join(rendered)


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
