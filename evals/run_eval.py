import json
import os
import csv
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

load_dotenv()

from evals.schemas import Case, AgentOutput, EvalResult, CompareConfig
from evals.judge import judge
from evals.compare import compare
from evals.report import generate_html

from app.baseline_agent import run_agent as run_baseline
from app.candidate_agent import run_agent as run_candidate


CASES_PATH = os.path.join(os.path.dirname(__file__), "cases.jsonl")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_cases(path: str) -> List[Case]:
    cases: List[Case] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(Case.parse_raw(line))
    return cases


def run() -> int:
    cases = load_cases(CASES_PATH)

    baseline_results = []
    candidate_results = []

    for case in cases:
        start = time.time()
        b_out = run_baseline(case.query, case.dict())
        b_out_obj = AgentOutput(**b_out)
        b_out_obj.latency_ms = int((time.time() - start) * 1000)

        start = time.time()
        c_out = run_candidate(case.query, case.dict())
        c_out_obj = AgentOutput(**c_out)
        c_out_obj.latency_ms = int((time.time() - start) * 1000)

        b_score = judge(case, b_out_obj, use_llm=False, baseline_output=None)
        c_score = judge(case, c_out_obj, use_llm=False, baseline_output=b_out_obj)

        baseline_results.append({"case_id": case.case_id, "case": case.dict(), "output": b_out_obj.dict(), "score": b_score.dict()})
        candidate_results.append({"case_id": case.case_id, "case": case.dict(), "output": c_out_obj.dict(), "score": c_score.dict()})

    # persist results
    eval_results_path = os.path.join(OUTPUT_DIR, "eval_results.json")
    with open(eval_results_path, "w", encoding="utf-8") as f:
        json.dump({"baseline": baseline_results, "candidate": candidate_results}, f, indent=2)

    # prepare comparison
    from evals.schemas import Score
    baseline_scores = [Score(**r["score"]) if isinstance(r["score"], dict) else r["score"] for r in baseline_results]
    candidate_scores = [Score(**r["score"]) if isinstance(r["score"], dict) else r["score"] for r in candidate_results]

    baseline_outputs = [type("O", (), r["output"])() for r in baseline_results]
    candidate_outputs = [type("O", (), r["output"])() for r in candidate_results]

    # populate attributes on lightweight objects
    for o, r in zip(baseline_outputs, baseline_results):
        for k, v in r["output"].items():
            setattr(o, k, v)
    for o, r in zip(candidate_outputs, candidate_results):
        for k, v in r["output"].items():
            setattr(o, k, v)

    cfg = CompareConfig()
    summary = compare(baseline_scores, candidate_scores, baseline_outputs, candidate_outputs, cfg)

    summary_path = os.path.join(OUTPUT_DIR, "eval_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # regression cases: candidate worse than baseline on overall score
    regression_path = os.path.join(OUTPUT_DIR, "regression_cases.csv")
    with open(regression_path, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "baseline_overall", "candidate_overall"])
        per_case = []
        for b, c in zip(baseline_results, candidate_results):
            b_score = sum([v for v in b["score"].values() if isinstance(v, (int, float))]) / 5.0
            c_score = sum([v for v in c["score"].values() if isinstance(v, (int, float))]) / 5.0
            per_case.append({"case_id": b["case_id"], "score_overall": c_score, "score": c["score"]})
            if c_score < b_score:
                writer.writerow([b["case_id"], f"{b_score:.2f}", f"{c_score:.2f}"])

    # html report
    report_path = os.path.join(OUTPUT_DIR, "eval_report.html")
    generate_html(summary, per_case, report_path)

    print(f"Wrote artifacts to {OUTPUT_DIR}")

    return 0 if summary.get("pass") else 1


if __name__ == "__main__":
    rc = run()
    sys.exit(rc)
