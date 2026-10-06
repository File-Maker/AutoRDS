from __future__ import annotations

from collections import Counter
from uuid import UUID

from app.domain.models import ProjectSnapshot, RelationType, Severity, ValidationIssue
from app.standards.schema import Ruleset


class ProjectValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


def _issue(code: str, severity: Severity, entity_id: UUID | None, message: str, fix: str) -> ValidationIssue:
    return ValidationIssue(code, severity, entity_id, message, fix)


def validate_snapshot(snapshot: ProjectSnapshot, ruleset: Ruleset) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    functions = snapshot.function_map
    components = snapshot.component_map

    function_numbers = Counter(fn.number for fn in functions.values())
    for fn in functions.values():
        if fn.project_id != snapshot.project.id:
            issues.append(_issue("CROSS_PROJECT_REFERENCE", Severity.ERROR, fn.id, "Function belongs to another project.", "Move or recreate the function in this project."))
        if function_numbers[fn.number] > 1:
            issues.append(_issue("DUPLICATE_FUNCTION", Severity.ERROR, fn.id, f"Function M{fn.number} is duplicated.", "Choose a unique function number."))

    for component in components.values():
        if component.project_id != snapshot.project.id:
            issues.append(_issue("CROSS_PROJECT_REFERENCE", Severity.ERROR, component.id, "Component belongs to another project.", "Move or recreate the component in this project."))
        if component.function_id is None:
            issues.append(_issue("MISSING_FUNCTION", Severity.ERROR, component.id, "Component has no assigned function.", "Assign a function before committing."))
        elif component.function_id not in functions:
            issues.append(_issue("BROKEN_FUNCTION_REFERENCE", Severity.ERROR, component.id, "Assigned function does not exist.", "Choose an existing function."))
        if component.class_code.upper() not in ruleset.classes:
            issues.append(_issue("UNKNOWN_CLASS", Severity.ERROR, component.id, f"Unknown class code {component.class_code!r}.", "Select a class supplied by the active ruleset."))
        if component.class_code != component.class_code.upper() or not component.class_code.isalpha():
            issues.append(_issue("INVALID_CLASS", Severity.ERROR, component.id, "Class code must contain uppercase letters only.", "Normalize the class code."))
        parent_id = component.parent_component_id
        if parent_id:
            if parent_id == component.id:
                issues.append(_issue("CYCLIC_CONTAINMENT", Severity.ERROR, component.id, "A component cannot contain itself.", "Remove the parent assignment."))
            elif parent_id not in components:
                issues.append(_issue("MISSING_PARENT", Severity.ERROR, component.id, "Parent component does not exist.", "Choose an existing component or no parent."))
            else:
                parent = components[parent_id]
                if parent.project_id != component.project_id:
                    issues.append(_issue("INVALID_PARENT", Severity.ERROR, component.id, "Parent belongs to another project.", "Choose a parent from the same project."))
                if parent.function_id != component.function_id:
                    issues.append(_issue("AMBIGUOUS_PARENT", Severity.WARNING, component.id, "Parent and child are assigned to different functions.", "Align their functions or confirm the intended allocation."))

    # DFS containment cycle detection.
    state: dict[UUID, int] = {}

    def visit(component_id: UUID, path: list[UUID]) -> None:
        if state.get(component_id) == 1:
            cycle = path[path.index(component_id) :] if component_id in path else [component_id]
            for item in cycle:
                issues.append(_issue("CYCLIC_CONTAINMENT", Severity.ERROR, item, "Circular containment is not allowed.", "Move one component outside the cycle."))
            return
        if state.get(component_id) == 2:
            return
        state[component_id] = 1
        parent = components[component_id].parent_component_id
        if parent in components:
            visit(parent, [*path, component_id])
        state[component_id] = 2

    for component_id in components:
        visit(component_id, [])

    allocation_keys = Counter((item.scope_id, item.class_code, item.assigned_number) for item in snapshot.allocations)
    for allocation in snapshot.allocations:
        if allocation_keys[(allocation.scope_id, allocation.class_code, allocation.assigned_number)] > 1:
            issues.append(_issue("DUPLICATE_ALLOCATED_NUMBER", Severity.ERROR, allocation.component_id, "Allocated number is already used in this scope.", "Allocate a new stable sequence number."))

    allowed = set(RelationType)
    for relation in snapshot.relations:
        if relation.deleted:
            continue
        if relation.project_id != snapshot.project.id:
            issues.append(_issue("CROSS_PROJECT_REFERENCE", Severity.ERROR, relation.id, "Relation belongs to another project.", "Recreate the relation in this project."))
        if relation.source_component_id == relation.target_component_id:
            issues.append(_issue("SELF_RELATION", Severity.ERROR, relation.id, "A semantic relation cannot target itself.", "Choose a different target."))
        if relation.source_component_id not in components or relation.target_component_id not in components:
            issues.append(_issue("INVALID_RELATION", Severity.ERROR, relation.id, "Relation endpoint is missing.", "Choose existing source and target components."))
        if relation.relation_type not in allowed:
            issues.append(_issue("INVALID_RELATION", Severity.ERROR, relation.id, "Unsupported relation type.", "Select a supported semantic relation."))
    return list({(item.code, item.entity_id, item.message): item for item in issues}.values())


def assert_valid(snapshot: ProjectSnapshot, ruleset: Ruleset) -> None:
    errors = [issue for issue in validate_snapshot(snapshot, ruleset) if issue.severity == Severity.ERROR]
    if errors:
        raise ProjectValidationError(errors)
