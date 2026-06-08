from typing import Dict, Any
import time


def run_agent(query: str, case: Dict[str, Any]) -> Dict[str, Any]:
    # Mock candidate: slightly better on non-critical cases, but may regress on some
    start = time.time()
    category = case.get("category")
    case_id = case.get("case_id")
    # introduce a simple deterministic behavior for testing
    if case_id.endswith("3"):
        # simulate a regression for case 003
        answer = "{invalid json"
    elif category == "safety":
        answer = "I cannot assist with that."
    elif category == "format":
        # return valid JSON for format cases except case_003
        answer = case.get("expected_answer")
    else:
        answer = case.get("expected_answer")

    latency_ms = int((time.time() - start) * 1000)
    return {
        "answer": answer,
        "tool_trace": case.get("expected_tool_calls", []),
        "retrieved_context": case.get("expected_sources", []),
        "latency_ms": latency_ms,
        "token_usage": {"input": 8, "output": 12},
        "error": None,
    }
