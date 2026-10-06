from __future__ import annotations

from collections import defaultdict, deque
from uuid import UUID

from app.domain.models import ProjectSnapshot


class DependencyGraph:
    """Tracks designation dependencies without knowing how designations are rendered."""

    def __init__(self, snapshot: ProjectSnapshot) -> None:
        self.children: dict[UUID, set[UUID]] = defaultdict(set)
        self.function_members: dict[UUID, set[UUID]] = defaultdict(set)
        for component in snapshot.components:
            if component.deleted:
                continue
            if component.parent_component_id:
                self.children[component.parent_component_id].add(component.id)
            if component.function_id:
                self.function_members[component.function_id].add(component.id)

    def descendants(self, component_id: UUID) -> set[UUID]:
        found: set[UUID] = set()
        queue = deque([component_id])
        while queue:
            current = queue.popleft()
            for child in self.children.get(current, ()):
                if child not in found:
                    found.add(child)
                    queue.append(child)
        return found

    def affected_by_component(self, component_id: UUID) -> set[UUID]:
        return {component_id, *self.descendants(component_id)}

    def affected_by_function(self, function_id: UUID) -> set[UUID]:
        affected: set[UUID] = set()
        for component_id in self.function_members.get(function_id, ()):
            affected.update(self.affected_by_component(component_id))
        return affected
