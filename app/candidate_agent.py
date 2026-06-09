import os
import time
from typing import Any, Dict, List

import httpx


DEFAULT_BASE_URL = "http://ai-agent-platform-alb-1032596770.us-east-1.elb.amazonaws.com"
TIMEOUT_SECONDS = float(os.getenv("CANDIDATE_AGENT_TIMEOUT_SECONDS", "60"))


def _stringify_trace_items(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []

    values: List[str] = []
    for item in items:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            value = (
                item.get("tool_name")
                or item.get("name")
                or item.get("tool")
                or item.get("id")
                or str(item)
            )
            values.append(str(value))
        else:
            values.append(str(item))
    return values


def _stringify_citations(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []

    values: List[str] = []
    for item in items:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            value = (
                item.get("source_id")
                or item.get("source")
                or item.get("document_id")
                or item.get("id")
                or item.get("url")
                or str(item)
            )
            values.append(str(value))
        else:
            values.append(str(item))
    return values


def run_agent(query: str, case: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    base_url = os.getenv("CANDIDATE_AGENT_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    api_key = os.getenv("CANDIDATE_AGENT_API_KEY")

    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = httpx.post(
            f"{base_url}/chat",
            json={"message": query, "session_id": case.get("case_id")},
            headers=headers,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        answer = payload.get("answer", "")
        metadata = payload.get("metadata") or {}
        token_usage = metadata.get("token_usage") or {
            "input": metadata.get("input_tokens", 0),
            "output": metadata.get("output_tokens", 0),
        }
        tool_trace = _stringify_trace_items(payload.get("tool_trace", []))
        retrieved_context = _stringify_citations(payload.get("citations", []))
        error = None
    except Exception as exc:
        answer = ""
        tool_trace = []
        retrieved_context = []
        token_usage = {"input": 0, "output": 0}
        error = str(exc)

    latency_ms = int((time.time() - start) * 1000)
    return {
        "answer": answer,
        "tool_trace": tool_trace,
        "retrieved_context": retrieved_context,
        "latency_ms": latency_ms,
        "token_usage": token_usage,
        "error": error,
    }
