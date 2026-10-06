# AutoRDS architecture

AutoRDS treats a reference designation as a reproducible compilation result, never as identity.

```text
manual edits / approved inference
              │
              ▼
structured UUID-based project graph
              │
              ▼
versioned ruleset → validator → stable allocator → renderer → explanation
              │
              ▼
derived RDS, FLoC, graph and exports
```

The pure `app/domain`, `app/standards`, and `app/rds` packages have no FastAPI, SQLAlchemy,
React, or machine-learning dependencies. The service layer owns mutations, validation,
allocation persistence, dependency-aware recompilation, soft deletion, and append-only revisions.
Routes only translate HTTP requests to service calls.

Inference produces candidate class/function/parent/relation values. Users review those values
before they become domain entities. Inference providers have no path that returns or stores an
authoritative designation.

SQLite enables foreign keys and WAL mode. The default data directory is
`%LOCALAPPDATA%\AutoRDS`; application builds never place the database inside the executable.
