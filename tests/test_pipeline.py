"""Tests for envoy_cli/pipeline.py"""
import pytest

from envoy_cli.pipeline import (
    PipelineError,
    PipelineResult,
    PipelineStep,
    run_pipeline,
)


# ---------------------------------------------------------------------------
# PipelineStep
# ---------------------------------------------------------------------------

class TestPipelineStep:
    def test_to_dict_contains_action(self):
        step = PipelineStep(action="set", params={"key": "A", "value": "1"})
        d = step.to_dict()
        assert d["action"] == "set"
        assert d["params"]["key"] == "A"

    def test_from_dict_round_trip(self):
        original = PipelineStep(action="delete", params={"key": "X"})
        restored = PipelineStep.from_dict(original.to_dict())
        assert restored.action == original.action
        assert restored.params == original.params

    def test_from_dict_missing_action_raises(self):
        with pytest.raises(PipelineError, match="action"):
            PipelineStep.from_dict({"params": {}})

    def test_from_dict_defaults_params_to_empty(self):
        step = PipelineStep.from_dict({"action": "set"})
        assert step.params == {}


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------

class TestPipelineResult:
    def test_has_errors_false_when_empty(self):
        assert not PipelineResult().has_errors

    def test_has_errors_true_when_errors_present(self):
        r = PipelineResult(errors=["boom"])
        assert r.has_errors

    def test_summary_format(self):
        r = PipelineResult(applied=["a"], skipped=["b"], errors=["c", "d"])
        assert r.summary() == "1 applied, 1 skipped, 2 errors"


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------

def _secrets(**kw):
    return dict(kw)


class TestRunPipeline:
    def test_set_adds_key(self):
        secrets = _secrets()
        run_pipeline(secrets, [PipelineStep("set", {"key": "FOO", "value": "bar"})])
        assert secrets["FOO"] == "bar"

    def test_set_overwrites_existing(self):
        secrets = _secrets(FOO="old")
        run_pipeline(secrets, [PipelineStep("set", {"key": "FOO", "value": "new"})])
        assert secrets["FOO"] == "new"

    def test_delete_removes_key(self):
        secrets = _secrets(FOO="bar")
        run_pipeline(secrets, [PipelineStep("delete", {"key": "FOO"})])
        assert "FOO" not in secrets

    def test_delete_missing_key_is_skipped(self):
        secrets = _secrets()
        result = run_pipeline(secrets, [PipelineStep("delete", {"key": "GHOST"})])
        assert "delete:GHOST" in result.skipped

    def test_rename_moves_value(self):
        secrets = _secrets(OLD="val")
        run_pipeline(secrets, [PipelineStep("rename", {"src": "OLD", "dst": "NEW"})])
        assert secrets.get("NEW") == "val"
        assert "OLD" not in secrets

    def test_rename_missing_src_records_error(self):
        secrets = _secrets()
        result = run_pipeline(secrets, [PipelineStep("rename", {"src": "X", "dst": "Y"})])
        assert result.has_errors

    def test_copy_keeps_src(self):
        secrets = _secrets(SRC="v")
        run_pipeline(secrets, [PipelineStep("copy", {"src": "SRC", "dst": "DST"})])
        assert secrets["SRC"] == "v"
        assert secrets["DST"] == "v"

    def test_unknown_action_records_error(self):
        secrets = _secrets()
        result = run_pipeline(secrets, [PipelineStep("explode", {})])
        assert result.has_errors
        assert any("explode" in e for e in result.errors)

    def test_stop_on_error_raises(self):
        secrets = _secrets()
        with pytest.raises(PipelineError):
            run_pipeline(
                secrets,
                [PipelineStep("rename", {"src": "MISSING", "dst": "X"})],
                stop_on_error=True,
            )

    def test_multiple_steps_applied_in_order(self):
        secrets = _secrets(A="1")
        run_pipeline(
            secrets,
            [
                PipelineStep("set", {"key": "B", "value": "2"}),
                PipelineStep("rename", {"src": "A", "dst": "C"}),
            ],
        )
        assert secrets == {"B": "2", "C": "1"}

    def test_applied_list_tracks_steps(self):
        secrets = _secrets(K="v")
        result = run_pipeline(secrets, [PipelineStep("set", {"key": "K", "value": "x"})])
        assert "set:K" in result.applied
