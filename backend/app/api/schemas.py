from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreate(APIModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    ruleset_id: str = "ee3_2026_27"


class ProjectPatch(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    ruleset_id: str | None = None


class FunctionCreate(APIModel):
    number: int = Field(ge=0)
    label: str = Field(min_length=1, max_length=200)
    description: str = ""
    parent_id: UUID | None = None


class FunctionPatch(APIModel):
    number: int | None = Field(default=None, ge=0)
    label: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    parent_id: UUID | None = None


class ComponentCreate(APIModel):
    function_id: UUID
    parent_component_id: UUID | None = None
    class_code: str = Field(min_length=1, max_length=8)
    label: str = Field(min_length=1, max_length=200)
    description: str = ""


class ComponentPatch(APIModel):
    function_id: UUID | None = None
    parent_component_id: UUID | None = None
    class_code: str | None = Field(default=None, min_length=1, max_length=8)
    label: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class BulkComponentPatch(APIModel):
    component_ids: list[UUID] = Field(min_length=1)
    changes: ComponentPatch


class RelationCreate(APIModel):
    source_component_id: UUID
    target_component_id: UUID
    relation_type: str


class InferenceRequest(APIModel):
    text: str = Field(min_length=1)


class CandidateApproval(APIModel):
    candidate_key: str
    accepted: bool
    label: str | None = None
    class_code: str | None = None
    function_id: UUID | None = None
    parent_component_id: UUID | None = None
    prediction: dict[str, Any]


class InferenceApproval(APIModel):
    decisions: list[CandidateApproval]


class MigrationRequest(APIModel):
    target_ruleset_id: str
