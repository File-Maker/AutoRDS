from __future__ import annotations

from app.standards.schema import Ruleset


class EmbeddingClassifier:
    """Optional offline semantic matcher. Its output is only a class candidate."""

    model_name = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, ruleset: Ruleset) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("Install the optional 'embeddings' dependency to enable semantic matching") from exc
        self.ruleset = ruleset
        self.model = SentenceTransformer(self.model_name, local_files_only=True)
        self.codes = list(ruleset.classes)
        descriptions = [f"{definition.name} {' '.join(definition.aliases)}" for definition in ruleset.classes.values()]
        self.embeddings = self.model.encode(descriptions, normalize_embeddings=True)

    def classify(self, text: str) -> dict[str, float | str]:
        vector = self.model.encode([text], normalize_embeddings=True)[0]
        scores = self.embeddings @ vector
        index = int(scores.argmax())
        return {"class_code": self.codes[index], "confidence": float(scores[index]), "authoritative": False}
