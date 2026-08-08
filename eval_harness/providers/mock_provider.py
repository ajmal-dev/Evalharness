"""Offline provider for demos and CI."""

import random
import time

from eval_harness.models import GoldenCase
from eval_harness.providers.base import Provider


class MockProvider(Provider):
    """Returns each case's pre-recorded `mock_response` instead of calling a
    real model. Deterministic and free — this is what makes the harness
    runnable by anyone with no API key and no network access.
    """

    name = "mock"

    def generate(self, case: GoldenCase) -> str:
        # Simulated latency so timing data in the report looks realistic.
        time.sleep(random.uniform(0.02, 0.08))
        return case.mock_response
