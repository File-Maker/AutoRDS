from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4


class SourceType(StrEnum):
    MANUAL = "manual"
    INFERENCE = "inference"
    IMPORT = "import"


class RelationType(StrEnum):
    DRIVES = "DRIVES"
    SENSES = "SENSES"
    CONTROLS = "CONTROLS"
    MOUNTED_ON = "MOUNTED_ON"
    LOCATED_AT = "LOCATED_AT"
    CONNECTED_TO = "CONNECTED_TO"
    GUIDES = "GUIDES"
    PROTECTS = "PROTECTS"


class Severity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


def _id() -> UUID:
    return uuid4()


@dataclass(frozen=True, slots=True)
class Project:
    name: str
    ruleset_id: str = "ee3_2026_27"
    id: UUID = field(default_factory=_id)
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class FunctionNode:
    project_id: UUID
    number: int
    label: str
    id: UUID = field(default_factory=_id)
    parent_id: UUID | None = None
    description: str = ""
    deleted: bool = False


@dataclass(frozen=True, slots=True)
class Component:
    project_id: UUID
    function_id: UUID | None
    class_code: str
    label: str
    id: UUID = field(default_factory=_id)
    parent_component_id: UUID | None = None
    allocated_number: int | None = None
    description: str = ""
    source_type: SourceType = SourceType.MANUAL
    source_query_id: UUID | None = None
    deleted: bool = False

    def changed(self, **changes: Any) -> Component:
        changes.pop("id", None)
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class Relation:
    project_id: UUID
    source_component_id: UUID
    target_component_id: UUID
    relation_type: RelationType
    id: UUID = field(default_factory=_id)
    deleted: bool = False


@dataclass(frozen=True, slots=True)
class SequenceAllocation:
    scope_id: str
    class_code: str
    component_id: UUID
    assigned_number: int
    active: bool = True


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    severity: Severity
    entity_id: UUID | None
    message: str
    possible_fix: str | None = None


@dataclass(frozen=True, slots=True)
class DesignationToken:
    value: str
    meaning: str


@dataclass(frozen=True, slots=True)
class CompiledDesignation:
    component_id: UUID
    designation: str
    valid: bool
    tokens: tuple[DesignationToken, ...]
    issues: tuple[ValidationIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ProjectSnapshot:
    project: Project
    functions: tuple[FunctionNode, ...] = ()
    components: tuple[Component, ...] = ()
    relations: tuple[Relation, ...] = ()
    allocations: tuple[SequenceAllocation, ...] = ()

    @property
    def function_map(self) -> Mapping[UUID, FunctionNode]:
        return MappingProxyType({item.id: item for item in self.functions if not item.deleted})

    @property
    def component_map(self) -> Mapping[UUID, Component]:
        return MappingProxyType({item.id: item for item in self.components if not item.deleted})
