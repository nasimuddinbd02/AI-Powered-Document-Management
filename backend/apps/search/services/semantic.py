"""
Semantic search service.

Uses OpenAI embeddings and FAISS for vector similarity search
over document chunks.
"""

import logging
import os
from typing import Optional

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

# FAISS index path
FAISS_INDEX_DIR = os.path.join(settings.BASE_DIR, "faiss_indexes")


class SemanticSearchService:
    """
    Provides semantic (vector) search over document embeddings.

    Uses OpenAI embedding models to encode queries and FAISS for
    fast approximate nearest-neighbour lookup.
    """

    def __init__(self):
        self._index = None
        self._id_map = {}  # Maps FAISS index positions to document IDs
        self._embeddings_client = None

    def _get_embeddings_client(self):
        """Lazy-load the OpenAI embeddings client."""
        if self._embeddings_client is None:
            try:
                from langchain_openai import OpenAIEmbeddings
                self._embeddings_client = OpenAIEmbeddings(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_EMBEDDING_MODEL,
                )
            except Exception as e:
                logger.error("Failed to initialise OpenAI embeddings client: %s", e)
                raise
        return self._embeddings_client

    def _load_faiss_index(self):
        """Load the FAISS index from disk if available."""
        if self._index is not None:
            return

        try:
            import faiss
            index_path = os.path.join(FAISS_INDEX_DIR, "document_index.faiss")
            id_map_path = os.path.join(FAISS_INDEX_DIR, "id_map.npy")

            if os.path.exists(index_path) and os.path.exists(id_map_path):
                self._index = faiss.read_index(index_path)
                self._id_map = np.load(id_map_path, allow_pickle=True).item()
                logger.info("Loaded FAISS index with %d vectors", self._index.ntotal)
            else:
                logger.info("No FAISS index found — will create on first indexing.")
        except ImportError:
            logger.warning("FAISS not available — semantic search will be unavailable.")
        except Exception as e:
            logger.error("Error loading FAISS index: %s", e)

    def search(self, query, user=None, top_k=10):
        """
        Perform semantic search over document embeddings.

        Args:
            query: Natural language search query.
            user: Optional user for access filtering.
            top_k: Number of results to return.

        Returns:
            list[dict]: List of results with document_id, chunk_text, score.
        """
        from apps.ai_engine.models import DocumentEmbedding

        try:
            client = self._get_embeddings_client()
            query_embedding = client.embed_query(query)
        except Exception as e:
            logger.error("Failed to generate query embedding: %s", e)
            return []

        # Try FAISS first
        self._load_faiss_index()
        if self._index is not None and self._index.ntotal > 0:
            return self._search_faiss(query_embedding, user, top_k)

        # Fallback: brute-force cosine similarity over DB embeddings
        return self._search_brute_force(query_embedding, user, top_k)

    def _search_faiss(self, query_embedding, user, top_k):
        """Search using the FAISS index."""
        import faiss
        from apps.ai_engine.models import DocumentEmbedding
        from apps.documents.models import Document

        query_vector = np.array([query_embedding], dtype="float32")
        scores, indices = self._index.search(query_vector, top_k * 2)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            embedding_id = self._id_map.get(int(idx))
            if embedding_id is None:
                continue

            try:
                emb = DocumentEmbedding.objects.select_related("document").get(id=embedding_id)
                doc = emb.document
                # Access check
                if user and not user.is_staff:
                    if doc.owner_id != user.id and not doc.access_records.filter(user=user).exists():
                        continue

                results.append({
                    "document_id": doc.id,
                    "document_uuid": str(doc.uuid),
                    "document_title": doc.title,
                    "chunk_text": emb.chunk_text,
                    "chunk_index": emb.chunk_index,
                    "score": float(score),
                })
            except DocumentEmbedding.DoesNotExist:
                continue

            if len(results) >= top_k:
                break

        return results

    def _search_brute_force(self, query_embedding, user, top_k):
        """Brute-force cosine similarity search when FAISS is unavailable."""
        from apps.ai_engine.models import DocumentEmbedding

        embeddings = DocumentEmbedding.objects.select_related("document").all()

        if user and not user.is_staff:
            from django.db.models import Q
            embeddings = embeddings.filter(
                Q(document__owner=user) | Q(document__access_records__user=user)
            ).distinct()

        results = []
        query_vec = np.array(query_embedding, dtype="float32")
        query_norm = np.linalg.norm(query_vec)

        if query_norm == 0:
            return []

        for emb in embeddings:
            if not emb.embedding_vector:
                continue
            try:
                emb_vec = np.array(emb.embedding_vector, dtype="float32")
                emb_norm = np.linalg.norm(emb_vec)
                if emb_norm == 0:
                    continue
                similarity = float(np.dot(query_vec, emb_vec) / (query_norm * emb_norm))
                results.append({
                    "document_id": emb.document.id,
                    "document_uuid": str(emb.document.uuid),
                    "document_title": emb.document.title,
                    "chunk_text": emb.chunk_text,
                    "chunk_index": emb.chunk_index,
                    "score": similarity,
                })
            except Exception:
                continue

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def index_document(self, document_id, chunks, embeddings_list):
        """
        Add document chunks and their embeddings to the FAISS index.

        Args:
            document_id: The document's primary key.
            chunks: List of text chunks.
            embeddings_list: Corresponding list of embedding vectors.
        """
        from apps.ai_engine.models import DocumentEmbedding

        # Store in DB
        embedding_ids = []
        for i, (chunk, emb_vec) in enumerate(zip(chunks, embeddings_list)):
            db_emb, _ = DocumentEmbedding.objects.update_or_create(
                document_id=document_id,
                chunk_index=i,
                defaults={
                    "chunk_text": chunk,
                    "embedding_vector": emb_vec,
                    "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
                    "vector_dimension": len(emb_vec),
                },
            )
            embedding_ids.append(db_emb.id)

        # Update FAISS index
        self._update_faiss_index(embedding_ids, embeddings_list)

    def _update_faiss_index(self, embedding_ids, embeddings_list):
        """Add new vectors to the FAISS index and save to disk."""
        try:
            import faiss

            os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
            vectors = np.array(embeddings_list, dtype="float32")
            dim = vectors.shape[1]

            self._load_faiss_index()
            if self._index is None:
                self._index = faiss.IndexFlatIP(dim)  # Inner product (cosine on normalized)
                self._id_map = {}

            start_id = self._index.ntotal
            # Normalize for cosine similarity
            faiss.normalize_L2(vectors)
            self._index.add(vectors)

            for offset, emb_id in enumerate(embedding_ids):
                self._id_map[start_id + offset] = emb_id

            # Persist
            faiss.write_index(self._index, os.path.join(FAISS_INDEX_DIR, "document_index.faiss"))
            np.save(os.path.join(FAISS_INDEX_DIR, "id_map.npy"), self._id_map)

            logger.info("FAISS index updated — total vectors: %d", self._index.ntotal)
        except ImportError:
            logger.warning("FAISS not installed — skipping index update.")
        except Exception as e:
            logger.error("Error updating FAISS index: %s", e)
