# AutoRDS v0.1.0 — First Engineering Preview

AutoRDS is a local-first workspace for building, validating, explaining, and exporting Reference
Designations. This first release establishes the deterministic engineering foundation: project
objects keep stable UUID identities, while every displayed RDS is derived from approved structure
using a versioned ruleset.

## Highlights

- Build projects from functions, components, containment, and semantic relationships.
- Compile Reference Designations deterministically with the built-in `ee3_2026_27` ruleset.
- Keep allocated sequence numbers stable when objects are moved, edited, or deleted.
- Validate project structure and navigate directly to reported issues.
- Inspect token-by-token explanations showing how each designation was produced.
- Browse the project as a component tree, sortable/filterable FLoC table, or synchronized graph.
- Review revision history and undo structural changes.
- Export current project data as JSON, CSV, XLSX, or PDF.
- Export and import portable `.autords` project archives.
- Run locally on Windows through a standalone executable or from source.
- Keep projects on the local machine in SQLite; no cloud account or network connection is required.

## Safety by design

AutoRDS deliberately separates two responsibilities:

1. The inference assistant may propose structured engineering objects and classifications.
2. Only the deterministic compiler can produce final Reference Designations.

Suggestions must be reviewed before they become project data. Free-text descriptions never
directly overwrite structure or authoritative designations, and an object's UUID remains its
persistent identity even when its RDS changes.

## Natural-language assistance in this release

The Queries workspace can recognize a limited set of engineering phrases using local vocabulary
rules and fuzzy matching, then present candidates for review. This is an early assistance feature,
not a complete trained ML workflow.

Current limitations include:

- component descriptions are stored as metadata and are not analyzed automatically;
- inference coverage is limited, especially for semantic relationships and references between
  several objects proposed in the same query;
- optional embedding and correction-training modules are not yet exposed as a complete end-user
  workflow;
- accepted corrections are recorded, but this release does not continuously retrain and deploy a
  model from them.

Manual project construction and deterministic RDS compilation are the dependable production path
in v0.1.0.

## Install and run

### Standalone Windows build

1. Download `AutoRDS.exe` from the release assets.
2. Run the executable. AutoRDS starts a private local service and opens the workspace at
   `http://127.0.0.1:8134`.
3. Keep the console window open while using the application; close it to stop AutoRDS.

Windows may show a SmartScreen warning because this preview build is not code-signed. The release
currently provides a portable executable rather than an installer or automatic updater.

Project data is stored separately from the executable under:

```text
%LOCALAPPDATA%\AutoRDS\
```

Replacing the executable does not remove the local project database. Export important projects as
`.autords` archives before upgrading or moving to another computer.

### Run from source

Development requires Python 3.11 or newer, Node.js, and pnpm. Follow the setup and launch steps in
the repository README.

## Included quality checks

The repository includes backend unit and property tests, API tests, frontend tests, and a
Playwright milestone workflow. Coverage includes deterministic compilation, cycle rejection,
stable numbering, UUID stability, persistence across restart, undo, portable project round trips,
and spreadsheet export.

## Known limitations

- This is an engineering preview and should be independently verified before use in
  safety-critical or contractual documentation.
- The bundled ruleset is the initial project-specific interpretation; AutoRDS is not a substitute
  for access to the applicable IEC/ISO standards or an organization's engineering policy.
- Graph topology can be inspected and synchronized with other views, but not fully edited from the
  graph in this release.
- Ruleset migration and some advanced data-management operations are currently API-oriented rather
  than complete guided UI workflows.
- Portable import restores project structure; inference-decision and revision-history restoration
  is not yet complete.
- The standalone release targets Windows and is not yet distributed through a signed installer.

## Feedback

Please report reproducible problems through the repository issue tracker. Include the AutoRDS
version, the action being performed, the expected result, and—when it does not contain sensitive
engineering data—a minimal `.autords` project that demonstrates the issue.

Thank you for trying the first AutoRDS release.
