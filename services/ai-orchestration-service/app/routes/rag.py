"""
RAG (Retrieval-Augmented Generation) endpoints using Haystack
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import RAGQueryRequest, RAGQueryResponse
from app.services.haystack_rag import rag_service
from app.utils import logger

router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Perform RAG query
    
    Retrieves relevant context from knowledge base and generates answer.
    Uses Haystack for semantic search and LLM for generation.
    """
    try:
        logger.info(f"RAG query: {request.query[:50]}...")
        
        # Perform RAG query using Haystack
        result = await rag_service.query(
            query=request.query,
            top_k=request.top_k if hasattr(request, 'top_k') else 5
        )
        
        return RAGQueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
    
    except Exception as e:
        logger.error(f"RAG query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
async def index_documents(documents: list[dict]):
    """
    Index documents into vector database
    
    Accepts documents with content and metadata for RAG retrieval
    """
    try:
        logger.info(f"Indexing {len(documents)} documents")
        
        # Index documents using Haystack
        result = await rag_service.index_documents(documents)
        
        return result
    
    except Exception as e:
        logger.error(f"Document indexing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        document_count = await rag_service.get_document_count()
        
        return {
            "status": "operational",
            "document_count": document_count,
            "embedding_model": rag_service.embedding_model
        }
    
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents")
async def clear_documents():
    """Clear all documents from RAG system"""
    try:
        await rag_service.clear_documents()
        
        return {
            "status": "success",
            "message": "All documents cleared"
        }
    
    except Exception as e:
        logger.error(f"Error clearing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
