from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from app.domain.models import Component, FunctionNode, Project, ProjectSnapshot, Severity
from app.rds.compiler import RDSCompiler
from app.standards.loader import load_ruleset

RULESET = load_ruleset("ee3_2026_27")
COMPILER = RDSCompiler(RULESET)


def scenario():
    project = Project(name="Golden")
    function = FunctionNode(project_id=project.id, number=2, label="Joint 2")
    motor = Component(project_id=project.id, function_id=function.id, class_code="M", label="Motor")
    encoder = Component(project_id=project.id, function_id=function.id, parent_component_id=motor.id, class_code="B", label="Encoder")
    return ProjectSnapshot(project, (function,), (motor, encoder)), motor, encoder


def designation(result, component):
    return result.by_component(component.id).designation


def test_motor_under_joint_2():
    snapshot, motor, _ = scenario()
    assert designation(COMPILER.compile(snapshot), motor) == "=M2-M1"


def test_encoder_integrated_with_motor():
    snapshot, _, encoder = scenario()
    assert designation(COMPILER.compile(snapshot), encoder) == "=M2-M1.B1"


def test_encoder_separate_from_motor():
    snapshot, _, encoder = scenario()
    separate = replace(encoder, parent_component_id=None)
    changed = replace(snapshot, components=tuple(separate if item.id == encoder.id else item for item in snapshot.components))
    assert designation(COMPILER.compile(changed), separate) == "=M2-B1"


def test_compilation_is_deterministic_and_unique():
    snapshot, _, _ = scenario()
    first = COMPILER.compile(snapshot)
    second = COMPILER.compile(snapshot)
    assert first.designations == second.designations
    values = [item.designation for item in first.designations]
    assert len(values) == len(set(values))


def test_description_change_does_not_change_rds_or_uuid():
    snapshot, motor, _ = scenario()
    first = COMPILER.compile(snapshot)
    edited = replace(motor, description="Changed prose only")
    changed = replace(snapshot, components=tuple(edited if item.id == motor.id else item for item in snapshot.components), allocations=first.snapshot.allocations)
    second = COMPILER.compile(changed)
    assert edited.id == motor.id
    assert designation(first, motor) == designation(second, edited)


def test_moving_parent_recompiles_descendant():
    snapshot, motor, encoder = scenario()
    first = COMPILER.compile(snapshot)
    second_function = FunctionNode(project_id=snapshot.project.id, number=3, label="Joint 3")
    moved_motor = replace(motor, function_id=second_function.id)
    moved_encoder = replace(encoder, function_id=second_function.id)
    changed = replace(first.snapshot, functions=(*snapshot.functions, second_function), components=(moved_motor, moved_encoder))
    second = COMPILER.compile(changed)
    assert designation(first, encoder) == "=M2-M1.B1"
    assert designation(second, moved_encoder) == "=M3-M1.B1"


def test_containment_cycles_are_rejected():
    snapshot, motor, encoder = scenario()
    cyclic_motor = replace(motor, parent_component_id=encoder.id)
    result = COMPILER.compile(replace(snapshot, components=(cyclic_motor, encoder)))
    assert any(item.code == "CYCLIC_CONTAINMENT" and item.severity == Severity.ERROR for item in result.issues)


def test_deleted_b2_does_not_rename_b3():
    project = Project(name="Stable")
    function = FunctionNode(project_id=project.id, number=2, label="Joint 2")
    sensors = tuple(Component(project_id=project.id, function_id=function.id, class_code="B", label=f"Sensor {index}") for index in range(1, 4))
    first = COMPILER.compile(ProjectSnapshot(project, (function,), sensors))
    numbered = first.snapshot.components
    b2 = next(item for item in numbered if item.allocated_number == 2)
    b3 = next(item for item in numbered if item.allocated_number == 3)
    second = COMPILER.compile(replace(first.snapshot, components=tuple(replace(item, deleted=True) if item.id == b2.id else item for item in numbered)))
    assert designation(second, b3) == "=M2-B3"
    assert second.by_component(b2.id) is None


@given(st.lists(st.sampled_from(["B", "M", "K", "S", "X"]), min_size=1, max_size=20))
def test_random_valid_component_forests_are_unique(codes):
    project = Project(name="Generated")
    function = FunctionNode(project_id=project.id, number=2, label="Generated")
    components = tuple(Component(project_id=project.id, function_id=function.id, class_code=code, label=f"Object {index}") for index, code in enumerate(codes))
    result = COMPILER.compile(ProjectSnapshot(project, (function,), components))
    emitted = [item.designation for item in result.designations]
    assert len(emitted) == len(set(emitted))
    assert all(item.valid for item in result.designations)
