"""Orchestrates a full eval run: dataset -> provider -> evaluator -> summary."""

import time
from datetime import datetime, timezone
from typing import Dict, Type

from eval_harness.dataset import load_dataset
from eval_harness.evaluators.base import Evaluator
from eval_harness.evaluators.contains import ContainsEvaluator
from eval_harness.evaluators.exact_match import ExactMatchEvaluator
from eval_harness.evaluators.json_schema import JsonSchemaEvaluator
from eval_harness.evaluators.llm_judge import MockJudge
from eval_harness.evaluators.regex_match import RegexMatchEvaluator
from eval_harness.models import CaseResult, RunSummary
from eval_harness.providers.anthropic_provider import AnthropicProvider
from eval_harness.providers.base import Provider
from eval_harness.providers.mock_provider import MockProvider

PROVIDERS: Dict[str, Type[Provider]] = {
    "mock": MockProvider,
    "anthropic": AnthropicProvider,
}

EVALUATORS: Dict[str, Type[Evaluator]] = {
    "exact_match": ExactMatchEvaluator,
    "contains": ContainsEvaluator,
    "regex_match": RegexMatchEvaluator,
    "json_schema": JsonSchemaEvaluator,
    "llm_judge": MockJudge,
}


def run_eval(dataset_path: str, provider_name: str) -> RunSummary:
    cases = load_dataset(dataset_path)

    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider {provider_name!r}. Available: {sorted(PROVIDERS)}"
        )
    provider = PROVIDERS[provider_name]()

    started_at = datetime.now(timezone.utc).isoformat()
    case_results = []

    for case in cases:
        evaluator_cls = EVALUATORS.get(case.eval_method)
        if evaluator_cls is None:
            raise ValueError(
                f"Case {case.id!r} uses unknown eval_method {case.eval_method!r}. "
                f"Available: {sorted(EVALUATORS)}"
            )
        evaluator = evaluator_cls()

        t0 = time.perf_counter()
        output = provider.generate(case)
        latency_ms = (time.perf_counter() - t0) * 1000

        eval_result = evaluator.evaluate(case, output)
        case_results.append(
            CaseResult(
                case=case,
                output=output,
                eval_result=eval_result,
                latency_ms=latency_ms,
            )
        )

    finished_at = datetime.now(timezone.utc).isoformat()

    total = len(case_results)
    passed = sum(1 for r in case_results if r.eval_result.passed)
    failed = total - passed
    pass_rate = passed / total if total else 0.0

    by_category: Dict[str, Dict[str, int]] = {}
    for r in case_results:
        bucket = by_category.setdefault(r.case.category, {"passed": 0, "failed": 0})
        bucket["passed" if r.eval_result.passed else "failed"] += 1

    return RunSummary(
        provider_name=provider_name,
        total=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        by_category=by_category,
        case_results=case_results,
        started_at=started_at,
        finished_at=finished_at,
    )
