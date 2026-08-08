from eval_harness.runner import run_eval

DATASET_PATH = "data/golden_dataset.yaml"


def test_run_eval_with_mock_provider_produces_full_summary():
    summary = run_eval(DATASET_PATH, "mock")

    assert summary.provider_name == "mock"
    assert summary.total == 15
    assert summary.passed + summary.failed == summary.total
    assert 0.0 <= summary.pass_rate <= 1.0

    # The dataset intentionally mixes passes and failures so the demo report
    # shows the harness actually catching regressions, not an all-green run.
    assert summary.passed > 0
    assert summary.failed > 0

    assert set(summary.by_category) == {
        "qa",
        "classification",
        "summarization",
        "safety",
        "extraction",
    }
    for counts in summary.by_category.values():
        assert counts["passed"] + counts["failed"] > 0

    assert len(summary.case_results) == summary.total
    for result in summary.case_results:
        assert result.latency_ms >= 0
        assert isinstance(result.eval_result.passed, bool)


def test_run_eval_rejects_unknown_provider():
    import pytest

    with pytest.raises(ValueError, match="Unknown provider"):
        run_eval(DATASET_PATH, "does-not-exist")
