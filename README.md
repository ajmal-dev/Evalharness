# LLM Eval Harness

[![CI](https://github.com/Shezapk/llm-eval-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/Shezapk/llm-eval-harness/actions/workflows/ci.yml)

A self-contained **LLM output evaluation harness**: define a golden dataset of prompts + expected behavior, run it against an LLM provider, score every output with pluggable evaluators (including an LLM-as-judge style rubric grader), and get a pass/fail report you can read locally or gate a CI pipeline on.

Runs fully offline out of the box (a mock provider, zero setup, zero API key) and also supports a real, live call to the Anthropic Claude API as a second provider — so it's a genuine evaluation tool, not just a mock-shaped demo.

## Quickstart

```bash
pip install -r requirements.txt

python -m eval_harness.cli run
```

This runs the 15-case golden dataset (`data/golden_dataset.yaml`) against the default `mock` provider and writes:

- `reports/results.json` — raw structured results
- `reports/report.html` — a readable dashboard (open it in a browser)

It also prints a summary table to the terminal.

### Running against a real, live model

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or: ant auth login
python -m eval_harness.cli run --provider anthropic
```

This calls the real Anthropic Claude API (`claude-opus-5`) for every prompt in the dataset instead of using the pre-recorded mock responses. If no credential is found, `AnthropicProvider` fails immediately with a clear message rather than failing mid-run.

### CI gating

```bash
python -m eval_harness.cli run --fail-under 0.8
```

Exits non-zero if the pass rate drops below the threshold — wire this into a CI step to block a deploy/prompt-change on an eval regression.

## How LLM evaluation actually works here

There are two distinct roles, and it's worth being explicit about which is which:

1. **Provider** — the model under test. `Provider.generate(prompt) -> output`. This is the only place a live API call happens.
2. **Evaluator** — scores that output. Some evaluators are pure code (no LLM involved at all); one (`llm_judge`) simulates what a real LLM-as-judge grader would do.

```
golden_case.prompt
      │
      ▼
Provider.generate()  ──►  model output          (mock or a real, live Anthropic call)
      │
      ▼
Evaluator.evaluate(case, output)  ──►  pass/fail + score + reason
```

## Architecture

```
eval_harness/
├── models.py           # GoldenCase, EvalResult, CaseResult, RunSummary
├── dataset.py           # loads + validates data/golden_dataset.yaml
├── runner.py            # orchestrates: dataset -> provider -> evaluator -> summary
├── report.py            # writes results.json + report.html, prints terminal summary
├── cli.py                # `python -m eval_harness.cli run ...`
├── providers/
│   ├── base.py           # Provider ABC: generate(case) -> str
│   ├── mock_provider.py  # returns each case's pre-recorded mock_response
│   └── anthropic_provider.py  # real call to the live Claude API
└── evaluators/
    ├── base.py           # Evaluator ABC: evaluate(case, output) -> EvalResult
    ├── exact_match.py
    ├── contains.py
    ├── regex_match.py
    ├── json_schema.py
    └── llm_judge.py      # MockJudge: simulated rubric-based grading
```

## Eval methods

Each golden case picks one `eval_method` and configures it via `eval_config`:

| `eval_method` | Needs an LLM? | `eval_config` fields | Use for |
|---|---|---|---|
| `exact_match` | No | `expected`, `case_sensitive` (default `true`) | Classification labels, single correct answers |
| `contains` | No | `all_of`, `any_of`, `case_sensitive` (default `false`) | QA where multiple phrasings are acceptable |
| `regex_match` | No | `pattern`, `expected_match` (default `true`) | Refusal detection, format checks, catching over-refusal (`expected_match: false`) |
| `json_schema` | No | `schema` (JSON Schema) | Structured extraction |
| `llm_judge` | Simulated | `criteria: [{name, keywords, weight}]`, `min_score` (default `0.7`) | Open-ended tasks (summarization, tone) with no single correct string |

`llm_judge` currently ships as `MockJudge` — it scores a rubric by checking whether each criterion's keywords appear in the output. This keeps the whole harness free and offline. See `eval_harness/evaluators/llm_judge.py` for exactly how to swap in a real LLM grading call while keeping the same `eval_config` shape.

## Extending the harness

**Add a golden case** — append an entry to `data/golden_dataset.yaml`:

```yaml
- id: qa-004
  category: qa
  tags: [qa]
  prompt: "What is the boiling point of water at sea level in Celsius?"
  mock_response: "100 degrees Celsius."
  eval_method: contains
  eval_config:
    all_of: ["100"]
```

**Add a new provider** (e.g. OpenAI, Gemini, a local Ollama model) — implement `Provider.generate()` in a new file under `providers/`, then register it in `runner.PROVIDERS`:

```python
# eval_harness/providers/openai_provider.py
class OpenAIProvider(Provider):
    name = "openai"
    def generate(self, case: GoldenCase) -> str: ...
```

```python
# eval_harness/runner.py
PROVIDERS = {
    "mock": MockProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}
```

Also add `"openai"` to the `--provider` choices in `cli.py`.

**Add a new evaluator** — implement `Evaluator.evaluate()` in a new file under `evaluators/`, then register it in `runner.EVALUATORS` under a new `eval_method` name.

**Swap the mock judge for a real LLM judge** — implement a new `Evaluator` whose `evaluate()` sends the output + rubric to an LLM (e.g. via `AnthropicProvider`) with a grading prompt, parses a score back out, and register it under the `"llm_judge"` key in `runner.EVALUATORS` in place of `MockJudge`. The `eval_config` shape (`criteria` + `min_score`) doesn't need to change.

## Testing

```bash
pytest
```

Covers dataset loading/validation, every evaluator's pass and fail paths, end-to-end orchestration with the mock provider, and the Anthropic provider's credential check + request shape (mocked — no real network call, no API key needed to run the suite).

## Continuous Integration

`.github/workflows/ci.yml` runs on every push/PR to `main`: installs dependencies, runs `pytest`, then runs the golden dataset against the mock provider with `--fail-under 0.6` — so the eval gate demonstrated in this README is actually enforced in CI, not just described. The HTML/JSON report is uploaded as a build artifact on every run.
