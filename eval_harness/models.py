"""Core data types shared across the harness."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GoldenCase:
    id: str
    category: str
    prompt: str
    mock_response: str
    eval_method: str
    eval_config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class EvalResult:
    passed: bool
    score: float
    reason: str


@dataclass
class CaseResult:
    case: GoldenCase
    output: str
    eval_result: EvalResult
    latency_ms: float


@dataclass
class RunSummary:
    provider_name: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    by_category: Dict[str, Dict[str, int]]
    case_results: List[CaseResult]
    started_at: str
    finished_at: str
