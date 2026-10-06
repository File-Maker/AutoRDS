from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.models import CompiledDesignation, ProjectSnapshot, Severity, ValidationIssue
from app.standards.schema import Ruleset

from .allocator import SequenceAllocator
from .renderer import render_component_path
from .validator import validate_snapshot


@dataclass(frozen=True, slots=True)
class CompileResult:
    snapshot: ProjectSnapshot
    designations: tuple[CompiledDesignation, ...]
    issues: tuple[ValidationIssue, ...]

    def by_component(self, component_id: UUID) -> CompiledDesignation | None:
        return next((item for item in self.designations if item.component_id == component_id), None)


class RDSCompiler:
    """Pure deterministic compiler. Input is structured domain data only."""

    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset

    def compile(self, snapshot: ProjectSnapshot) -> CompileResult:
        allocated, _ = SequenceAllocator(self.ruleset).allocate(snapshot)
        issues = validate_snapshot(allocated, self.ruleset)
        components = allocated.component_map
        functions = allocated.function_map
        compiled: list[CompiledDesignation] = []

        def ancestry(component_id: UUID) -> list:
            chain = []
            seen: set[UUID] = set()
            parent_id = components[component_id].parent_component_id
            while parent_id in components and parent_id not in seen:
                seen.add(parent_id)
                parent = components[parent_id]
                chain.append(parent)
                parent_id = parent.parent_component_id
            return list(reversed(chain))

        for component in sorted(components.values(), key=lambda item: str(item.id)):
            item_issues = tuple(issue for issue in issues if issue.entity_id in {None, component.id})
            function = functions.get(component.function_id) if component.function_id else None
            if function and component.class_code in self.ruleset.classes:
                designation, tokens = render_component_path(component, ancestry(component.id), function, self.ruleset)
            else:
                designation, tokens = "", ()
            compiled.append(
                CompiledDesignation(
                    component.id,
                    designation,
                    bool(designation) and not any(issue.severity == Severity.ERROR for issue in item_issues),
                    tokens,
                    item_issues,
                )
            )

        counts: dict[str, list[UUID]] = {}
        for item in compiled:
            if item.designation:
                counts.setdefault(item.designation, []).append(item.component_id)
        duplicate_ids = {component_id for ids in counts.values() if len(ids) > 1 for component_id in ids}
        if duplicate_ids:
            extra = [ValidationIssue("DUPLICATE_DESIGNATION", Severity.ERROR, item, "Compiled designation is duplicated.", "Resolve conflicting class/number allocations.") for item in duplicate_ids]
            issues.extend(extra)
            compiled = [
                CompiledDesignation(item.component_id, item.designation, False, item.tokens, item.issues + tuple(issue for issue in extra if issue.entity_id == item.component_id)) if item.component_id in duplicate_ids else item
                for item in compiled
            ]
        return CompileResult(allocated, tuple(compiled), tuple(issues))
