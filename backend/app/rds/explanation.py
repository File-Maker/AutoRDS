from __future__ import annotations

from app.domain.models import CompiledDesignation


def explain(compiled: CompiledDesignation) -> dict[str, object]:
    return {
        "designation": compiled.designation,
        "summary": " · ".join(f"{token.value}: {token.meaning}" for token in compiled.tokens),
        "tokens": [{"value": token.value, "meaning": token.meaning} for token in compiled.tokens],
        "valid": compiled.valid,
        "issues": [
            {
                "code": issue.code,
                "severity": issue.severity,
                "message": issue.message,
                "possible_fix": issue.possible_fix,
            }
            for issue in compiled.issues
        ],
    }
