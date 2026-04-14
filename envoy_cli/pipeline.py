"""Pipeline: chain multiple vault operations in a single declarative run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class PipelineError(Exception):
    """Raised when a pipeline step fails."""


@dataclass
class PipelineStep:
    action: str          # set | delete | rename | copy
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "params": self.params}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineStep":
        if "action" not in data:
            raise PipelineError("Pipeline step missing 'action' field")
        return cls(action=data["action"], params=data.get("params", {}))


@dataclass
class PipelineResult:
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def summary(self) -> str:
        return (
            f"{len(self.applied)} applied, "
            f"{len(self.skipped)} skipped, "
            f"{len(self.errors)} errors"
        )


_VALID_ACTIONS = {"set", "delete", "rename", "copy"}


def run_pipeline(
    secrets: Dict[str, str],
    steps: List[PipelineStep],
    *,
    stop_on_error: bool = False,
) -> PipelineResult:
    """Apply *steps* to a mutable copy of *secrets* and return the result."""
    result = PipelineResult()
    data = dict(secrets)

    for step in steps:
        action = step.action
        if action not in _VALID_ACTIONS:
            msg = f"Unknown action '{action}'"
            result.errors.append(msg)
            if stop_on_error:
                raise PipelineError(msg)
            continue

        try:
            if action == "set":
                key = step.params["key"]
                data[key] = step.params["value"]
                result.applied.append(f"set:{key}")

            elif action == "delete":
                key = step.params["key"]
                if key not in data:
                    result.skipped.append(f"delete:{key}")
                else:
                    del data[key]
                    result.applied.append(f"delete:{key}")

            elif action == "rename":
                src, dst = step.params["src"], step.params["dst"]
                if src not in data:
                    raise PipelineError(f"rename: key '{src}' not found")
                data[dst] = data.pop(src)
                result.applied.append(f"rename:{src}->{dst}")

            elif action == "copy":
                src, dst = step.params["src"], step.params["dst"]
                if src not in data:
                    raise PipelineError(f"copy: key '{src}' not found")
                data[dst] = data[src]
                result.applied.append(f"copy:{src}->{dst}")

        except PipelineError as exc:
            result.errors.append(str(exc))
            if stop_on_error:
                raise
        except KeyError as exc:
            msg = f"Missing param {exc} for action '{action}'"
            result.errors.append(msg)
            if stop_on_error:
                raise PipelineError(msg) from exc

    # Write mutated secrets back in-place so callers see changes
    secrets.clear()
    secrets.update(data)
    return result
