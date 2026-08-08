from eval_harness.evaluators.base import Evaluator
from eval_harness.models import EvalResult, GoldenCase


class ContainsEvaluator(Evaluator):
    """Passes if the output contains all of `all_of` and at least one of
    `any_of` (either key is optional, but at least one must be set).
    """

    def evaluate(self, case: GoldenCase, output: str) -> EvalResult:
        all_of = case.eval_config.get("all_of", [])
        any_of = case.eval_config.get("any_of", [])
        case_sensitive = case.eval_config.get("case_sensitive", False)

        def norm(s: str) -> str:
            return s if case_sensitive else s.lower()

        haystack = norm(output)
        missing_all = [s for s in all_of if norm(s) not in haystack]
        any_hit = any(norm(s) in haystack for s in any_of) if any_of else True

        passed = not missing_all and any_hit
        reasons = []
        if missing_all:
            reasons.append(f"missing required substrings: {missing_all}")
        if any_of and not any_hit:
            reasons.append(f"none of the expected substrings found: {any_of}")
        reason = "All required substrings found." if passed else "; ".join(reasons)

        total_checks = len(all_of) + (1 if any_of else 0)
        satisfied = (len(all_of) - len(missing_all)) + (1 if any_hit and any_of else 0)
        score = satisfied / total_checks if total_checks else 1.0

        return EvalResult(passed=passed, score=score, reason=reason)
