"""Evaluator abstraction: scores a model output against a golden case."""

from abc import ABC, abstractmethod

from eval_harness.models import EvalResult, GoldenCase


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, case: GoldenCase, output: str) -> EvalResult:
        raise NotImplementedError
