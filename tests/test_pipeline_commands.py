"""Tests for envoy_cli/pipeline_commands.py"""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envoy_cli.pipeline_commands import cmd_pipeline_run, cmd_pipeline_validate
from envoy_cli.pipeline import PipelineError


def _make_args(**kw):
    args = MagicMock()
    args.vault_dir = kw.get("vault_dir", "/tmp")
    args.passphrase = kw.get("passphrase", "secret")
    args.env = kw.get("env", "local")
    args.stop_on_error = kw.get("stop_on_error", False)
    args.file = kw.get("file", "")
    return args


def _write_pipeline(steps: list, tmp_dir: str) -> str:
    path = os.path.join(tmp_dir, "pipeline.json")
    Path(path).write_text(json.dumps(steps), encoding="utf-8")
    return path


def _make_manager(secrets: dict):
    vault = MagicMock()
    vault.all.return_value = dict(secrets)
    vault.set = MagicMock()

    manager = MagicMock()
    manager._load_vault.return_value = vault
    manager._save_vault = MagicMock()
    return manager, vault


class TestCmdPipelineValidate:
    def test_valid_file_returns_valid_message(self, tmp_path):
        steps = [{"action": "set", "params": {"key": "A", "value": "1"}}]
        path = str(tmp_path / "p.json")
        Path(path).write_text(json.dumps(steps))
        args = _make_args(file=path)
        result = cmd_pipeline_validate(args)
        assert "valid" in result.lower()
        assert "1 step" in result

    def test_invalid_action_reported(self, tmp_path):
        steps = [{"action": "explode", "params": {}}]
        path = str(tmp_path / "p.json")
        Path(path).write_text(json.dumps(steps))
        args = _make_args(file=path)
        result = cmd_pipeline_validate(args)
        assert "failed" in result.lower()
        assert "explode" in result

    def test_missing_file_returns_error_string(self, tmp_path):
        args = _make_args(file=str(tmp_path / "nonexistent.json"))
        result = cmd_pipeline_validate(args)
        assert "Invalid pipeline" in result

    def test_non_array_json_returns_error(self, tmp_path):
        path = str(tmp_path / "bad.json")
        Path(path).write_text(json.dumps({"action": "set"}))
        args = _make_args(file=path)
        result = cmd_pipeline_validate(args)
        assert "Invalid pipeline" in result


class TestCmdPipelineRun:
    def test_run_applies_set_step(self, tmp_path):
        steps = [{"action": "set", "params": {"key": "FOO", "value": "bar"}}]
        path = _write_pipeline(steps, str(tmp_path))
        args = _make_args(file=path)
        manager, vault = _make_manager({})

        with patch("envoy_cli.pipeline_commands._make_manager", return_value=manager):
            result = cmd_pipeline_run(args)

        assert "1 applied" in result
        vault.set.assert_called_once_with("FOO", "bar")

    def test_run_returns_summary_string(self, tmp_path):
        steps = [
            {"action": "set", "params": {"key": "A", "value": "1"}},
            {"action": "delete", "params": {"key": "GHOST"}},
        ]
        path = _write_pipeline(steps, str(tmp_path))
        args = _make_args(file=path)
        manager, _vault = _make_manager({})

        with patch("envoy_cli.pipeline_commands._make_manager", return_value=manager):
            result = cmd_pipeline_run(args)

        assert "Pipeline complete" in result
        assert "1 applied" in result
        assert "1 skipped" in result

    def test_run_saves_vault_after_execution(self, tmp_path):
        steps = [{"action": "set", "params": {"key": "X", "value": "y"}}]
        path = _write_pipeline(steps, str(tmp_path))
        args = _make_args(file=path, env="staging")
        manager, _vault = _make_manager({})

        with patch("envoy_cli.pipeline_commands._make_manager", return_value=manager):
            cmd_pipeline_run(args)

        manager._save_vault.assert_called_once()
