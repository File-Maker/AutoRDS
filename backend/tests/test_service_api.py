from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.services.project_service import ProjectService


def test_exact_milestone_and_undo(session):
    service = ProjectService(session)
    project = service.create_project("Milestone")
    project_id = UUID(project["id"])
    project = service.create_function(project_id, 2, "Joint 2")
    function_id = UUID(str(project["functions"][0]["id"]))
    motor = service.create_component(project_id, function_id, "M", "Motor")
    assert motor["designation"] == "=M2-M1"
    encoder = service.create_component(project_id, function_id, "B", "Encoder", parent_component_id=UUID(str(motor["id"])))
    encoder_id = UUID(str(encoder["id"]))
    assert encoder["designation"] == "=M2-M1.B1"
    moved = service.move_component(encoder_id, None)
    assert moved["designation"] == "=M2-B1"
    restored = service.undo(project_id)
    same = next(item for item in restored["components"] if str(item["id"]) == str(encoder_id))
    assert same["designation"] == "=M2-M1.B1"
    assert str(same["id"]) == str(encoder_id)
    redone = service.redo(project_id)
    same = next(item for item in redone["components"] if str(item["id"]) == str(encoder_id))
    assert same["designation"] == "=M2-B1"


def test_deleted_number_is_not_reused(session):
    service = ProjectService(session)
    project_id = UUID(service.create_project("Numbers")["id"])
    function_id = UUID(str(service.create_function(project_id, 2, "Joint")["functions"][0]["id"]))
    values = [service.create_component(project_id, function_id, "B", f"B{index}") for index in range(3)]
    service.delete_component(UUID(str(values[1]["id"])))
    current = service.get_project(project_id)
    assert [item["designation"] for item in current["components"]] == ["=M2-B1", "=M2-B3"]
    fourth = service.create_component(project_id, function_id, "B", "B4")
    assert fourth["designation"] == "=M2-B4"


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
