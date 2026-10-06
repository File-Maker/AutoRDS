# AutoRDS

AutoRDS is a local-first engineering workspace for constructing, validating, explaining, and
exporting Reference Designations. It keeps persistent object identity separate from RDS: every
project entity has an immutable UUID, while every displayed designation is derived by a
deterministic compiler from approved structured data and a versioned ruleset.

The complete reference workflow is supported:

```text
project → function =M2 → motor =M2-M1 → integrated encoder =M2-M1.B1
        → move encoder outside motor =M2-B1 → undo =M2-M1.B1
        → restart → portable export/import → equivalent compiled project
```

## What is included

- Pure Python domain model for projects, functions, components, containment, and semantic
  relations, with UUID identity throughout.
- Strict, versioned YAML rulesets and vocabulary. The built-in `ee3_2026_27` ruleset is based on
  IEC 81346-1 and IEC 81346-2:2019 concepts and is not hardcoded into UI or generic compiler code.
- Deterministic graph validation, scoped stable allocation, rendering, dependency tracking, and
  token-by-token explanations.
- Central sequence records that do not silently reuse deleted numbers or renumber survivors.
- SQLite persistence with foreign keys, WAL mode, soft deletion, Alembic migration, append-only
  revisions, and undo for structural operations.
- FastAPI API for projects, functions, components, relations, validation, FLoC, graphs, history,
  explanations, ruleset migration, inference review, imports, and exports.
- Dense React engineering workspace with manual builder, live backend preview, component tree,
  inspector, sortable/filterable FLoC, synchronized XYFlow graph, validation navigation, revision
  history, keyboard undo, and copy/export actions.
- Portable `.autords` ZIP projects plus current-state JSON, CSV, XLSX, and PDF FLoC exports.
- Review-first natural-language inference with RapidFuzz and deterministic vocabulary rules.
  Optional local sentence-transformer matching and correction-data-driven scikit-learn trainers
  predict structured fields only; neither can emit authoritative RDS.
- Pytest, Hypothesis, API, Vitest, and Playwright coverage, with a GitHub Actions merge gate.
- A single local production server on `127.0.0.1:8134` and a PyInstaller recipe for
  `AutoRDS.exe`.

## Quick start on Windows

Requirements for development are Python 3.11 or newer, Node.js, and pnpm. `uv` is preferred; the
setup script falls back to a standard Python virtual environment when `uv` is unavailable.

```powershell
./scripts/setup.ps1
./run.ps1
```

Or double-click `run.bat`. The script builds the frontend when needed, starts the local server,
waits for `/api/health`, and opens [http://127.0.0.1:8134](http://127.0.0.1:8134). Stop it with
Ctrl+C. All project data stays on the machine by default.

The default persistent directory is:

```text
%LOCALAPPDATA%\AutoRDS\
├── autords.db
├── backups\
├── exports\
├── logs\
├── models\
└── rulesets\
```

Set `AUTORDS_DATA_DIR` to use a different location, which is also useful for isolated testing.

## Development

Run the backend and frontend separately for hot reload:

```powershell
# terminal 1
cd backend
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8134 --reload

# terminal 2
cd frontend
pnpm dev
```

The Vite development server proxies `/api` to the backend. API documentation is available at
`http://127.0.0.1:8134/docs` while the backend is running without an assembled static build.

### Verification

```powershell
cd backend
./.venv/Scripts/ruff.exe check .
./.venv/Scripts/python.exe -m pytest -q

cd ../frontend
pnpm lint
pnpm exec tsc --noEmit
pnpm test
pnpm build
pnpm exec playwright install chromium
pnpm e2e
```

Backend tests include the golden EE3 examples, random valid trees, idempotence, uniqueness,
cycle rejection, dependent recompilation, stable numbering after deletion, UUID stability,
restart persistence, and portable round trips. Playwright exercises the complete milestone and
XLSX export through a running application.

## Production-local build and packaging

Assemble the built React application into FastAPI static assets:

```powershell
./scripts/build.ps1
./run.ps1
```

Build the standalone executable after setup:

```powershell
./scripts/package.ps1
```

The result is `dist\AutoRDS.exe`. The executable contains the server, compiled frontend,
built-in rulesets, migration assets, and runtime libraries. It never stores user projects inside
the executable, so replacing the application does not remove `%LOCALAPPDATA%\AutoRDS\autords.db`.

## Repository layout

```text
backend/
  app/domain/        UUID-based pure domain model
  app/standards/     strict ruleset schema, loader, and built-ins
  app/rds/           allocator, compiler, validation, dependency graph, explanation
  app/persistence/   SQLAlchemy models and SQLite configuration
  app/services/      mutations, revisions, import/export
  app/inference/     reviewable candidates, optional embeddings, structured classifiers
  app/api/           FastAPI schemas and routes
  alembic/           database migrations
  tests/             golden, property, service, API, persistence, and round-trip tests
frontend/
  src/               React engineering workspace
  e2e/               Playwright milestone regression
docs/                architecture and ruleset notes
scripts/             setup, production build, and packaging
```

See [architecture](docs/architecture.md) and [ruleset authoring](docs/rulesets.md) for the key
boundaries. The central invariant is simple: inference proposes structure; only the deterministic
compiler produces Reference Designations.

## License

See [LICENSE](LICENSE).
