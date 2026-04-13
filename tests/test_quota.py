"""Tests for envoy_cli.quota."""

import pytest
from envoy_cli.quota import (
    QuotaConfig,
    QuotaError,
    DEFAULT_QUOTA,
    set_quota,
    get_quota,
    check_quota,
    remove_quota,
)


# ---------------------------------------------------------------------------
# QuotaConfig
# ---------------------------------------------------------------------------

class TestQuotaConfig:
    def test_to_dict_contains_required_fields(self):
        cfg = QuotaConfig(limit=100, env="staging")
        d = cfg.to_dict()
        assert d["limit"] == 100
        assert d["env"] == "staging"

    def test_from_dict_round_trip(self):
        cfg = QuotaConfig(limit=50, env="production")
        restored = QuotaConfig.from_dict(cfg.to_dict())
        assert restored.limit == cfg.limit
        assert restored.env == cfg.env

    def test_from_dict_missing_field_raises(self):
        with pytest.raises(QuotaError, match="Missing field"):
            QuotaConfig.from_dict({"limit": 10})


# ---------------------------------------------------------------------------
# set_quota / get_quota
# ---------------------------------------------------------------------------

class TestSetGetQuota:
    def test_meta_key_added(self):
        result = set_quota({}, limit=200, env="local")
        assert "__quota__" in result

    def test_original_secrets_unchanged(self):
        base = {"DB_URL": "postgres://localhost"}
        result = set_quota(base, limit=100, env="local")
        assert result["DB_URL"] == "postgres://localhost"

    def test_zero_limit_raises(self):
        with pytest.raises(QuotaError):
            set_quota({}, limit=0, env="local")

    def test_negative_limit_raises(self):
        with pytest.raises(QuotaError):
            set_quota({}, limit=-5, env="local")

    def test_get_returns_none_when_not_set(self):
        assert get_quota({}, env="local") is None

    def test_get_returns_config_when_set(self):
        secrets = set_quota({}, limit=75, env="staging")
        cfg = get_quota(secrets, env="staging")
        assert cfg is not None
        assert cfg.limit == 75

    def test_get_returns_none_for_different_env(self):
        secrets = set_quota({}, limit=75, env="staging")
        assert get_quota(secrets, env="production") is None


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

class TestCheckQuota:
    def test_no_error_when_under_limit(self):
        secrets = set_quota({"A": "1", "B": "2"}, limit=10, env="local")
        check_quota(secrets, env="local", adding=1)  # should not raise

    def test_raises_when_limit_exceeded(self):
        secrets = set_quota({"A": "1", "B": "2"}, limit=2, env="local")
        with pytest.raises(QuotaError, match="Quota exceeded"):
            check_quota(secrets, env="local", adding=1)

    def test_uses_default_quota_when_not_configured(self):
        # 1 secret, adding 1 — well under DEFAULT_QUOTA
        check_quota({"A": "1"}, env="local", adding=1)

    def test_meta_keys_excluded_from_count(self):
        secrets = set_quota({}, limit=1, env="local")
        # Only the __quota__ meta key exists; real count is 0
        check_quota(secrets, env="local", adding=1)  # should not raise


# ---------------------------------------------------------------------------
# remove_quota
# ---------------------------------------------------------------------------

class TestRemoveQuota:
    def test_meta_key_removed(self):
        secrets = set_quota({"X": "y"}, limit=10, env="local")
        result = remove_quota(secrets)
        assert "__quota__" not in result

    def test_other_keys_preserved(self):
        secrets = set_quota({"X": "y"}, limit=10, env="local")
        result = remove_quota(secrets)
        assert result["X"] == "y"

    def test_remove_on_empty_secrets_is_safe(self):
        result = remove_quota({})
        assert result == {}
