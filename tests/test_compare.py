from evals.schemas import Case, Score, CompareConfig
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


def test_compare_ignores_non_critical_faithfulness_failures():
    cfg = CompareConfig()
    cases = [
        Case(
            case_id="case_non_critical",
            category="email_generation",
            query="Write an email",
            expected_answer="email",
            critical=False,
            expected_sources=["doc_product_faq"],
        )
    ]
    baseline_scores = [make_score()]
    candidate_scores = [make_score(faithfulness=0.0)]
    baseline_outputs = [type("O", (), {"latency_ms": 10, "error": None})()]
    candidate_outputs = [type("O", (), {"latency_ms": 10, "error": None})()]

    res = compare(baseline_scores, candidate_scores, baseline_outputs, candidate_outputs, cfg, cases)

    assert res["critical_failures"] == []


def test_compare_uses_score_tolerance():
    cfg = CompareConfig(score_tolerance=0.01)
    baseline_scores = [Score(correctness=5.0, faithfulness=5.0, relevance=5.0, format_correctness=5.0, tool_use_accuracy=5.0)]
    candidate_scores = [Score(correctness=4.99, faithfulness=5.0, relevance=5.0, format_correctness=5.0, tool_use_accuracy=5.0)]
    baseline_outputs = [type("O", (), {"latency_ms": 10, "error": None})()]
    candidate_outputs = [type("O", (), {"latency_ms": 10, "error": None})()]

    res = compare(baseline_scores, candidate_scores, baseline_outputs, candidate_outputs, cfg)

    assert res["pass"] is True
