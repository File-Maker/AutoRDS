from __future__ import annotations

import json
from pathlib import Path

from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

MIN_SAMPLES = 25


def train_classifier(decisions: list[dict], target: str, output: Path) -> dict:
    """Train a structured-value classifier; RDS strings are intentionally unsupported targets."""
    if target not in {"class", "function", "parent", "relation"}:
        raise ValueError("Unsupported target; models may never target RDS strings")
    rows = [(item["input"], item["approved"].get(target)) for item in decisions]
    rows = [(text, value) for text, value in rows if value is not None]
    if len(rows) < MIN_SAMPLES or len({value for _, value in rows}) < 2:
        return {"trained": False, "reason": f"At least {MIN_SAMPLES} labeled examples across two classes are required"}
    pipeline = Pipeline([("vectorizer", TfidfVectorizer(ngram_range=(1, 2))), ("classifier", LogisticRegression(max_iter=1000))])
    pipeline.fit([text for text, _ in rows], [value for _, value in rows])
    output.parent.mkdir(parents=True, exist_ok=True)
    dump(pipeline, output)
    metadata = {"target": target, "samples": len(rows), "classes": list(pipeline.classes_)}
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {"trained": True, **metadata}
