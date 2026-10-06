from __future__ import annotations

import json
from dataclasses import asdict, replace
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import __version__
from app.domain.models import Component
from app.inference.rules import RuleInferenceProvider
from app.persistence.database import SessionLocal
from app.persistence.models import GenerationQueryModel, InferenceDecisionModel, RulesetMigrationModel
from app.rds.compiler import RDSCompiler
from app.rds.explanation import explain
from app.services.exports import engineering_export, export_portable, floc_rows, import_portable
from app.services.project_service import ProjectService
from app.standards.loader import RulesetRegistry

from .schemas import BulkComponentPatch, ComponentCreate, ComponentPatch, FunctionCreate, FunctionPatch, InferenceApproval, InferenceRequest, MigrationRequest, ProjectCreate, ProjectPatch, RelationCreate

router = APIRouter(prefix="/api")


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def service(session: Session = Depends(get_session)) -> ProjectService:
    return ProjectService(session)


def _changes(model) -> dict:
    return {key: value for key, value in model.model_dump().items() if key in model.model_fields_set}


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "application": "AutoRDS", "version": __version__, "local": True}


@router.get("/rulesets")
def rulesets() -> list[dict]:
    return [item.model_dump() for item in RulesetRegistry.list()]


@router.get("/rulesets/{ruleset_id}")
def ruleset(ruleset_id: str) -> dict:
    try:
        return RulesetRegistry.get(ruleset_id).model_dump()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/projects", status_code=201)
def create_project(payload: ProjectCreate, projects: ProjectService = Depends(service)) -> dict:
    return projects.create_project(**payload.model_dump())


@router.get("/projects")
def list_projects(projects: ProjectService = Depends(service)) -> list[dict]:
    return projects.list_projects()


@router.get("/projects/{project_id}")
def get_project(project_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.get_project(project_id)


@router.patch("/projects/{project_id}")
def patch_project(project_id: UUID, payload: ProjectPatch, projects: ProjectService = Depends(service)) -> dict:
    return projects.update_project(project_id, _changes(payload))


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: UUID, projects: ProjectService = Depends(service)) -> Response:
    projects.delete_project(project_id)
    return Response(status_code=204)


@router.post("/projects/{project_id}/functions", status_code=201)
def create_function(project_id: UUID, payload: FunctionCreate, projects: ProjectService = Depends(service)) -> dict:
    return projects.create_function(project_id, **payload.model_dump())


@router.patch("/functions/{function_id}")
def patch_function(function_id: UUID, payload: FunctionPatch, projects: ProjectService = Depends(service)) -> dict:
    return projects.update_function(function_id, _changes(payload))


@router.delete("/functions/{function_id}")
def delete_function(function_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.delete_function(function_id)


@router.post("/projects/{project_id}/components/preview")
def preview_component(project_id: UUID, payload: ComponentCreate, projects: ProjectService = Depends(service)) -> dict:
    snapshot = projects.snapshot(project_id)
    candidate = Component(project_id=project_id, function_id=payload.function_id, parent_component_id=payload.parent_component_id, class_code=payload.class_code.upper(), label=payload.label, description=payload.description)
    result = RDSCompiler(RulesetRegistry.get(snapshot.project.ruleset_id)).compile(replace(snapshot, components=(*snapshot.components, candidate)))
    compiled = result.by_component(candidate.id)
    return asdict(compiled) if compiled else {}


@router.post("/projects/{project_id}/components", status_code=201)
def create_component(project_id: UUID, payload: ComponentCreate, projects: ProjectService = Depends(service)) -> dict:
    return projects.create_component(project_id, **payload.model_dump())


@router.patch("/components/{component_id}")
def patch_component(component_id: UUID, payload: ComponentPatch, projects: ProjectService = Depends(service)) -> dict:
    return projects.update_component(component_id, _changes(payload))


@router.delete("/components/{component_id}")
def delete_component(component_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.delete_component(component_id)


@router.post("/components/{component_id}/duplicate", status_code=201)
def duplicate_component(component_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.duplicate_component(component_id)


@router.post("/projects/{project_id}/components/bulk")
def bulk_update_components(project_id: UUID, payload: BulkComponentPatch, projects: ProjectService = Depends(service)) -> dict:
    changes = _changes(payload.changes)
    for component_id in payload.component_ids:
        model = projects._component(component_id)
        if model.project_id != str(project_id):
            raise ValueError("Bulk edit cannot cross project boundaries")
        projects.update_component(component_id, changes, "Bulk edit")
    return projects.get_project(project_id)


@router.post("/components/{component_id}/restore")
def restore_component(component_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.restore_component(component_id)


@router.post("/projects/{project_id}/relations", status_code=201)
def create_relation(project_id: UUID, payload: RelationCreate, projects: ProjectService = Depends(service)) -> dict:
    return projects.create_relation(project_id, **payload.model_dump())


@router.delete("/relations/{relation_id}")
def delete_relation(relation_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.delete_relation(relation_id)


@router.post("/projects/{project_id}/validate")
def validate(project_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return {"issues": projects.validate_project(project_id)}


@router.post("/projects/{project_id}/recompile")
def recompile(project_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.get_project(project_id)


@router.post("/projects/{project_id}/undo")
def undo(project_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.undo(project_id)


@router.post("/projects/{project_id}/redo")
def redo(project_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return projects.redo(project_id)


@router.get("/projects/{project_id}/floc")
def floc(project_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    return {"headers": ["RDS", "Component", "Function", "Class", "Parent", "Description", "Status", "Warnings"], "rows": floc_rows(projects, project_id)}


@router.get("/projects/{project_id}/graph")
def graph(project_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    project = projects.get_project(project_id)
    nodes = [{"id": str(item["id"]), "type": "function", "label": f"=M{item['number']} — {item['label']}"} for item in project["functions"]]
    nodes += [{"id": str(item["id"]), "type": "component", "label": f"{item['designation']} — {item['label']}"} for item in project["components"]]
    edges = [{"id": f"allocation-{item['id']}", "source": str(item["function_id"]), "target": str(item["id"]), "kind": "allocation"} for item in project["components"] if not item["parent_component_id"]]
    edges += [{"id": f"containment-{item['id']}", "source": str(item["parent_component_id"]), "target": str(item["id"]), "kind": "containment"} for item in project["components"] if item["parent_component_id"]]
    edges += [{"id": str(item["id"]), "source": str(item["source_component_id"]), "target": str(item["target_component_id"]), "kind": "semantic", "label": item["relation_type"]} for item in project["relations"]]
    return {"nodes": nodes, "edges": edges}


@router.get("/components/{component_id}/history")
def component_history(component_id: UUID, projects: ProjectService = Depends(service)) -> list[dict]:
    return projects.history(component_id)


@router.get("/components/{component_id}/explanation")
def component_explanation(component_id: UUID, projects: ProjectService = Depends(service)) -> dict:
    model = projects._component(component_id)
    compiled = projects.compile_project(UUID(model.project_id)).by_component(component_id)
    if not compiled:
        raise HTTPException(404, "Compiled designation not found")
    return explain(compiled)


@router.get("/projects/{project_id}/export/{format}")
def export_engineering(project_id: UUID, format: str, projects: ProjectService = Depends(service)) -> Response:
    if format not in {"json", "csv", "xlsx", "pdf"}:
        raise HTTPException(400, "Supported formats: json, csv, xlsx, pdf")
    content, media_type = engineering_export(projects, project_id, format)
    return Response(content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="floc.{format}"'})


@router.get("/projects/{project_id}/portable")
def portable_export(project_id: UUID, projects: ProjectService = Depends(service)) -> Response:
    content = export_portable(projects, project_id)
    name = projects.get_project(project_id)["name"].replace('"', "")
    return Response(content, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{name}.autords"'})


@router.post("/projects/import", status_code=201)
async def portable_import(file: UploadFile = File(...), session: Session = Depends(get_session)) -> dict:
    return import_portable(session, await file.read())


@router.post("/projects/{project_id}/inference")
def infer(project_id: UUID, payload: InferenceRequest, projects: ProjectService = Depends(service)) -> dict:
    snapshot = projects.snapshot(project_id)
    provider = RuleInferenceProvider(RulesetRegistry.get(snapshot.project.ruleset_id))
    candidates = provider.infer(payload.text)
    query = GenerationQueryModel(id=str(uuid4()), project_id=str(project_id), query=payload.text, provider=provider.version, candidates_json=json.dumps(candidates))
    projects.session.add(query)
    projects.session.commit()
    return {"query_id": query.id, "provider": provider.version, "authoritative": False, "candidates": candidates}


@router.post("/inference/{query_id}/approve")
def approve_inference(query_id: UUID, payload: InferenceApproval, projects: ProjectService = Depends(service)) -> dict:
    query = projects.session.get(GenerationQueryModel, str(query_id))
    if not query:
        raise HTTPException(404, "Inference query not found")
    created: dict[str, str] = {}
    for decision in payload.decisions:
        approved = {
            "accepted": decision.accepted,
            "label": decision.label,
            "class": decision.class_code,
            "function_id": str(decision.function_id) if decision.function_id else None,
            "parent_component_id": str(decision.parent_component_id) if decision.parent_component_id else None,
        }
        projects.session.add(
            InferenceDecisionModel(
                id=str(uuid4()),
                query_id=query.id,
                candidate_key=decision.candidate_key,
                prediction_json=json.dumps(decision.prediction),
                approved_json=json.dumps(approved),
                corrected=any(decision.prediction.get(key) != value for key, value in {"class_code": decision.class_code, "label": decision.label}.items() if value),
                project_context_json=json.dumps({"project_id": query.project_id}),
                provider_version=query.provider,
            )
        )
        projects.session.commit()
        if decision.accepted and decision.function_id and decision.class_code and decision.label:
            component = projects.create_component(UUID(query.project_id), decision.function_id, decision.class_code, decision.label, parent_component_id=decision.parent_component_id, source_type="inference", source_query_id=query_id)
            created[decision.candidate_key] = str(component["id"])
    return {"created": created, "project": projects.get_project(UUID(query.project_id))}


def _migration_preview(projects: ProjectService, project_id: UUID, target_ruleset_id: str) -> dict:
    snapshot = projects.snapshot(project_id)
    current = RDSCompiler(RulesetRegistry.get(snapshot.project.ruleset_id)).compile(snapshot)
    target = RDSCompiler(RulesetRegistry.get(target_ruleset_id)).compile(replace(snapshot, project=replace(snapshot.project, ruleset_id=target_ruleset_id)))
    old = {item.component_id: item for item in current.designations}
    new = {item.component_id: item for item in target.designations}
    changes = [{"component_id": str(key), "before": old[key].designation, "after": new[key].designation, "valid": new[key].valid} for key in new if key in old and old[key].designation != new[key].designation]
    return {
        "from": snapshot.project.ruleset_id,
        "to": target_ruleset_id,
        "unchanged": len(new) - len(changes),
        "changed": len(changes),
        "invalid": sum(not item.valid for item in new.values()),
        "ambiguous": sum(issue.code == "AMBIGUOUS_PARENT" for issue in target.issues),
        "changes": changes,
    }


@router.post("/projects/{project_id}/ruleset-migration/preview")
def preview_migration(project_id: UUID, payload: MigrationRequest, projects: ProjectService = Depends(service)) -> dict:
    return _migration_preview(projects, project_id, payload.target_ruleset_id)


@router.post("/projects/{project_id}/ruleset-migration/apply")
def apply_migration(project_id: UUID, payload: MigrationRequest, projects: ProjectService = Depends(service)) -> dict:
    preview = _migration_preview(projects, project_id, payload.target_ruleset_id)
    project = projects._project_model(project_id)
    before = projects._model_dict(project)
    project.ruleset_id = payload.target_ruleset_id
    migration = RulesetMigrationModel(id=str(uuid4()), project_id=str(project_id), from_ruleset=preview["from"], to_ruleset=preview["to"], preview_json=json.dumps(preview))
    projects.session.add(migration)
    projects._revision(str(project_id), "project", str(project_id), "ruleset_migration", before, projects._model_dict(project), "Apply ruleset migration")
    projects._validate_and_commit(project_id)
    return projects.get_project(project_id)
