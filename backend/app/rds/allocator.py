from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from uuid import UUID

from app.domain.models import Component, ProjectSnapshot, SequenceAllocation
from app.standards.schema import Ruleset


def allocation_scope(component: Component) -> str:
    owner = component.parent_component_id or component.function_id
    return f"{component.project_id}:{owner or 'unassigned'}"


class SequenceAllocator:
    """Allocates stable numbers centrally; historical allocations reserve their numbers."""

    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset

    def allocate(self, snapshot: ProjectSnapshot) -> tuple[ProjectSnapshot, tuple[SequenceAllocation, ...]]:
        allocations = list(snapshot.allocations)
        by_component: dict[UUID, SequenceAllocation] = {item.component_id: item for item in allocations if item.active}
        used: dict[tuple[str, str], set[int]] = defaultdict(set)
        for item in allocations:
            used[(item.scope_id, item.class_code)].add(item.assigned_number)

        allocated_components: list[Component] = []
        for component in sorted(snapshot.components, key=lambda item: str(item.id)):
            existing = by_component.get(component.id)
            scope = allocation_scope(component)
            code = component.class_code.upper()
            # Moving or changing class creates a new current-scope allocation, while old numbers
            # stay reserved. This prevents unrelated surviving objects from being renamed.
            if existing and existing.scope_id == scope and existing.class_code == code:
                number = existing.assigned_number
            elif component.allocated_number and component.allocated_number not in used[(scope, code)]:
                number = component.allocated_number
                existing = SequenceAllocation(scope, code, component.id, number)
                allocations.append(existing)
                by_component[component.id] = existing
                used[(scope, code)].add(number)
            else:
                number = 1
                while number in used[(scope, code)]:
                    number += 1
                existing = SequenceAllocation(scope, code, component.id, number)
                allocations = [replace(item, active=False) if item.component_id == component.id and item.active else item for item in allocations]
                allocations.append(existing)
                by_component[component.id] = existing
                used[(scope, code)].add(number)
            allocated_components.append(replace(component, allocated_number=number))

        return replace(snapshot, components=tuple(allocated_components), allocations=tuple(allocations)), tuple(allocations)
