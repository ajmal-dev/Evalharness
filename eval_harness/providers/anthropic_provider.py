"""Real provider: calls the live Anthropic Claude API."""

import os

from eval_harness.models import GoldenCase
from eval_harness.providers.base import Provider

_MODEL = "claude-opus-5"


def _has_resolvable_credential() -> bool:
    """Best-effort check for whether the Anthropic SDK will find credentials.

    Mirrors the SDK's own resolution order closely enough to fail fast at
    provider construction time rather than on the first API call: an env var,
    or an `ant auth login` profile directory.
    """
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True

    candidates = []
    config_dir = os.environ.get("ANTHROPIC_CONFIG_DIR")
    if config_dir:
        candidates.append(config_dir)
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(os.path.join(appdata, "Anthropic"))
    candidates.append(os.path.join(os.path.expanduser("~"), ".config", "anthropic"))

    return any(os.path.isdir(path) for path in candidates)


class AnthropicProvider(Provider):
    """Calls the real Anthropic Claude API (model claude-opus-5) for each
    golden case's prompt.

    Requires ANTHROPIC_API_KEY (or an `ant auth login` profile) to be
    resolvable. Fails fast with a clear error at construction time if no
    credential is found, instead of failing mid-run on the first request.
    """

    name = "anthropic"

    def __init__(self) -> None:
        if not _has_resolvable_credential():
            raise RuntimeError(
                "No Anthropic credentials found. Set the ANTHROPIC_API_KEY "
                "environment variable, or run `ant auth login`, before using "
                "--provider anthropic."
            )
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "The `anthropic` package is required for --provider anthropic. "
                "Install it with: pip install anthropic"
            ) from exc

        self._client = anthropic.Anthropic()

    def generate(self, case: GoldenCase) -> str:
        response = self._client.messages.create(
            model=_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": case.prompt}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )
