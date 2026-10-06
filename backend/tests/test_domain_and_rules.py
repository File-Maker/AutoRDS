from pathlib import Path
from uuid import uuid4

import pytest

from app.domain.models import Component, FunctionNode, Project, ProjectSnapshot
from app.standards.loader import load_ruleset


def test_construct_project_without_database():
    project = Project(name="Robot")
    function = FunctionNode(project_id=project.id, number=2, label="Joint 2")
    motor = Component(project_id=project.id, function_id=function.id, class_code="M", label="Motor")
    encoder = Component(project_id=project.id, function_id=function.id, parent_component_id=motor.id, class_code="B", label="Encoder")
    snapshot = ProjectSnapshot(project, (function,), (motor, encoder))
    assert snapshot.component_map[encoder.id].parent_component_id == motor.id
    assert snapshot.project.id != uuid4()


def test_ruleset_loads_prefixes_classes_and_numbering():
    ruleset = load_ruleset("ee3_2026_27")
    assert ruleset.aspects.function.prefix == "="
    assert ruleset.aspects.product.prefix == "-"
    assert ruleset.classes["B"].name == "sensing_object"
    assert "encoder" in ruleset.classes["B"].aliases
    assert ruleset.numbering.strategy == "scoped_sequence"
    assert ruleset.numbering.resequence_on_delete is False


def test_invalid_ruleset_is_rejected(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text("id: broken\naspects: [not, valid", encoding="utf-8")
    with pytest.raises(ValueError):
        load_ruleset(path)
