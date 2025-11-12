# vectorsearch/providers/utils.py
from ..models import EmbeddingVersion
from .base import EmbeddingProvider
from .mock import MockProvider
# Import other providers here as they are created

def get_provider_instance(version: EmbeddingVersion) -> EmbeddingProvider:
    """Factory function to get an instance of an embedding provider."""
    provider_map = {
        EmbeddingVersion.Provider.MOCK: MockProvider,
        # EmbeddingVersion.Provider.OPENAI: OpenAIProvider,
    }
    provider_class = provider_map.get(version.provider)

    if not provider_class:
        raise NotImplementedError(f"Provider '{version.provider}' is not implemented.")

    return provider_class(version)
