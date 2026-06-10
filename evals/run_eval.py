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

from app.baseline_agent import agent_url as baseline_agent_url
from app.baseline_agent import run_agent as run_baseline
from app.candidate_agent import agent_url as candidate_agent_url
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


def baseline_enabled() -> bool:
    value = os.getenv("BASELINE_AGENT_ENABLED", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def score_overall(score: Dict[str, Any]) -> float:
    return sum([v for v in score.values() if isinstance(v, (int, float))]) / 5.0


def run() -> int:
    cases = load_cases(CASES_PATH)
    total_cases = len(cases)
    use_baseline = baseline_enabled()

    if use_baseline:
        print(f"Baseline agent URL: {baseline_agent_url()}/chat")
    else:
        print("Baseline agent: disabled (BASELINE_AGENT_ENABLED=false)")
    print(f"Candidate agent URL: {candidate_agent_url()}/chat")

    baseline_results = []
    candidate_results = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{total_cases}] Running {case.case_id} ({case.category}): {case.query}")

        b_out_obj = None
        b_score = None
        b_overall = None
        if use_baseline:
            start = time.time()
            b_out = run_baseline(case.query, case.dict())
            b_out_obj = AgentOutput(**b_out)
            b_out_obj.latency_ms = int((time.time() - start) * 1000)
            b_score = judge(case, b_out_obj, use_llm=False, baseline_output=None)
            b_overall = (
                b_score.correctness
                + b_score.faithfulness
                + b_score.relevance
                + b_score.format_correctness
                + b_score.tool_use_accuracy
            ) / 5.0

        start = time.time()
        c_out = run_candidate(case.query, case.dict())
        c_out_obj = AgentOutput(**c_out)
        c_out_obj.latency_ms = int((time.time() - start) * 1000)

        c_score = judge(case, c_out_obj, use_llm=False, baseline_output=b_out_obj)
        c_overall = (
            c_score.correctness
            + c_score.faithfulness
            + c_score.relevance
            + c_score.format_correctness
            + c_score.tool_use_accuracy
        ) / 5.0

        if use_baseline and b_out_obj and b_overall is not None:
            baseline_log = (
                f"baseline={b_overall:.2f} ({b_out_obj.latency_ms}ms"
                f"{', error' if b_out_obj.error else ''})"
            )
        else:
            baseline_log = "baseline=disabled"

        print(
            f"[{index}/{total_cases}] Completed {case.case_id}: "
            f"{baseline_log}, candidate={c_overall:.2f} ({c_out_obj.latency_ms}ms"
            f"{', error' if c_out_obj.error else ''})"
        )

        if use_baseline and b_out_obj and b_score:
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
    summary = compare(baseline_scores, candidate_scores, baseline_outputs, candidate_outputs, cfg, cases, use_baseline)

    summary_path = os.path.join(OUTPUT_DIR, "eval_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # regression cases: candidate worse than baseline on overall score
    regression_path = os.path.join(OUTPUT_DIR, "regression_cases.csv")
    with open(regression_path, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        per_case = []
        if use_baseline:
            writer.writerow(["case_id", "baseline_overall", "candidate_overall"])
            for b, c in zip(baseline_results, candidate_results):
                b_score = score_overall(b["score"])
                c_score = score_overall(c["score"])
                per_case.append({"case_id": b["case_id"], "score_overall": c_score, "score": c["score"]})
                if c_score < b_score:
                    writer.writerow([b["case_id"], f"{b_score:.2f}", f"{c_score:.2f}"])
        else:
            writer.writerow(["case_id", "candidate_overall"])
            for c in candidate_results:
                c_score = score_overall(c["score"])
                per_case.append({"case_id": c["case_id"], "score_overall": c_score, "score": c["score"]})

    # html report
    report_path = os.path.join(OUTPUT_DIR, "eval_report.html")
    generate_html(summary, per_case, report_path)

    print(f"Wrote artifacts to {OUTPUT_DIR}")

    return 0 if summary.get("pass") else 1


if __name__ == "__main__":
    rc = run()
    sys.exit(rc)
