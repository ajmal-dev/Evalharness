"""Loads and validates the golden dataset YAML file."""

from pathlib import Path
from typing import List

import yaml

from eval_harness.models import GoldenCase

# eval_config keys required for each eval_method, beyond what "contains"
# needs (which is validated separately since it accepts either of two keys).
_REQUIRED_CONFIG_KEYS = {
    "exact_match": ["expected"],
    "regex_match": ["pattern"],
    "json_schema": ["schema"],
    "llm_judge": ["criteria"],
}


def load_dataset(path: str) -> List[GoldenCase]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    cases_data = raw.get("cases", [])
    if not cases_data:
        raise ValueError(f"No cases found in dataset file: {path}")

    cases: List[GoldenCase] = []
    seen_ids = set()
    for entry in cases_data:
        case = GoldenCase(
            id=entry["id"],
            category=entry["category"],
            prompt=entry["prompt"],
            mock_response=entry["mock_response"],
            eval_method=entry["eval_method"],
            eval_config=entry.get("eval_config", {}) or {},
            tags=entry.get("tags", []) or [],
        )
        if case.id in seen_ids:
            raise ValueError(f"Duplicate case id: {case.id}")
        seen_ids.add(case.id)

        _validate_case(case)
        cases.append(case)

    return cases


def _validate_case(case: GoldenCase) -> None:
    if case.eval_method == "contains":
        if not case.eval_config.get("all_of") and not case.eval_config.get("any_of"):
            raise ValueError(
                f"Case {case.id!r} (contains) needs eval_config.all_of and/or "
                "eval_config.any_of."
            )
        return

    required = _REQUIRED_CONFIG_KEYS.get(case.eval_method)
    if required is None:
        raise ValueError(
            f"Case {case.id!r} has unknown eval_method {case.eval_method!r}."
        )
    for key in required:
        if key not in case.eval_config:
            raise ValueError(
                f"Case {case.id!r} ({case.eval_method}) is missing "
                f"eval_config.{key}."
            )
