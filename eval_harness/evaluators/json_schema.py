import json

import jsonschema

from eval_harness.evaluators.base import Evaluator
from eval_harness.models import EvalResult, GoldenCase


class JsonSchemaEvaluator(Evaluator):
    """Parses the output as JSON and validates it against eval_config.schema."""

    def evaluate(self, case: GoldenCase, output: str) -> EvalResult:
        schema = case.eval_config["schema"]

        try:
            data = json.loads(output.strip())
        except json.JSONDecodeError as exc:
            return EvalResult(
                passed=False, score=0.0, reason=f"Output is not valid JSON: {exc}"
            )

        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as exc:
            return EvalResult(
                passed=False,
                score=0.0,
                reason=f"Schema validation failed: {exc.message}",
            )

        return EvalResult(
            passed=True, score=1.0, reason="Output is valid JSON matching schema."
        )
