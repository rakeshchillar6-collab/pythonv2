# vectorsearch/providers/mock.py
import numpy as np
from typing import List
from .base import EmbeddingProvider
from ..models import EmbeddingVersion

class MockProvider(EmbeddingProvider):
    """
    A mock embedding provider for testing and development.
    It generates deterministic random vectors based on a fixed seed.
    """
    def __init__(self, version: EmbeddingVersion):
        super().__init__(version)
        # Use a fixed seed to ensure embeddings are deterministic for tests
        self.rng = np.random.default_rng(seed=42)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generates a list of random embedding vectors with the correct dimension.
        The content of the texts is ignored.
        """
        if not self.version.dim:
            raise ValueError("EmbeddingVersion dimension is not set for MockProvider.")

        embeddings = []
        for _ in texts:
            vector = self.rng.random(self.version.dim, dtype=np.float32)
            if self.version.normalize:
                vector = vector / np.linalg.norm(vector)
            embeddings.append(vector.tolist())

        return embeddings
