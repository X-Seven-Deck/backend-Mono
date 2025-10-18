"""
Haystack RAG Pipeline Implementation

Production-grade RAG system with semantic search, document indexing,
and answer generation using Haystack framework.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from haystack import Pipeline, Document
from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
from haystack.components.writers import DocumentWriter
from haystack.components.retrievers import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator

from app.config import settings
from app.utils import logger


class HaystackRAGService:
    """
    Production-grade RAG service using Haystack framework
    
    Features:
    - Document indexing with embeddings
    - Semantic search with vector similarity
    - Answer generation with LLM
    - Support for multiple document stores (InMemory, Pinecone, pgvector)
    """
    
    def __init__(self):
        """Initialize RAG service with document store and pipelines"""
        self.document_store = None
        self.indexing_pipeline = None
        self.query_pipeline = None
        self.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        self._initialized = False
        
    async def initialize(self):
        """Initialize document store and pipelines"""
        if self._initialized:
            return
            
        try:
            logger.info("Initializing Haystack RAG service")
            
            # Initialize document store (InMemory for now, can switch to Pinecone/pgvector)
            self.document_store = InMemoryDocumentStore()
            
            # Build indexing pipeline
            self._build_indexing_pipeline()
            
            # Build query pipeline
            self._build_query_pipeline()
            
            self._initialized = True
            logger.info("Haystack RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}", exc_info=True)
            raise
    
    def _build_indexing_pipeline(self):
        """Build document indexing pipeline"""
        try:
            # Create document embedder
            doc_embedder = SentenceTransformersDocumentEmbedder(
                model=self.embedding_model
            )
            doc_embedder.warm_up()
            
            # Create document writer
            doc_writer = DocumentWriter(document_store=self.document_store)
            
            # Build pipeline
            self.indexing_pipeline = Pipeline()
            self.indexing_pipeline.add_component("embedder", doc_embedder)
            self.indexing_pipeline.add_component("writer", doc_writer)
            self.indexing_pipeline.connect("embedder.documents", "writer.documents")
            
            logger.info("Indexing pipeline built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build indexing pipeline: {e}", exc_info=True)
            raise
    
    def _build_query_pipeline(self):
        """Build RAG query pipeline"""
        try:
            # Create text embedder for queries
            text_embedder = SentenceTransformersTextEmbedder(
                model=self.embedding_model
            )
            text_embedder.warm_up()
            
            # Create retriever
            retriever = InMemoryEmbeddingRetriever(
                document_store=self.document_store,
                top_k=5
            )
            
            # Create prompt template
            prompt_template = """
            Answer the question based on the provided context. If the answer cannot be found in the context, say "I don't have enough information to answer this question."
            
            Context:
            {% for doc in documents %}
                {{ doc.content }}
            {% endfor %}
            
            Question: {{ query }}
            
            Answer:
            """
            
            prompt_builder = PromptBuilder(template=prompt_template)
            
            # Create LLM generator
            generator = OpenAIGenerator(
                api_key=settings.openai_api_key,
                model="gpt-4o-mini",
                generation_kwargs={
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            # Build pipeline
            self.query_pipeline = Pipeline()
            self.query_pipeline.add_component("text_embedder", text_embedder)
            self.query_pipeline.add_component("retriever", retriever)
            self.query_pipeline.add_component("prompt_builder", prompt_builder)
            self.query_pipeline.add_component("generator", generator)
            
            # Connect components
            self.query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
            self.query_pipeline.connect("retriever.documents", "prompt_builder.documents")
            self.query_pipeline.connect("prompt_builder.prompt", "generator.prompt")
            
            logger.info("Query pipeline built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build query pipeline: {e}", exc_info=True)
            raise
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Index documents into vector database
        
        Args:
            documents: List of documents with 'content' and optional 'metadata'
            batch_size: Number of documents to process at once
            
        Returns:
            Dictionary with indexing results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Indexing {len(documents)} documents")
            
            # Convert to Haystack Document format
            haystack_docs = []
            for doc in documents:
                haystack_doc = Document(
                    content=doc.get("content", ""),
                    meta=doc.get("metadata", {})
                )
                haystack_docs.append(haystack_doc)
            
            # Process in batches
            indexed_count = 0
            for i in range(0, len(haystack_docs), batch_size):
                batch = haystack_docs[i:i + batch_size]
                
                # Run indexing pipeline
                result = self.indexing_pipeline.run({
                    "embedder": {"documents": batch}
                })
                
                indexed_count += len(batch)
                logger.info(f"Indexed {indexed_count}/{len(haystack_docs)} documents")
            
            return {
                "status": "success",
                "indexed": indexed_count,
                "total": len(documents),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document indexing error: {e}", exc_info=True)
            raise
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform RAG query
        
        Args:
            query: User question
            top_k: Number of documents to retrieve
            filters: Optional metadata filters
            
        Returns:
            Dictionary with answer, sources, and confidence
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"RAG query: {query[:100]}...")
            
            # Run query pipeline
            result = self.query_pipeline.run({
                "text_embedder": {"text": query},
                "prompt_builder": {"query": query}
            })
            
            # Extract answer
            answer = result["generator"]["replies"][0] if result["generator"]["replies"] else "No answer generated"
            
            # Extract sources
            sources = []
            if "retriever" in result and "documents" in result["retriever"]:
                for doc in result["retriever"]["documents"]:
                    sources.append({
                        "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                        "score": doc.score if hasattr(doc, "score") else 0.0,
                        "metadata": doc.meta
                    })
            
            # Calculate confidence (average of document scores)
            confidence = sum(s["score"] for s in sources) / len(sources) if sources else 0.0
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"RAG query error: {e}", exc_info=True)
            raise
    
    async def get_document_count(self) -> int:
        """Get total number of indexed documents"""
        if not self._initialized:
            await self.initialize()
        
        return self.document_store.count_documents()
    
    async def clear_documents(self):
        """Clear all documents from store"""
        if not self._initialized:
            await self.initialize()
        
        self.document_store.delete_documents()
        logger.info("All documents cleared from store")


# Global RAG service instance
rag_service = HaystackRAGService()
