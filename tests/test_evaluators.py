from eval_harness.evaluators.contains import ContainsEvaluator
from eval_harness.evaluators.exact_match import ExactMatchEvaluator
from eval_harness.evaluators.json_schema import JsonSchemaEvaluator
from eval_harness.evaluators.llm_judge import MockJudge
from eval_harness.evaluators.regex_match import RegexMatchEvaluator
from eval_harness.models import GoldenCase


def make_case(eval_method: str, eval_config: dict) -> GoldenCase:
    return GoldenCase(
        id="test-case",
        category="test",
        prompt="irrelevant for evaluator unit tests",
        mock_response="irrelevant",
        eval_method=eval_method,
        eval_config=eval_config,
    )


# ---- ExactMatchEvaluator ----

def test_exact_match_passes_on_identical_value():
    case = make_case("exact_match", {"expected": "positive"})
    result = ExactMatchEvaluator().evaluate(case, "positive")
    assert result.passed is True
    assert result.score == 1.0


def test_exact_match_fails_on_different_value():
    case = make_case("exact_match", {"expected": "positive"})
    result = ExactMatchEvaluator().evaluate(case, "negative")
    assert result.passed is False
    assert result.score == 0.0


def test_exact_match_case_insensitive_option():
    case = make_case("exact_match", {"expected": "Positive", "case_sensitive": False})
    result = ExactMatchEvaluator().evaluate(case, "positive")
    assert result.passed is True


# ---- ContainsEvaluator ----

def test_contains_passes_when_all_required_substrings_present():
    case = make_case("contains", {"all_of": ["Paris", "France"]})
    result = ContainsEvaluator().evaluate(case, "The capital of France is Paris.")
    assert result.passed is True
    assert result.score == 1.0


def test_contains_fails_when_a_required_substring_missing():
    case = make_case("contains", {"all_of": ["Jane Austen"]})
    result = ContainsEvaluator().evaluate(case, "Written by Charlotte Bronte.")
    assert result.passed is False
    assert result.score == 0.0


def test_contains_any_of_passes_with_one_match():
    case = make_case("contains", {"any_of": ["cat", "dog"]})
    result = ContainsEvaluator().evaluate(case, "I have a dog.")
    assert result.passed is True


# ---- RegexMatchEvaluator ----

def test_regex_match_passes_when_refusal_pattern_found():
    case = make_case("regex_match", {"pattern": "can't|cannot", "expected_match": True})
    result = RegexMatchEvaluator().evaluate(case, "I can't help with that.")
    assert result.passed is True


def test_regex_match_fails_when_refusal_pattern_missing_but_expected():
    case = make_case("regex_match", {"pattern": "can't|cannot", "expected_match": True})
    result = RegexMatchEvaluator().evaluate(case, "Sure, here's how...")
    assert result.passed is False


def test_regex_match_expected_match_false_catches_over_refusal():
    case = make_case("regex_match", {"pattern": "can't|cannot", "expected_match": False})
    result = RegexMatchEvaluator().evaluate(case, "I can't help with that.")
    assert result.passed is False


# ---- JsonSchemaEvaluator ----

SCHEMA = {
    "type": "object",
    "required": ["name", "email"],
    "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
}


def test_json_schema_passes_on_valid_matching_json():
    case = make_case("json_schema", {"schema": SCHEMA})
    result = JsonSchemaEvaluator().evaluate(
        case, '{"name": "John Smith", "email": "john@example.com"}'
    )
    assert result.passed is True


def test_json_schema_fails_on_invalid_json():
    case = make_case("json_schema", {"schema": SCHEMA})
    result = JsonSchemaEvaluator().evaluate(case, "not json at all")
    assert result.passed is False
    assert "not valid JSON" in result.reason


def test_json_schema_fails_on_schema_mismatch():
    case = make_case("json_schema", {"schema": SCHEMA})
    result = JsonSchemaEvaluator().evaluate(case, '{"name": "John Smith"}')
    assert result.passed is False


# ---- MockJudge ----

CRITERIA_CONFIG = {
    "min_score": 0.7,
    "criteria": [
        {"name": "mentions revenue", "keywords": ["revenue", "12%"], "weight": 1},
        {"name": "mentions stock", "keywords": ["stock", "shares"], "weight": 1},
    ],
}


def test_mock_judge_passes_when_criteria_satisfied():
    case = make_case("llm_judge", CRITERIA_CONFIG)
    result = MockJudge().evaluate(
        case, "Revenue was up 12% and the stock price rose."
    )
    assert result.passed is True
    assert result.score == 1.0


def test_mock_judge_fails_on_vague_output_missing_criteria():
    case = make_case("llm_judge", CRITERIA_CONFIG)
    result = MockJudge().evaluate(case, "The meeting covered various topics.")
    assert result.passed is False
    assert result.score == 0.0
