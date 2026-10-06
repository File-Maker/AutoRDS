from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Aspect(StrictModel):
    prefix: str = Field(min_length=1, max_length=2)


class Aspects(StrictModel):
    function: Aspect
    product: Aspect
    location: Aspect


class EE3Rules(StrictModel):
    function_pattern: str
    require_function_prefix: bool


class ProductRules(StrictModel):
    containment_separator: str = Field(min_length=1, max_length=2)
    preserve_allocated_numbers: bool


class NumberingRules(StrictModel):
    strategy: Literal["scoped_sequence"]
    resequence_on_delete: bool


class ValidationRules(StrictModel):
    duplicate_designations: Literal["error", "warning", "info"]
    missing_function: Literal["error", "warning", "info"]
    unknown_class: Literal["error", "warning", "info"]
    cyclic_containment: Literal["error", "warning", "info"]
    ambiguous_parent: Literal["error", "warning", "info"]


class ClassDefinition(StrictModel):
    name: str
    aliases: list[str]


class Ruleset(StrictModel):
    id: str
    name: str
    version: str
    standard_basis: list[str]
    aspects: Aspects
    ee3: EE3Rules
    product: ProductRules
    numbering: NumberingRules
    validation: ValidationRules
    classes: dict[str, ClassDefinition]

    @field_validator("classes")
    @classmethod
    def normalize_codes(cls, value: dict[str, ClassDefinition]) -> dict[str, ClassDefinition]:
        if not value:
            raise ValueError("ruleset must define at least one class")
        if any(code != code.upper() or not code.isalpha() for code in value):
            raise ValueError("class codes must be uppercase letters")
        return value
