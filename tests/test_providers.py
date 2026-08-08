"""AnthropicProvider tests. These never make a real network call — the SDK
is faked out via sys.modules so the suite runs offline and without a key.
"""

import sys
import types

import pytest

from eval_harness.models import GoldenCase
from eval_harness.providers.anthropic_provider import AnthropicProvider


def test_anthropic_provider_requires_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_CONFIG_DIR", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr("os.path.isdir", lambda path: False)

    with pytest.raises(RuntimeError, match="No Anthropic credentials"):
        AnthropicProvider()


def test_anthropic_provider_generate_calls_sdk_with_expected_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class FakeBlock:
        type = "text"
        text = "hello from claude"

    class FakeResponse:
        content = [FakeBlock()]

    class FakeMessages:
        last_kwargs = None

        def create(self, **kwargs):
            FakeMessages.last_kwargs = kwargs
            return FakeResponse()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.messages = FakeMessages()

    fake_anthropic_module = types.ModuleType("anthropic")
    fake_anthropic_module.Anthropic = FakeClient
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic_module)

    provider = AnthropicProvider()
    case = GoldenCase(
        id="x",
        category="qa",
        prompt="hi",
        mock_response="",
        eval_method="contains",
        eval_config={"all_of": ["hi"]},
    )

    output = provider.generate(case)

    assert output == "hello from claude"
    assert FakeMessages.last_kwargs["model"] == "claude-opus-5"
    assert FakeMessages.last_kwargs["messages"] == [{"role": "user", "content": "hi"}]
