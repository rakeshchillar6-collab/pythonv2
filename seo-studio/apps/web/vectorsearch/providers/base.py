# vectorsearch/providers/base.py
from abc import ABC, abstractmethod
from typing import List
from ..models import EmbeddingVersion

class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    Defines the interface for embedding lists of texts.
    """
    def __init__(self, version: EmbeddingVersion):
        self.version = version

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of texts and returns a list of embedding vectors.
        This method must be implemented by subclasses.
        """
        pass

    def get_embedding_version(self) -> EmbeddingVersion:
        """Returns the EmbeddingVersion associated with this provider."""
        return self.version
