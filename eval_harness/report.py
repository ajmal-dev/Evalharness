"""Turns a RunSummary into a JSON file, an HTML dashboard, and terminal output."""

import html
import json
from pathlib import Path

from eval_harness.models import RunSummary


def summary_to_dict(summary: RunSummary) -> dict:
    return {
        "provider": summary.provider_name,
        "started_at": summary.started_at,
        "finished_at": summary.finished_at,
        "total": summary.total,
        "passed": summary.passed,
        "failed": summary.failed,
        "pass_rate": summary.pass_rate,
        "by_category": summary.by_category,
        "cases": [
            {
                "id": r.case.id,
                "category": r.case.category,
                "eval_method": r.case.eval_method,
                "prompt": r.case.prompt,
                "tags": r.case.tags,
                "output": r.output,
                "latency_ms": round(r.latency_ms, 2),
                "passed": r.eval_result.passed,
                "score": round(r.eval_result.score, 4),
                "reason": r.eval_result.reason,
            }
            for r in summary.case_results
        ],
    }


def write_json(summary: RunSummary, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "results.json"
    path.write_text(
        json.dumps(summary_to_dict(summary), indent=2), encoding="utf-8"
    )
    return path


def print_terminal_summary(summary: RunSummary) -> None:
    print(f"Provider: {summary.provider_name}")
    print(
        f"Total: {summary.total}  Passed: {summary.passed}  "
        f"Failed: {summary.failed}  Pass rate: {summary.pass_rate:.1%}"
    )
    print()
    print(f"{'ID':<14}{'Category':<16}{'Method':<14}{'Result':<8}{'Score':<7}")
    print("-" * 59)
    for r in summary.case_results:
        result = "PASS" if r.eval_result.passed else "FAIL"
        print(
            f"{r.case.id:<14}{r.case.category:<16}{r.case.eval_method:<14}"
            f"{result:<8}{r.eval_result.score:<7.2f}"
        )
    print()
    print("By category:")
    for category, counts in sorted(summary.by_category.items()):
        total = counts["passed"] + counts["failed"]
        print(f"  {category:<16} {counts['passed']}/{total} passed")


def write_html(summary: RunSummary, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.html"
    path.write_text(_render_html(summary), encoding="utf-8")
    return path


def _render_html(summary: RunSummary) -> str:
    esc = html.escape
    pass_rate_pct = f"{summary.pass_rate * 100:.1f}%"
    pass_rate_class = (
        "good" if summary.pass_rate >= 0.9 else "warn" if summary.pass_rate >= 0.7 else "bad"
    )

    category_rows = ""
    for category, counts in sorted(summary.by_category.items()):
        total = counts["passed"] + counts["failed"]
        rate = counts["passed"] / total if total else 0.0
        category_rows += f"""
        <tr>
          <td>{esc(category)}</td>
          <td>{counts['passed']}</td>
          <td>{counts['failed']}</td>
          <td>{total}</td>
          <td>{rate * 100:.0f}%</td>
        </tr>"""

    case_rows = ""
    sorted_results = sorted(
        summary.case_results, key=lambda r: (r.case.category, r.case.id)
    )
    for r in sorted_results:
        status_class = "pass" if r.eval_result.passed else "fail"
        status_label = "PASS" if r.eval_result.passed else "FAIL"
        tags = ", ".join(r.case.tags) if r.case.tags else "&mdash;"
        case_rows += f"""
      <details class="case {status_class}">
        <summary>
          <span class="badge {status_class}">{status_label}</span>
          <span class="case-id">{esc(r.case.id)}</span>
          <span class="case-category">{esc(r.case.category)}</span>
          <span class="case-method">{esc(r.case.eval_method)}</span>
          <span class="case-score">score {r.eval_result.score:.2f}</span>
          <span class="case-latency">{r.latency_ms:.0f} ms</span>
        </summary>
        <div class="detail">
          <div class="field"><span class="label">Prompt</span><pre>{esc(r.case.prompt)}</pre></div>
          <div class="field"><span class="label">Output</span><pre>{esc(r.output)}</pre></div>
          <div class="field"><span class="label">Reason</span><pre>{esc(r.eval_result.reason)}</pre></div>
          <div class="field"><span class="label">Tags</span> {tags}</div>
        </div>
      </details>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LLM Eval Harness Report</title>
<style>
  :root {{
    --bg: #f7f7f9;
    --card-bg: #ffffff;
    --border: #e2e2e7;
    --text: #1c1c22;
    --muted: #6b6b75;
    --good: #1a7f4e;
    --good-bg: #e6f6ee;
    --bad: #b3261e;
    --bad-bg: #fbe9e8;
    --warn: #a3620a;
    --warn-bg: #fdf3e0;
    --accent: #4b3fd6;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
  }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 4px; }}
  .meta {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 28px; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 32px; }}
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }}
  .card .value {{ font-size: 1.7rem; font-weight: 700; }}
  .card .label {{ color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.03em; }}
  .card.good .value {{ color: var(--good); }}
  .card.warn .value {{ color: var(--warn); }}
  .card.bad .value {{ color: var(--bad); }}
  h2 {{ font-size: 1.1rem; margin: 32px 0 12px; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
  th {{ color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.03em; }}
  tr:last-child td {{ border-bottom: none; }}
  details.case {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-left: 4px solid var(--border);
    border-radius: 8px;
    margin-bottom: 8px;
    padding: 0;
  }}
  details.case.pass {{ border-left-color: var(--good); }}
  details.case.fail {{ border-left-color: var(--bad); }}
  details.case summary {{
    cursor: pointer;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.88rem;
    list-style: none;
  }}
  details.case summary::-webkit-details-marker {{ display: none; }}
  .badge {{ font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; letter-spacing: 0.03em; }}
  .badge.pass {{ color: var(--good); background: var(--good-bg); }}
  .badge.fail {{ color: var(--bad); background: var(--bad-bg); }}
  .case-id {{ font-weight: 600; min-width: 90px; }}
  .case-category {{ color: var(--muted); }}
  .case-method {{ color: var(--accent); font-family: ui-monospace, monospace; font-size: 0.78rem; }}
  .case-score, .case-latency {{ margin-left: auto; color: var(--muted); font-size: 0.8rem; }}
  .detail {{ padding: 4px 14px 14px; border-top: 1px solid var(--border); }}
  .field {{ margin-top: 10px; }}
  .field .label {{ display: block; color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 4px; }}
  pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>LLM Eval Harness Report</h1>
  <div class="meta">
    Provider: <strong>{esc(summary.provider_name)}</strong>
    &middot; Started: {esc(summary.started_at)}
    &middot; Finished: {esc(summary.finished_at)}
  </div>

  <div class="cards">
    <div class="card"><div class="value">{summary.total}</div><div class="label">Total cases</div></div>
    <div class="card good"><div class="value">{summary.passed}</div><div class="label">Passed</div></div>
    <div class="card bad"><div class="value">{summary.failed}</div><div class="label">Failed</div></div>
    <div class="card {pass_rate_class}"><div class="value">{pass_rate_pct}</div><div class="label">Pass rate</div></div>
  </div>

  <h2>By category</h2>
  <table>
    <thead><tr><th>Category</th><th>Passed</th><th>Failed</th><th>Total</th><th>Pass rate</th></tr></thead>
    <tbody>{category_rows}
    </tbody>
  </table>

  <h2>Case results</h2>
  {case_rows}
</div>
</body>
</html>
"""
