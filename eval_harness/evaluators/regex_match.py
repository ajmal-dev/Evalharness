import re

from eval_harness.evaluators.base import Evaluator
from eval_harness.models import EvalResult, GoldenCase


class RegexMatchEvaluator(Evaluator):
    """Passes if whether eval_config.pattern matches the output equals
    eval_config.expected_match (default True). Set expected_match to False
    to assert the pattern must NOT appear (e.g. catching over-refusal).
    """

    def evaluate(self, case: GoldenCase, output: str) -> EvalResult:
        pattern = case.eval_config["pattern"]
        expected_match = case.eval_config.get("expected_match", True)

        matched = re.search(pattern, output, re.IGNORECASE) is not None
        passed = matched == expected_match

        if expected_match:
            reason = (
                f"Pattern {pattern!r} matched as expected."
                if matched
                else f"Pattern {pattern!r} was expected to match but did not."
            )
        else:
            reason = (
                f"Pattern {pattern!r} correctly did not match."
                if not matched
                else f"Pattern {pattern!r} matched but was expected not to."
            )

        return EvalResult(passed=passed, score=1.0 if passed else 0.0, reason=reason)
