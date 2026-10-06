from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ProjectModel(Base, TimestampMixin):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ruleset_id: Mapped[str] = mapped_column(String(100), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class FunctionNodeModel(Base, TimestampMixin):
    __tablename__ = "function_nodes"
    __table_args__ = (UniqueConstraint("project_id", "number", name="uq_function_number"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("function_nodes.id"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class ComponentModel(Base, TimestampMixin):
    __tablename__ = "components"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    function_id: Mapped[str | None] = mapped_column(ForeignKey("function_nodes.id"), index=True)
    parent_component_id: Mapped[str | None] = mapped_column(ForeignKey("components.id"), index=True)
    class_code: Mapped[str] = mapped_column(String(8), nullable=False)
    allocated_number: Mapped[int | None] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    source_query_id: Mapped[str | None] = mapped_column(String(36))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class RelationModel(Base, TimestampMixin):
    __tablename__ = "relations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_component_id: Mapped[str] = mapped_column(ForeignKey("components.id"))
    target_component_id: Mapped[str] = mapped_column(ForeignKey("components.id"))
    relation_type: Mapped[str] = mapped_column(String(40), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class SequenceAllocationModel(Base):
    __tablename__ = "sequence_allocations"
    __table_args__ = (UniqueConstraint("scope_id", "class_code", "assigned_number", name="uq_sequence_scope"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope_id: Mapped[str] = mapped_column(String(160), index=True)
    class_code: Mapped[str] = mapped_column(String(8), nullable=False)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    assigned_number: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class GenerationQueryModel(Base):
    __tablename__ = "generation_queries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    candidates_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class InferenceDecisionModel(Base):
    __tablename__ = "inference_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_id: Mapped[str] = mapped_column(ForeignKey("generation_queries.id"), index=True)
    candidate_key: Mapped[str] = mapped_column(String(100), nullable=False)
    prediction_json: Mapped[str] = mapped_column(Text, nullable=False)
    approved_json: Mapped[str] = mapped_column(Text, nullable=False)
    corrected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    project_context_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    provider_version: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class RevisionModel(Base):
    __tablename__ = "revisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    operation: Mapped[str] = mapped_column(String(40), nullable=False)
    before_json: Mapped[str | None] = mapped_column(Text)
    after_json: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    undone_at: Mapped[datetime | None] = mapped_column(DateTime)


class RulesetMigrationModel(Base):
    __tablename__ = "ruleset_migrations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    from_ruleset: Mapped[str] = mapped_column(String(100), nullable=False)
    to_ruleset: Mapped[str] = mapped_column(String(100), nullable=False)
    preview_json: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
