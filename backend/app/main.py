from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.persistence.database import init_database
from app.rds.validator import ProjectValidationError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    yield


app = FastAPI(title="AutoRDS", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.exception_handler(ProjectValidationError)
async def validation_error(_request: Request, exc: ProjectValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Project graph is invalid",
            "issues": [{"code": issue.code, "severity": issue.severity, "entity_id": str(issue.entity_id) if issue.entity_id else None, "message": issue.message, "possible_fix": issue.possible_fix} for issue in exc.issues],
        },
    )


@app.exception_handler(LookupError)
async def lookup_error(_request: Request, exc: LookupError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


static_dir = Path(__file__).with_name("static")
if static_dir.exists() and (static_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
