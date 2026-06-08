from typing import Dict, Any
import time


def run_agent(query: str, case: Dict[str, Any]) -> Dict[str, Any]:
    # Mock baseline: conservative answers
    start = time.time()
    category = case.get("category")
    case_id = case.get("case_id")
    if category == "format":
        answer = case.get("expected_answer")  # baseline returns expected format
    elif category == "safety":
        answer = "I cannot assist with that."
    elif category == "tool":
        answer = case.get("expected_answer")
    else:
        answer = str(case.get("expected_answer"))

    latency_ms = int((time.time() - start) * 1000)
    return {
        "answer": answer,
        "tool_trace": case.get("expected_tool_calls", []),
        "retrieved_context": case.get("expected_sources", []),
        "latency_ms": latency_ms,
        "token_usage": {"input": 10, "output": 10},
        "error": None,
    }
