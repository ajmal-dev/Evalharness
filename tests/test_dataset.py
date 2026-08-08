import pytest

from eval_harness.dataset import load_dataset

DATASET_PATH = "data/golden_dataset.yaml"


def test_load_dataset_returns_all_cases():
    cases = load_dataset(DATASET_PATH)
    assert len(cases) == 15
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids)), "case ids must be unique"


def test_load_dataset_covers_expected_categories():
    cases = load_dataset(DATASET_PATH)
    categories = {c.category for c in cases}
    assert categories == {"qa", "classification", "summarization", "safety", "extraction"}


def test_load_dataset_covers_expected_eval_methods():
    cases = load_dataset(DATASET_PATH)
    methods = {c.eval_method for c in cases}
    assert methods == {"exact_match", "contains", "regex_match", "json_schema", "llm_judge"}


def test_load_dataset_missing_file_raises(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        load_dataset(str(missing))


def test_load_dataset_rejects_missing_required_config(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text(
        """
cases:
  - id: bad-001
    category: qa
    prompt: "hello"
    mock_response: "hi"
    eval_method: exact_match
    eval_config: {}
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="expected"):
        load_dataset(str(bad_file))


def test_load_dataset_rejects_duplicate_ids(tmp_path):
    dup_file = tmp_path / "dup.yaml"
    dup_file.write_text(
        """
cases:
  - id: dup-001
    category: qa
    prompt: "hello"
    mock_response: "hi"
    eval_method: contains
    eval_config: {all_of: ["hi"]}
  - id: dup-001
    category: qa
    prompt: "hello again"
    mock_response: "hi"
    eval_method: contains
    eval_config: {all_of: ["hi"]}
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate case id"):
        load_dataset(str(dup_file))
