import os
import time
from typing import Any, Dict

import httpx

from app.agent_adapter import normalize_retrieved_context, normalize_tool_trace


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = float(os.getenv("BASELINE_AGENT_TIMEOUT_SECONDS", "60"))


def run_agent(query: str, case: Dict[str, Any]) -> Dict[str, Any]:
    start = time.time()
    base_url = os.getenv("BASELINE_AGENT_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    api_key = os.getenv("BASELINE_AGENT_API_KEY")

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
        tool_trace = normalize_tool_trace(payload.get("tool_trace", []))
        retrieved_context = normalize_retrieved_context(payload.get("citations", []))
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
