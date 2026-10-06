AutoRDS is a local-first engineering application for constructing,
managing, validating and explaining Reference Designations.

The application has two strictly separated subsystems:

1. Semantic inference:
   Converts natural-language engineering descriptions into candidate
   structured machine objects, relationships and classifications.

2. Deterministic RDS compilation:
   Converts approved structured project data into designations according
   to a versioned ruleset.

Inference is NEVER authoritative.
Inference MUST NEVER directly generate or persist final RDS strings.
All final designations MUST originate from the deterministic compiler.

The persistent identity of every object is its UUID, never its RDS.

RDS values are derived data.

The standards/rules layer is data-driven and versioned.
Do not hardcode EE3-specific rules into UI code or generic compiler code.

All edits that affect structure must trigger dependency-aware recompilation.

Existing allocated sequence numbers remain stable unless the user explicitly
requests resequencing.

The application must work fully offline and store all projects locally.