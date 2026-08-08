"""Provider abstraction: anything that can turn a prompt into a model output."""

from abc import ABC, abstractmethod

from eval_harness.models import GoldenCase


class Provider(ABC):
    """A Provider's only job is: prompt in, model output out.

    Whether that output comes from a live API call or a canned string is an
    implementation detail hidden behind this interface, which is what lets
    the rest of the harness (evaluators, reporting) stay provider-agnostic.
    """

    name: str = "base"

    @abstractmethod
    def generate(self, case: GoldenCase) -> str:
        """Return the model's output text for the given golden case's prompt."""
        raise NotImplementedError
