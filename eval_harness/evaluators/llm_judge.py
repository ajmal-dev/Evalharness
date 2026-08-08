"""LLM-as-judge style evaluator.

MockJudge simulates what a real LLM grader would do: given a rubric of
weighted criteria, it scores an output by checking whether each criterion's
keywords appear in the text. This keeps the harness fully offline and free
to run, which is why it's the default judge here.

To swap in a REAL LLM judge instead of this simulation, implement a new
Evaluator whose evaluate() sends the output + rubric to an LLM (e.g. via
AnthropicProvider) with a grading prompt like:

    "Given this rubric: {criteria}. Given this candidate output: {output}.
     For each criterion, answer yes/no and explain why. Then give an
     overall score from 0 to 1."

...parses a structured score/explanation out of the response (structured
outputs / a JSON schema work well here), and returns an EvalResult built
from that. The eval_config shape (criteria + min_score) can stay exactly
the same — only the scoring mechanism changes, and register the new class
under the "llm_judge" key in runner.EVALUATORS in place of MockJudge.
"""

from eval_harness.evaluators.base import Evaluator
from eval_harness.models import EvalResult, GoldenCase


class MockJudge(Evaluator):
    def evaluate(self, case: GoldenCase, output: str) -> EvalResult:
        criteria = case.eval_config["criteria"]
        min_score = case.eval_config.get("min_score", 0.7)

        haystack = output.lower()
        total_weight = sum(c.get("weight", 1.0) for c in criteria)
        earned_weight = 0.0
        satisfied, missing = [], []

        for criterion in criteria:
            keywords = criterion.get("keywords", [])
            weight = criterion.get("weight", 1.0)
            hit = any(kw.lower() in haystack for kw in keywords)
            if hit:
                earned_weight += weight
                satisfied.append(criterion["name"])
            else:
                missing.append(criterion["name"])

        score = earned_weight / total_weight if total_weight else 0.0
        passed = score >= min_score

        reason = f"Score {score:.2f} (threshold {min_score:.2f})."
        if satisfied:
            reason += f" Satisfied: {', '.join(satisfied)}."
        if missing:
            reason += f" Missing: {', '.join(missing)}."

        return EvalResult(passed=passed, score=score, reason=reason)
