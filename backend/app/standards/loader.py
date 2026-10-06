from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from .schema import Ruleset

BUILTIN = Path(__file__).with_name("builtin")


def load_ruleset(source: str | Path = "ee3_2026_27") -> Ruleset:
    path = Path(source)
    if not path.exists():
        path = BUILTIN / f"{source}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Ruleset not found: {source}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        vocabulary_path = path.with_name("ee3_vocabulary.yaml")
        if "classes" not in payload and vocabulary_path.exists():
            payload["classes"] = yaml.safe_load(vocabulary_path.read_text(encoding="utf-8"))["classes"]
        return Ruleset.model_validate(payload)
    except (yaml.YAMLError, ValidationError, TypeError, KeyError) as exc:
        raise ValueError(f"Invalid ruleset {path.name}: {exc}") from exc


class RulesetRegistry:
    @staticmethod
    @lru_cache(maxsize=32)
    def get(ruleset_id: str) -> Ruleset:
        return load_ruleset(ruleset_id)

    @staticmethod
    def list() -> list[Ruleset]:
        return [load_ruleset(path) for path in sorted(BUILTIN.glob("*.yaml")) if "vocabulary" not in path.name]
