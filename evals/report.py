from typing import List, Dict, Any
import datetime
import json


def generate_html(summary: Dict[str, Any], per_case: List[Dict[str, Any]], out_path: str) -> None:
    now = datetime.datetime.utcnow().isoformat()
    baseline_score = summary.get("baseline_overall")
    latency_regression = summary.get("latency_regression_pct")
    html = [
        "<html><head><meta charset=\"utf-8\"><title>Eval Report</title></head><body>",
        f"<h1>Eval Report - {now}</h1>",
        f"<h2>Overall: {'PASS' if summary.get('pass') else 'FAIL'}</h2>",
        f"<p>Baseline: {'enabled' if summary.get('baseline_enabled') else 'disabled'}</p>",
        f"<p>Baseline score: {baseline_score:.2f}</p>" if baseline_score is not None else "<p>Baseline score: n/a</p>",
        f"<p>Candidate score: {summary.get('candidate_overall'):.2f}</p>",
        f"<p>Latency regression %: {latency_regression:.2f}%</p>" if latency_regression is not None else "<p>Latency regression %: n/a</p>",
        "<h2>Per-case results</h2>",
        "<ul>",
    ]

    for c in per_case:
        html.append(f"<li><b>{c['case_id']}</b>: score={c['score_overall']:.2f} reason={c['score'].get('reason','')}")
        if c.get('regression'):
            html.append(" <span style='color:red'>(regression)</span>")
        html.append("</li>")

    html.append("</ul>")
    html.append("</body></html>")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write('\n'.join(html))
