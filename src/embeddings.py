"""Sentence-transformer embedding utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=4)
def load_sentence_transformer(model_name: str) -> SentenceTransformer:
    """Load and cache a sentence-transformer model."""

    return SentenceTransformer(model_name)


@dataclass(slots=True)
class EmbeddingService:
    """Generate semantic embeddings for textual profiles."""

    model_name: str
    _model: SentenceTransformer | None = field(default=None, init=False, repr=False)

    @property
    def model(self) -> SentenceTransformer:
        """Lazily load the embedding model."""

        if self._model is None:
            self._model = load_sentence_transformer(self.model_name)
        return self._model

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text input."""

        return np.asarray(self.model.encode([text], normalize_embeddings=True))[0]

    def embed_many(self, texts: Iterable[str]) -> np.ndarray:
        """Embed many text inputs at once."""

        return np.asarray(self.model.encode(list(texts), normalize_embeddings=True))
