import json
from uuid import UUID

from app.inference.rules import RuleInferenceProvider
from app.services.exports import engineering_export, export_portable, import_portable
from app.services.project_service import ProjectService
from app.standards.loader import load_ruleset


def populated(service):
    project_id = UUID(service.create_project("Portable")["id"])
    function_id = UUID(str(service.create_function(project_id, 2, "Joint 2")["functions"][0]["id"]))
    motor = service.create_component(project_id, function_id, "M", "Motor")
    service.create_component(project_id, function_id, "B", "Encoder", parent_component_id=UUID(str(motor["id"])))
    return project_id


def test_all_engineering_exports_compile(session):
    service = ProjectService(session)
    project_id = populated(service)
    for format in ("json", "csv", "xlsx", "pdf"):
        content, media_type = engineering_export(service, project_id, format)
        assert content
        assert media_type
    data, _ = engineering_export(service, project_id, "json")
    assert "=M2-M1.B1" in {item["RDS"] for item in json.loads(data)["floc"]}


def test_portable_round_trip_is_semantically_equivalent(session):
    service = ProjectService(session)
    original_id = populated(service)
    original = service.get_project(original_id)
    imported = import_portable(session, export_portable(service, original_id))
    imported_semantics = sorted((item["designation"], item["label"], item["class_code"]) for item in imported["components"])
    original_semantics = sorted((item["designation"], item["label"], item["class_code"]) for item in original["components"])
    assert imported_semantics == original_semantics


def test_rule_inference_returns_semantics_not_rds():
    provider = RuleInferenceProvider(load_ruleset("ee3_2026_27"))
    candidates = provider.infer("Joint 2 rotates the product using a servo motor. An encoder is mounted directly on the motor. There is also a separate limit sensor.")
    assert [(item["class_code"], item["function_number"]) for item in candidates] == [("M", 2), ("B", 2), ("B", 2)]
    assert candidates[1]["parent_key"] == candidates[0]["key"]
    assert candidates[2]["parent_key"] is None
    assert all("designation" not in item for item in candidates)
