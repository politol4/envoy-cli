"""Tests for envoy_cli.dependency."""
import pytest

from envoy_cli.dependency import (
    DependencyError,
    add_dependency,
    find_dependents,
    get_dependencies,
    remove_dependency,
)


def _base() -> dict:
    return {"DB_URL": "postgres://localhost", "DB_PASS": "secret", "API_KEY": "abc"}


class TestAddDependency:
    def test_meta_key_added(self):
        result = add_dependency(_base(), "DB_URL", "DB_PASS")
        assert "__dep__.DB_URL" in result

    def test_dependency_value_stored(self):
        result = add_dependency(_base(), "DB_URL", "DB_PASS")
        assert "DB_PASS" in result["__dep__.DB_URL"]

    def test_original_secrets_unchanged(self):
        base = _base()
        add_dependency(base, "DB_URL", "DB_PASS")
        assert "__dep__.DB_URL" not in base

    def test_multiple_deps_stored_sorted(self):
        s = add_dependency(_base(), "DB_URL", "DB_PASS")
        s = add_dependency(s, "DB_URL", "API_KEY")
        deps = get_dependencies(s, "DB_URL")
        assert deps == sorted(deps)
        assert len(deps) == 2

    def test_duplicate_dep_not_added_twice(self):
        s = add_dependency(_base(), "DB_URL", "DB_PASS")
        s = add_dependency(s, "DB_URL", "DB_PASS")
        assert get_dependencies(s, "DB_URL").count("DB_PASS") == 1

    def test_missing_key_raises(self):
        with pytest.raises(DependencyError, match="Key not found"):
            add_dependency(_base(), "MISSING", "DB_PASS")

    def test_missing_dep_key_raises(self):
        with pytest.raises(DependencyError, match="Dependency key not found"):
            add_dependency(_base(), "DB_URL", "MISSING")

    def test_self_dependency_raises(self):
        with pytest.raises(DependencyError, match="cannot depend on itself"):
            add_dependency(_base(), "DB_URL", "DB_URL")


class TestRemoveDependency:
    def _with_dep(self):
        return add_dependency(_base(), "DB_URL", "DB_PASS")

    def test_removes_dependency(self):
        s = remove_dependency(self._with_dep(), "DB_URL", "DB_PASS")
        assert get_dependencies(s, "DB_URL") == []

    def test_meta_key_cleaned_up_when_empty(self):
        s = remove_dependency(self._with_dep(), "DB_URL", "DB_PASS")
        assert "__dep__.DB_URL" not in s

    def test_non_existent_dep_raises(self):
        with pytest.raises(DependencyError, match="does not depend on"):
            remove_dependency(self._with_dep(), "DB_URL", "API_KEY")


class TestGetDependencies:
    def test_returns_empty_for_unknown_key(self):
        assert get_dependencies(_base(), "DB_URL") == []

    def test_returns_list_of_deps(self):
        s = add_dependency(_base(), "DB_URL", "DB_PASS")
        assert get_dependencies(s, "DB_URL") == ["DB_PASS"]


class TestFindDependents:
    def test_finds_dependent_key(self):
        s = add_dependency(_base(), "DB_URL", "DB_PASS")
        dependents = find_dependents(s, "DB_PASS")
        assert "DB_URL" in dependents

    def test_no_dependents_returns_empty(self):
        assert find_dependents(_base(), "API_KEY") == []

    def test_multiple_dependents_returned_sorted(self):
        s = add_dependency(_base(), "DB_URL", "API_KEY")
        s = add_dependency(s, "DB_PASS", "API_KEY")
        dependents = find_dependents(s, "API_KEY")
        assert dependents == sorted(dependents)
        assert len(dependents) == 2
