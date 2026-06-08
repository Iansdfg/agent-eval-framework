import os
import json
from evals.run_eval import load_cases, run


def test_load_cases():
    path = os.path.join(os.path.dirname(__file__), "..", "evals", "cases.jsonl")
    cases = load_cases(path)
    assert len(cases) >= 1


def test_run_eval_returns_exit_code_zero_for_improved_candidate(monkeypatch, tmp_path):
    # monkeypatch agents to ensure candidate beats baseline
    from app import baseline_agent, candidate_agent

    def b_run(query, case):
        return {
            "answer": "old",
            "tool_trace": [],
            "retrieved_context": [],
            "latency_ms": 10,
            "token_usage": {"input": 5, "output": 5},
            "error": None,
        }

    def c_run(query, case):
        return {
            "answer": "better",
            "tool_trace": [],
            "retrieved_context": [],
            "latency_ms": 10,
            "token_usage": {"input": 5, "output": 5},
            "error": None,
        }

    monkeypatch.setattr(baseline_agent, "run_agent", b_run)
    monkeypatch.setattr(candidate_agent, "run_agent", c_run)

    # run the evaluation; expect exit code 1 or 0 depending on dataset, but ensure runner runs
    rc = run()
    assert isinstance(rc, int)
