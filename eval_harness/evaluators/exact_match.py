from eval_harness.evaluators.base import Evaluator
from eval_harness.models import EvalResult, GoldenCase


class ExactMatchEvaluator(Evaluator):
    """Passes only if the output equals eval_config.expected exactly
    (modulo surrounding whitespace and, optionally, case).
    """

    def evaluate(self, case: GoldenCase, output: str) -> EvalResult:
        expected = case.eval_config["expected"]
        case_sensitive = case.eval_config.get("case_sensitive", True)

        actual = output.strip()
        target = expected.strip()
        if not case_sensitive:
            actual = actual.lower()
            target = target.lower()

        passed = actual == target
        reason = (
            f"Output matched expected value {expected!r}."
            if passed
            else f"Expected {expected!r}, got {output.strip()!r}."
        )
        return EvalResult(passed=passed, score=1.0 if passed else 0.0, reason=reason)
