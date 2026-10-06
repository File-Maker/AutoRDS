# Ruleset authoring

Built-in standards live under `backend/app/standards/builtin`. A ruleset declares aspect
prefixes, function patterns, containment syntax, stable-numbering behavior, validation
severities, and class vocabulary. The generic compiler reads the validated schema and contains
no EE3-specific UI or rendering branches.

Rulesets are parsed with `yaml.safe_load` and validated by strict Pydantic v2 models. Unknown
fields, malformed codes, unsupported allocation strategies, or incomplete structures are
rejected. A migration must be previewed before it is applied; the preview reports unchanged,
changed, invalid, and ambiguous objects, and applying it creates a revision.
