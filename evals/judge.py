import os
import json
from typing import Dict, Any, List
from evals.schemas import Case, AgentOutput, Score


def _score_scale(x: float) -> float:
    # clamp between 0 and 5
    return max(0.0, min(5.0, x))


def heuristic_score(case: Case, output: AgentOutput) -> Score:
    reason_parts: List[str] = []
    # correctness: simple token overlap with expected_answer
    expected = str(case.expected_answer).lower()
    ans = (output.answer or "").lower()
    if not ans:
        correctness = 0.0
        reason_parts.append("empty answer")
    else:
        overlap = len(set(expected.split()) & set(ans.split()))
        total = max(1, len(set(expected.split())))
        correctness = _score_scale(5.0 * (overlap / total))

    # faithfulness: if expected_sources present, check retrieved_context
    if case.expected_sources:
        hits = sum(1 for s in case.expected_sources if any(s in c for c in output.retrieved_context))
        faithfulness = _score_scale(5.0 * (hits / len(case.expected_sources)))
    else:
        faithfulness = 5.0

    # relevance: presence of some expected words
    relevance = correctness

    # format correctness
    format_correctness = 5.0
    if case.category == "format":
        try:
            json.loads(output.answer)
            format_correctness = 5.0
        except Exception:
            format_correctness = 0.0
            reason_parts.append("invalid json format")

    # tool use accuracy
    tool_use_accuracy = 5.0
    if case.expected_tool_calls:
        hits = sum(1 for t in case.expected_tool_calls if t in output.tool_trace)
        tool_use_accuracy = _score_scale(5.0 * (hits / len(case.expected_tool_calls)))

    return Score(
        correctness=round(correctness, 2),
        faithfulness=round(faithfulness, 2),
        relevance=round(relevance, 2),
        format_correctness=round(format_correctness, 2),
        tool_use_accuracy=round(tool_use_accuracy, 2),
        reason="; ".join(reason_parts) if reason_parts else ""
    )


def judge_with_llm(case: Case, baseline_output: AgentOutput, candidate_output: AgentOutput) -> Score:
    # Placeholder: in real usage, call OpenAI-compatible LLM judge API
    # For MVP, we return heuristic average between baseline and candidate differences
    # NOTE: This function is optional and guarded by ENABLE_LLM_JUDGE env var in runner
    return heuristic_score(case, candidate_output)


def judge(case: Case, output: AgentOutput, use_llm: bool = False, baseline_output: AgentOutput = None) -> Score:
    if use_llm and os.getenv("ENABLE_LLM_JUDGE", "false").lower() == "true":
        return judge_with_llm(case, baseline_output, output)
    return heuristic_score(case, output)
