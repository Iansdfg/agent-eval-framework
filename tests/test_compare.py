from evals.schemas import Score, CompareConfig
from evals.compare import compare


def make_score(correctness=5.0, faithfulness=5.0):
    return Score(correctness=correctness, faithfulness=faithfulness, relevance=5.0, format_correctness=5.0, tool_use_accuracy=5.0, reason="")


def test_compare_passes_when_candidate_better():
    cfg = CompareConfig(min_score_delta=0.1)
    baseline_scores = [make_score()]
    candidate_scores = [make_score(correctness=5.0, faithfulness=5.0)]
    baseline_outputs = [type("O", (), {"latency_ms": 10, "error": None})()]
    candidate_outputs = [type("O", (), {"latency_ms": 10, "error": None})()]
    res = compare(baseline_scores, candidate_scores, baseline_outputs, candidate_outputs, cfg)
    assert "pass" in res
