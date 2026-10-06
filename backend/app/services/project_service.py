from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    Component,
    FunctionNode,
    Project,
    ProjectSnapshot,
    Relation,
    RelationType,
    SequenceAllocation,
    Severity,
    SourceType,
)
from app.persistence.models import (
    ComponentModel,
    FunctionNodeModel,
    ProjectModel,
    RelationModel,
    RevisionModel,
    SequenceAllocationModel,
)
from app.rds.allocator import allocation_scope
from app.rds.compiler import CompileResult, RDSCompiler
from app.rds.dependency_graph import DependencyGraph
from app.rds.validator import ProjectValidationError
from app.standards.loader import RulesetRegistry


def _uuid(value: str | None) -> UUID | None:
    return UUID(value) if value else None


def _jsonable(value: Any) -> Any:
    if isinstance(value, (UUID, datetime)):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return value


def _dump(payload: dict[str, Any] | None) -> str | None:
    return json.dumps(payload, default=_jsonable, sort_keys=True) if payload is not None else None


class ProjectService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _project_model(self, project_id: UUID) -> ProjectModel:
        model = self.session.get(ProjectModel, str(project_id))
        if not model or model.deleted_at:
            raise LookupError("Project not found")
        return model

    @staticmethod
    def _model_dict(model: Any) -> dict[str, Any]:
        return {column.name: getattr(model, column.name) for column in model.__table__.columns}

    def _revision(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        reason: str,
    ) -> RevisionModel:
        revision = RevisionModel(
            id=str(uuid4()),
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            before_json=_dump(before),
            after_json=_dump(after),
            reason=reason,
        )
        self.session.add(revision)
        return revision

    def create_project(self, name: str, description: str = "", ruleset_id: str = "ee3_2026_27") -> dict[str, Any]:
        RulesetRegistry.get(ruleset_id)
        model = ProjectModel(id=str(uuid4()), name=name.strip(), description=description, ruleset_id=ruleset_id)
        if not model.name:
            raise ValueError("Project name is required")
        self.session.add(model)
        self.session.flush()
        self._revision(model.id, "project", model.id, "create", None, self._model_dict(model), "Create project")
        self.session.commit()
        return self.get_project(UUID(model.id))

    def list_projects(self) -> list[dict[str, Any]]:
        projects = self.session.scalars(select(ProjectModel).where(ProjectModel.deleted_at.is_(None)).order_by(ProjectModel.updated_at.desc())).all()
        return [{"id": item.id, "name": item.name, "description": item.description, "ruleset_id": item.ruleset_id, "updated_at": item.updated_at.isoformat()} for item in projects]

    def update_project(self, project_id: UUID, changes: dict[str, Any], reason: str = "Edit project") -> dict[str, Any]:
        model = self._project_model(project_id)
        before = self._model_dict(model)
        for field in ("name", "description"):
            if field in changes:
                setattr(model, field, changes[field])
        if "ruleset_id" in changes:
            RulesetRegistry.get(changes["ruleset_id"])
            model.ruleset_id = changes["ruleset_id"]
        self._revision(model.id, "project", model.id, "edit", before, self._model_dict(model), reason)
        self._validate_and_commit(project_id)
        return self.get_project(project_id)

    def delete_project(self, project_id: UUID) -> None:
        model = self._project_model(project_id)
        before = self._model_dict(model)
        model.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        self._revision(model.id, "project", model.id, "delete", before, self._model_dict(model), "Delete project")
        self.session.commit()

    def create_function(self, project_id: UUID, number: int, label: str, description: str = "", parent_id: UUID | None = None) -> dict[str, Any]:
        self._project_model(project_id)
        model = FunctionNodeModel(id=str(uuid4()), project_id=str(project_id), number=number, label=label, description=description, parent_id=str(parent_id) if parent_id else None)
        self.session.add(model)
        self.session.flush()
        self._revision(model.project_id, "function", model.id, "create", None, self._model_dict(model), "Create function")
        self._validate_and_commit(project_id)
        return self.get_project(project_id)

    def update_function(self, function_id: UUID, changes: dict[str, Any], reason: str = "Edit function") -> dict[str, Any]:
        model = self.session.get(FunctionNodeModel, str(function_id))
        if not model or model.deleted_at:
            raise LookupError("Function not found")
        before = self._model_dict(model)
        for field in ("number", "label", "description", "parent_id"):
            if field in changes:
                value = changes[field]
                setattr(model, field, str(value) if field == "parent_id" and value else value)
        self._revision(model.project_id, "function", model.id, "edit", before, self._model_dict(model), reason)
        self._validate_and_commit(UUID(model.project_id))
        return self.get_project(UUID(model.project_id))

    def delete_function(self, function_id: UUID) -> dict[str, Any]:
        model = self.session.get(FunctionNodeModel, str(function_id))
        if not model or model.deleted_at:
            raise LookupError("Function not found")
        before = self._model_dict(model)
        model.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        self._revision(model.project_id, "function", model.id, "delete", before, self._model_dict(model), "Delete function")
        self._validate_and_commit(UUID(model.project_id))
        return self.get_project(UUID(model.project_id))

    def _component(self, component_id: UUID, include_deleted: bool = False) -> ComponentModel:
        model = self.session.get(ComponentModel, str(component_id))
        if not model or (model.deleted_at and not include_deleted):
            raise LookupError("Component not found")
        return model

    def create_component(
        self,
        project_id: UUID,
        function_id: UUID,
        class_code: str,
        label: str,
        description: str = "",
        parent_component_id: UUID | None = None,
        source_type: str = "manual",
        source_query_id: UUID | None = None,
    ) -> dict[str, Any]:
        self._project_model(project_id)
        model = ComponentModel(
            id=str(uuid4()),
            project_id=str(project_id),
            function_id=str(function_id),
            parent_component_id=str(parent_component_id) if parent_component_id else None,
            class_code=class_code.upper(),
            label=label,
            description=description,
            source_type=source_type,
            source_query_id=str(source_query_id) if source_query_id else None,
        )
        self.session.add(model)
        self.session.flush()
        self._ensure_allocations(project_id)
        self._revision(model.project_id, "component", model.id, "create", None, self._model_dict(model), "Create component")
        self._validate_and_commit(project_id)
        return self.component_payload(UUID(model.id))

    def update_component(self, component_id: UUID, changes: dict[str, Any], reason: str = "Edit component") -> dict[str, Any]:
        model = self._component(component_id)
        project_id = UUID(model.project_id)
        before = self._model_dict(model)
        structural = {"function_id", "parent_component_id", "class_code"}
        for field in ("function_id", "parent_component_id", "class_code", "label", "description"):
            if field in changes:
                value = changes[field]
                if field.endswith("_id"):
                    value = str(value) if value else None
                if field == "class_code":
                    value = value.upper()
                setattr(model, field, value)
        operation = "move" if structural.intersection(changes) else "edit"
        self.session.flush()
        if structural.intersection(changes):
            self._ensure_allocations(project_id)
        affected = DependencyGraph(self.snapshot(project_id)).affected_by_component(component_id)
        self._revision(model.project_id, "component", model.id, operation, before, self._model_dict(model), f"{reason}; recompiled {len(affected)} dependent object(s)")
        self._validate_and_commit(project_id)
        return self.component_payload(component_id)

    def move_component(self, component_id: UUID, parent_component_id: UUID | None) -> dict[str, Any]:
        return self.update_component(component_id, {"parent_component_id": parent_component_id}, "Move component")

    def change_function(self, component_id: UUID, function_id: UUID) -> dict[str, Any]:
        return self.update_component(component_id, {"function_id": function_id}, "Change function")

    def change_parent(self, component_id: UUID, parent_component_id: UUID | None) -> dict[str, Any]:
        return self.move_component(component_id, parent_component_id)

    def change_class(self, component_id: UUID, class_code: str) -> dict[str, Any]:
        return self.update_component(component_id, {"class_code": class_code}, "Change class")

    def delete_component(self, component_id: UUID) -> dict[str, Any]:
        model = self._component(component_id)
        project_id = UUID(model.project_id)
        snapshot = self.snapshot(project_id)
        children = DependencyGraph(snapshot).children.get(component_id, set())
        if children:
            raise ValueError("Move or delete contained components before deleting their parent")
        before = self._model_dict(model)
        model.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        self._revision(model.project_id, "component", model.id, "delete", before, self._model_dict(model), "Delete component")
        self._validate_and_commit(project_id)
        return self.get_project(project_id)

    def restore_component(self, component_id: UUID) -> dict[str, Any]:
        model = self._component(component_id, include_deleted=True)
        before = self._model_dict(model)
        model.deleted_at = None
        self._ensure_allocations(UUID(model.project_id))
        self._revision(model.project_id, "component", model.id, "restore", before, self._model_dict(model), "Restore component")
        self._validate_and_commit(UUID(model.project_id))
        return self.component_payload(component_id)

    def duplicate_component(self, component_id: UUID) -> dict[str, Any]:
        source = self._component(component_id)
        return self.create_component(
            UUID(source.project_id),
            UUID(source.function_id),
            source.class_code,
            f"{source.label} copy",
            description=source.description,
            parent_component_id=_uuid(source.parent_component_id),
            source_type=source.source_type,
        )

    def create_relation(self, project_id: UUID, source_component_id: UUID, target_component_id: UUID, relation_type: str) -> dict[str, Any]:
        self._project_model(project_id)
        model = RelationModel(id=str(uuid4()), project_id=str(project_id), source_component_id=str(source_component_id), target_component_id=str(target_component_id), relation_type=RelationType(relation_type).value)
        self.session.add(model)
        self.session.flush()
        self._revision(model.project_id, "relation", model.id, "create", None, self._model_dict(model), "Create semantic relation")
        self._validate_and_commit(project_id)
        return self.get_project(project_id)

    def delete_relation(self, relation_id: UUID) -> dict[str, Any]:
        model = self.session.get(RelationModel, str(relation_id))
        if not model or model.deleted_at:
            raise LookupError("Relation not found")
        before = self._model_dict(model)
        model.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        self._revision(model.project_id, "relation", model.id, "delete", before, self._model_dict(model), "Delete semantic relation")
        self._validate_and_commit(UUID(model.project_id))
        return self.get_project(UUID(model.project_id))

    def _ensure_allocations(self, project_id: UUID) -> None:
        components = self.session.scalars(select(ComponentModel).where(ComponentModel.project_id == str(project_id), ComponentModel.deleted_at.is_(None))).all()
        all_allocations = self.session.scalars(select(SequenceAllocationModel)).all()
        for component in components:
            domain = self._component_domain(component)
            scope = allocation_scope(domain)
            code = component.class_code.upper()
            current = next((item for item in all_allocations if item.component_id == component.id and item.active), None)
            if current and current.scope_id == scope and current.class_code == code:
                component.allocated_number = current.assigned_number
                continue
            if current:
                current.active = False
            previous = next((item for item in all_allocations if item.component_id == component.id and item.scope_id == scope and item.class_code == code), None)
            if previous:
                previous.active = True
                component.allocated_number = previous.assigned_number
                continue
            used = [item.assigned_number for item in all_allocations if item.scope_id == scope and item.class_code == code]
            number = max(used, default=0) + 1
            allocation = SequenceAllocationModel(scope_id=scope, class_code=code, component_id=component.id, assigned_number=number, active=True)
            self.session.add(allocation)
            all_allocations.append(allocation)
            component.allocated_number = number
        self.session.flush()

    def _component_domain(self, item: ComponentModel) -> Component:
        return Component(
            id=UUID(item.id),
            project_id=UUID(item.project_id),
            function_id=_uuid(item.function_id),
            parent_component_id=_uuid(item.parent_component_id),
            class_code=item.class_code,
            allocated_number=item.allocated_number,
            label=item.label,
            description=item.description,
            source_type=SourceType(item.source_type),
            source_query_id=_uuid(item.source_query_id),
            deleted=item.deleted_at is not None,
        )

    def snapshot(self, project_id: UUID) -> ProjectSnapshot:
        project = self._project_model(project_id)
        functions = self.session.scalars(select(FunctionNodeModel).where(FunctionNodeModel.project_id == project.id)).all()
        components = self.session.scalars(select(ComponentModel).where(ComponentModel.project_id == project.id)).all()
        relations = self.session.scalars(select(RelationModel).where(RelationModel.project_id == project.id)).all()
        component_ids = {item.id for item in components}
        allocations = self.session.scalars(select(SequenceAllocationModel).where(SequenceAllocationModel.component_id.in_(component_ids))).all() if component_ids else []
        return ProjectSnapshot(
            Project(id=UUID(project.id), name=project.name, description=project.description, ruleset_id=project.ruleset_id, created_at=project.created_at.replace(tzinfo=UTC)),
            tuple(
                FunctionNode(id=UUID(item.id), project_id=UUID(item.project_id), number=item.number, label=item.label, parent_id=_uuid(item.parent_id), description=item.description, deleted=item.deleted_at is not None) for item in functions
            ),
            tuple(self._component_domain(item) for item in components),
            tuple(
                Relation(
                    id=UUID(item.id),
                    project_id=UUID(item.project_id),
                    source_component_id=UUID(item.source_component_id),
                    target_component_id=UUID(item.target_component_id),
                    relation_type=RelationType(item.relation_type),
                    deleted=item.deleted_at is not None,
                )
                for item in relations
            ),
            tuple(SequenceAllocation(item.scope_id, item.class_code, UUID(item.component_id), item.assigned_number, item.active) for item in allocations),
        )

    def compile_project(self, project_id: UUID) -> CompileResult:
        self._ensure_allocations(project_id)
        snapshot = self.snapshot(project_id)
        return RDSCompiler(RulesetRegistry.get(snapshot.project.ruleset_id)).compile(snapshot)

    def validate_project(self, project_id: UUID) -> list[dict[str, Any]]:
        return [asdict(issue) for issue in self.compile_project(project_id).issues]

    def _validate_and_commit(self, project_id: UUID) -> CompileResult:
        try:
            result = self.compile_project(project_id)
            errors = [issue for issue in result.issues if issue.severity == Severity.ERROR]
            if errors:
                raise ProjectValidationError(errors)
            self.session.commit()
            return result
        except Exception:
            self.session.rollback()
            raise

    def get_project(self, project_id: UUID) -> dict[str, Any]:
        result = self.compile_project(project_id)
        compiled = {str(item.component_id): item for item in result.designations}
        snapshot = result.snapshot
        component_payloads = [self._component_payload(item, compiled.get(str(item.id)), snapshot) for item in snapshot.components if not item.deleted]
        component_payloads.sort(key=lambda item: item["designation"])
        return {
            "id": str(snapshot.project.id),
            "name": snapshot.project.name,
            "description": snapshot.project.description,
            "ruleset_id": snapshot.project.ruleset_id,
            "functions": [asdict(item) for item in snapshot.functions if not item.deleted],
            "components": component_payloads,
            "relations": [asdict(item) for item in snapshot.relations if not item.deleted],
            "validation": [asdict(item) for item in result.issues],
        }

    def _component_payload(self, component: Component, compiled: Any, snapshot: ProjectSnapshot) -> dict[str, Any]:
        function = snapshot.function_map.get(component.function_id) if component.function_id else None
        parent = snapshot.component_map.get(component.parent_component_id) if component.parent_component_id else None
        return {
            **asdict(component),
            "designation": compiled.designation if compiled else "",
            "valid": compiled.valid if compiled else False,
            "tokens": [asdict(item) for item in compiled.tokens] if compiled else [],
            "issues": [asdict(item) for item in compiled.issues] if compiled else [],
            "function_label": function.label if function else None,
            "function_number": function.number if function else None,
            "parent_label": parent.label if parent else None,
        }

    def component_payload(self, component_id: UUID) -> dict[str, Any]:
        model = self._component(component_id)
        project = self.get_project(UUID(model.project_id))
        return next(item for item in project["components"] if str(item["id"]) == str(component_id))

    def history(self, component_id: UUID) -> list[dict[str, Any]]:
        rows = self.session.scalars(select(RevisionModel).where(RevisionModel.entity_id == str(component_id)).order_by(RevisionModel.timestamp.desc())).all()
        return [{**self._model_dict(item), "before": json.loads(item.before_json) if item.before_json else None, "after": json.loads(item.after_json) if item.after_json else None} for item in rows]

    def undo(self, project_id: UUID) -> dict[str, Any]:
        revision = self.session.scalar(select(RevisionModel).where(RevisionModel.project_id == str(project_id), RevisionModel.undone_at.is_(None), RevisionModel.entity_type != "project").order_by(RevisionModel.timestamp.desc()))
        if not revision:
            raise LookupError("Nothing to undo")
        model_class = {"component": ComponentModel, "function": FunctionNodeModel, "relation": RelationModel}.get(revision.entity_type)
        if not model_class:
            raise ValueError("Revision cannot be undone")
        model = self.session.get(model_class, revision.entity_id)
        before = json.loads(revision.before_json) if revision.before_json else None
        if revision.operation == "create":
            model.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        elif before:
            for key, value in before.items():
                if key in {"created_at", "updated_at", "timestamp"}:
                    continue
                if key == "deleted_at" and value:
                    value = datetime.fromisoformat(value)
                setattr(model, key, value)
        revision.undone_at = datetime.now(UTC).replace(tzinfo=None)
        self._ensure_allocations(project_id)
        self._validate_and_commit(project_id)
        return self.get_project(project_id)

    def redo(self, project_id: UUID) -> dict[str, Any]:
        revision = self.session.scalar(
            select(RevisionModel)
            .where(
                RevisionModel.project_id == str(project_id),
                RevisionModel.undone_at.is_not(None),
                RevisionModel.entity_type != "project",
            )
            .order_by(RevisionModel.undone_at.desc())
        )
        if not revision:
            raise LookupError("Nothing to redo")
        model_class = {
            "component": ComponentModel,
            "function": FunctionNodeModel,
            "relation": RelationModel,
        }.get(revision.entity_type)
        if not model_class:
            raise ValueError("Revision cannot be redone")
        model = self.session.get(model_class, revision.entity_id)
        after = json.loads(revision.after_json) if revision.after_json else None
        if revision.operation == "create":
            model.deleted_at = None
        elif after:
            for key, value in after.items():
                if key in {"created_at", "updated_at", "timestamp"}:
                    continue
                if key == "deleted_at" and value:
                    value = datetime.fromisoformat(value)
                setattr(model, key, value)
        revision.undone_at = None
        self._ensure_allocations(project_id)
        self._validate_and_commit(project_id)
        return self.get_project(project_id)
