from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from rapidfuzz import fuzz, process

from app.standards.schema import Ruleset


@dataclass(frozen=True)
class Candidate:
    key: str
    label: str
    class_code: str
    class_name: str
    class_confidence: float
    function_number: int | None
    function_confidence: float
    parent_key: str | None
    parent_confidence: float
    evidence: str


class RuleInferenceProvider:
    """Produces reviewable semantic candidates, never RDS strings."""

    version = "rules-1.0"

    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset
        self.aliases = {alias.lower(): code for code, definition in ruleset.classes.items() for alias in definition.aliases}

    def infer(self, text: str) -> list[dict]:
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", text) if item.strip()]
        current_function: int | None = None
        found: list[Candidate] = []
        for sentence in sentences:
            function_match = re.search(r"(?:joint|function)\s*(\d+)|\bM(\d+)\b", sentence, re.I)
            if function_match:
                current_function = int(next(group for group in function_match.groups() if group))
            lowered = sentence.lower()
            scan_text = re.split(r"\b(?:is\s+)?(?:mounted|integrated|contained)\b", lowered, maxsplit=1)[0]
            matches: list[tuple[int, str, str]] = []
            for alias, code in self.aliases.items():
                for match in re.finditer(rf"\b{re.escape(alias)}s?\b", scan_text):
                    matches.append((match.start(), alias, code))
            best_by_class: dict[str, tuple[int, str, str]] = {}
            for match in matches:
                current = best_by_class.get(match[2])
                if current is None or (len(match[1]), match[0]) > (len(current[1]), current[0]):
                    best_by_class[match[2]] = match
            for _, alias, code in sorted(best_by_class.values()):
                if any(item.label.lower() == alias and item.evidence == sentence for item in found):
                    continue
                label = alias.title()
                key = f"candidate-{len(found) + 1}"
                parent_key = None
                parent_confidence = 0.0
                if re.search(r"(?:mounted|integrated|inside|directly)\s+(?:directly\s+)?(?:on|in|inside)?", lowered):
                    earlier = [item for item in found if item.evidence != sentence or item.label.lower() != alias]
                    if earlier:
                        parent_key, parent_confidence = earlier[-1].key, 0.78
                found.append(Candidate(key, label, code, self.ruleset.classes[code].name, 0.97, current_function, 0.96 if current_function is not None else 0.0, parent_key, parent_confidence, sentence))
        if not found:
            best = process.extractOne(text.lower(), self.aliases.keys(), scorer=fuzz.token_set_ratio)
            if best and best[1] >= 55:
                alias, score, _ = best
                code = self.aliases[alias]
                found.append(Candidate("candidate-1", alias.title(), code, self.ruleset.classes[code].name, score / 100, current_function, 0.5 if current_function else 0.0, None, 0.0, text))
        return [asdict(item) for item in found]
