from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Case(BaseModel):
    case_id: str
    category: str
    query: str
    expected_answer: Any
    rubric: Optional[str] = None
    critical: bool = False
    expected_tool_calls: Optional[List[str]] = []
    expected_sources: Optional[List[str]] = []


class AgentOutput(BaseModel):
    answer: str
    tool_trace: List[str] = Field(default_factory=list)
    retrieved_context: List[str] = Field(default_factory=list)
    latency_ms: int = 0
    token_usage: Dict[str, int] = Field(default_factory=lambda: {"input": 0, "output": 0})
    error: Optional[str] = None


class Score(BaseModel):
    correctness: float
    faithfulness: float
    relevance: float
    format_correctness: float
    tool_use_accuracy: float
    reason: Optional[str] = None


class EvalResult(BaseModel):
    case_id: str
    case: Case
    output: AgentOutput
    score: Score


class CompareConfig(BaseModel):
    min_score_delta: float = 0.0
    score_tolerance: float = 0.01
    max_latency_regression_pct: float = 30.0
    min_critical_faithfulness: float = 4.0
    required_critical_pass_rate: float = 1.0
