from __future__ import annotations

from app.domain.models import Component, DesignationToken, FunctionNode
from app.standards.schema import Ruleset


def render_function(function: FunctionNode, ruleset: Ruleset) -> str:
    value = ruleset.ee3.function_pattern.format(number=function.number)
    return f"{ruleset.aspects.function.prefix}{value}"


def render_component_path(
    component: Component,
    ancestry: list[Component],
    function: FunctionNode,
    ruleset: Ruleset,
) -> tuple[str, tuple[DesignationToken, ...]]:
    function_value = render_function(function, ruleset)
    tokens = [DesignationToken(function_value, "assigned function")]
    pieces = [function_value]
    path = [*ancestry, component]
    for index, item in enumerate(path):
        prefix = ruleset.aspects.product.prefix if index == 0 else ruleset.product.containment_separator
        value = f"{prefix}{item.class_code}{item.allocated_number}"
        meaning = ruleset.classes[item.class_code].name.replace("_", " ")
        if index > 0:
            meaning = f"contained {meaning}"
        pieces.append(value)
        tokens.append(DesignationToken(value, meaning))
    return "".join(pieces), tuple(tokens)
