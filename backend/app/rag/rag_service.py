"""
RAG Service for AD Clinical Knowledge Retrieval
Uses Vertex AI Text Embeddings + Vector Search
"""

import logging
from typing import List, Dict, Any
import os

from app.rag.rag_config import DEFAULT_RAG_CONFIG, AD_CLINICAL_KNOWLEDGE

logger = logging.getLogger(__name__)


class ADRAGService:
    """
    Retrieval-Augmented Generation service for AD clinical knowledge
    """

    def __init__(self, config=None):
        self.config = config or DEFAULT_RAG_CONFIG
        self.embeddings_client = None
        self.vector_store = None
        self.is_initialized = False

    def initialize(self):
        """Initialize Vertex AI embeddings and vector store"""
        try:
            from google.cloud import aiplatform
            from langchain_google_vertexai import VertexAIEmbeddings

            # Initialize Vertex AI
            aiplatform.init(
                project=self.config.project_id,
                location=self.config.region
            )

            # Initialize embeddings model
            self.embeddings_client = VertexAIEmbeddings(
                model_name=self.config.embedding_model,
                project=self.config.project_id
            )

            self.is_initialized = True
            logger.info("RAG service initialized successfully")

        except ImportError as e:
            logger.warning(f"Vertex AI packages not available: {e}. RAG disabled.")
            self.is_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            self.is_initialized = False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text documents

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not self.is_initialized:
            logger.warning("RAG not initialized, returning empty embeddings")
            return [[0.0] * self.config.embedding_dimension for _ in texts]

        try:
            embeddings = self.embeddings_client.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * self.config.embedding_dimension for _ in texts]

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query string

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        if not self.is_initialized:
            return [0.0] * self.config.embedding_dimension

        try:
            embedding = self.embeddings_client.embed_query(query)
            return embedding
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return [0.0] * self.config.embedding_dimension

    def retrieve_relevant_knowledge(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant clinical knowledge for a query

        Args:
            query: Clinical query (e.g., "How to differentiate AD from psoriasis?")
            top_k: Number of results to return

        Returns:
            List of relevant knowledge sources with scores
        """
        top_k = top_k or self.config.num_neighbors

        if not self.is_initialized:
            # Fallback: Simple keyword matching
            logger.info("Using fallback keyword matching for RAG")
            return self._fallback_keyword_search(query, top_k)

        try:
            # Embed the query
            query_embedding = self.embed_query(query)

            # For now, use in-memory similarity search
            # TODO: Replace with Vertex AI Vector Search for production
            from numpy import dot
            from numpy.linalg import norm

            results = []
            for doc in AD_CLINICAL_KNOWLEDGE:
                # Embed document content
                doc_embedding = self.embed_query(doc["content"][:500])  # First 500 chars

                # Calculate cosine similarity
                similarity = dot(query_embedding, doc_embedding) / (
                    norm(query_embedding) * norm(doc_embedding) + 1e-10
                )

                results.append({
                    "source": doc,
                    "similarity_score": float(similarity),
                    "relevance": doc["relevance_score"]
                })

            # Sort by similarity and return top-k
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")
            return self._fallback_keyword_search(query, top_k)

    def _fallback_keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Simple keyword-based fallback when embeddings unavailable"""
        query_lower = query.lower()
        keywords = query_lower.split()

        results = []
        for doc in AD_CLINICAL_KNOWLEDGE:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()

            # Simple keyword matching score
            score = sum(
                1 for keyword in keywords
                if keyword in content_lower or keyword in title_lower
            ) / len(keywords)

            results.append({
                "source": doc,
                "similarity_score": score,
                "relevance": doc["relevance_score"]
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def augment_prompt_with_knowledge(
        self,
        base_prompt: str,
        clinical_query: str,
        top_k: int = 3
    ) -> str:
        """
        Augment a prompt with relevant clinical knowledge

        Args:
            base_prompt: Original prompt
            clinical_query: What clinical knowledge is needed
            top_k: Number of knowledge sources to include

        Returns:
            Enhanced prompt with clinical context
        """
        # Retrieve relevant knowledge
        knowledge_results = self.retrieve_relevant_knowledge(clinical_query, top_k)

        if not knowledge_results:
            return base_prompt

        # Build knowledge context
        knowledge_context = "\n\n=== CLINICAL KNOWLEDGE BASE ===\n\n"

        for idx, result in enumerate(knowledge_results, 1):
            source = result["source"]
            knowledge_context += f"[Source {idx}: {source['title']}]\n"
            knowledge_context += f"{source['content'][:1500]}...\n\n"  # Truncate long content

        # Combine with base prompt
        augmented_prompt = f"{base_prompt}\n\n{knowledge_context}\n\nPlease use the clinical knowledge provided above to inform your analysis."

        logger.info(f"Augmented prompt with {len(knowledge_results)} knowledge sources")
        return augmented_prompt


# Global instance
rag_service = ADRAGService()
