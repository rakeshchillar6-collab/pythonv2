# Semantic Search Subsystem Documentation

This document provides a detailed overview of the Semantic Search API, its models, and how to use it.

## 1. Data Models

The subsystem is built around several key models:

-   `Corpus`: A collection of documents (e.g., "Blog Posts").
-   `Document`: A single piece of content within a corpus.
-   `EmbeddingVersion`: Metadata about the AI model used for embeddings.
-   `Chunk`: A piece of text from a document, which holds the actual vector embedding.
-   `QueryLog`: Records all search queries for analysis.

## 2. Ingestion API

### Ingest a Single Document

Queues a single document for chunking and embedding.

-   **Endpoint**: `POST /api/vector/ingest/`
-   **Permission**: `admin` or `editor` role required.
-   **Body**:

```json
{
  "corpus_id": "uuid-of-the-corpus",
  "external_id": "unique-id-in-source-system",
  "title": "Document Title",
  "raw_text": "The full text content of the document...",
  "metadata": {
    "url": "/blog/my-post",
    "tags": ["django", "ai"],
    "category": "Technology"
  }
}
```

-   **Response** (`202 Accepted`):

```json
{
  "document_id": "uuid-of-the-new-document",
  "status": "processing"
}
```

-   **Example (`curl`)**:

```bash
curl -X POST http://localhost:8000/api/vector/ingest/ \
-H "Authorization: Bearer <your_jwt_token>" \
-H "Content-Type: application/json" \
-d '{...}'
```

### Ingest Multiple Documents (Bulk)

Queues multiple documents for ingestion in a single request.

-   **Endpoint**: `POST /api/vector/ingest-bulk/`
-   **Body**: An array of document objects (same structure as single ingest).
-   **Response** (`207 Multi-Status`): An array of results, one for each input document.

## 3. Search API

### Perform a Search

Executes a search query.

-   **Endpoint**: `POST /api/vector/search/`
-   **Permission**: `admin` or `editor` role required.
-   **Body**:

```json
{
  "query": "What is hybrid search?",
  "mode": "hybrid", // "vector", "bm25", "hybrid"
  "corpus_ids": ["uuid-of-corpus-1"],
  "filters": {
    "lang": "en",
    "tags": ["ai"]
  },
  "top_k": 5,
  "alpha": 0.5, // Weight for BM25 in hybrid mode (0.0 to 1.0)
  "with_snippet": true
}
```

-   **Response** (`200 OK`): An array of ranked search hits.

```json
[
  {
    "document_id": "...",
    "document_title": "Advanced Search Techniques",
    "chunk_id": "...",
    "score": 0.89,
    "snippet": "Hybrid search combines the strengths of <mark>BM25</mark> and vector search...",
    "document_metadata": {
      "url": "/blog/advanced-search"
    }
  }
]
```

-   **Example (`curl`)**:

```bash
curl -X POST http://localhost:8000/api/vector/search/ \
-H "Authorization: Bearer <your_jwt_token>" \
-H "Content-Type: application/json" \
-d '{...}'
```

## 4. Management API

### Trigger Re-embedding

Queues a task to re-embed all documents in a corpus with a new model version.

-   **Endpoint**: `POST /api/vector/reembed/`
-   **Permission**: `admin` or `editor` role required.
-   **Body**:

```json
{
  "corpus_id": "uuid-of-the-corpus-to-reembed",
  "embedding_version_id": "uuid-of-the-new-embedding-version"
}
```

-   **Response** (`202 Accepted`):

```json
{
  "status": "queued",
  "message": "Re-embedding queued for corpus ..."
}
```
---

*This documentation provides a high-level overview. For detailed field descriptions, refer to the OpenAPI/Swagger schema at `/api/schema/`.*
