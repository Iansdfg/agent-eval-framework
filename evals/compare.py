from typing import Any, Dict, List, Optional

from evals.schemas import Case, CompareConfig, Score


def overall_score(score: Score) -> float:
    # average of the five metrics, scale 0-5
    vals = [score.correctness, score.faithfulness, score.relevance, score.format_correctness, score.tool_use_accuracy]
    return sum(vals) / len(vals)


def compare(
    baseline_scores: List[Score],
    candidate_scores: List[Score],
    baseline_outputs: List[Any],
    candidate_outputs: List[Any],
    config: CompareConfig,
    cases: Optional[List[Case]] = None,
) -> Dict[str, Any]:
    # compute overall averages
    baseline_overall = sum(overall_score(s) for s in baseline_scores) / max(1, len(baseline_scores))
    candidate_overall = sum(overall_score(s) for s in candidate_scores) / max(1, len(candidate_scores))

    # latency and error rates
    def error_rate(outputs):
        return sum(1 for o in outputs if o.error) / max(1, len(outputs))

    baseline_latency = sum(o.latency_ms for o in baseline_outputs) / max(1, len(baseline_outputs))
    candidate_latency = sum(o.latency_ms for o in candidate_outputs) / max(1, len(candidate_outputs))

    latency_regression_pct = ((candidate_latency - baseline_latency) / max(1.0, baseline_latency)) * 100.0

    baseline_err = error_rate(baseline_outputs)
    candidate_err = error_rate(candidate_outputs)

    critical_failures = []
    for i, s in enumerate(candidate_scores):
        is_critical = cases[i].critical if cases and i < len(cases) else True
        if is_critical and s.faithfulness < config.min_critical_faithfulness:
            critical_failures.append(i)

    pass_deploy = True
    min_candidate_score = baseline_overall * (1.0 + config.min_score_delta)
    if candidate_overall + config.score_tolerance < min_candidate_score:
        pass_deploy = False

    if latency_regression_pct > config.max_latency_regression_pct:
        pass_deploy = False

    if candidate_err > baseline_err:
        pass_deploy = False

    if critical_failures and config.required_critical_pass_rate >= 1.0:
        pass_deploy = False

    return {
        "baseline_overall": baseline_overall,
        "candidate_overall": candidate_overall,
        "latency_regression_pct": latency_regression_pct,
        "baseline_error_rate": baseline_err,
        "candidate_error_rate": candidate_err,
        "critical_failures": critical_failures,
        "pass": pass_deploy,
    }
