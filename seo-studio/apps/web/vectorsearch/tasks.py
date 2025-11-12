# vectorsearch/tasks.py
import logging
import numpy as np
from celery import shared_task
from .models import TextChunk

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def generate_embedding_for_chunk(self, chunk_id: str):
    """
    Celery task to generate and save an embedding for a TextChunk.

    In a real implementation, this would call an external embedding service
    (like OpenAI, a local model via Ollama, etc.). For now, it generates
    a random vector to simulate the process.
    """
    try:
        chunk = TextChunk.objects.get(id=chunk_id)
        logger.info(f"Generating embedding for TextChunk ID: {chunk.id}")

        # --- SIMULATED EMBEDDING GENERATION ---
        # Replace this with your actual embedding model call
        embedding_dimension = 1536  # Must match VectorField dimension
        random_vector = np.random.rand(embedding_dimension).tolist()
        # ------------------------------------

        chunk.embedding = random_vector
        chunk.save(update_fields=['embedding'])

        logger.info(f"Successfully generated and saved embedding for TextChunk ID: {chunk.id}")
        return f"Embedding generated for chunk {chunk_id}"

    except TextChunk.DoesNotExist:
        logger.error(f"TextChunk with ID {chunk_id} not found.")
        # Do not retry if the object doesn't exist
        return f"Failed: TextChunk {chunk_id} not found."
    except Exception as e:
        logger.error(f"Error generating embedding for chunk {chunk_id}: {e}")
        # Retry the task, e.g., in case of a temporary network issue with an external API
        raise self.retry(exc=e, countdown=60, max_retries=3)
