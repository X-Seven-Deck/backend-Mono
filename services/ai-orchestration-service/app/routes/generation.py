"""
Text generation endpoints using multiple LLM providers
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import GenerateRequest, GenerateResponse
from app.core.llm_provider import llm_manager, LLMProvider
from app.utils import logger
import json

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text using LLM
    
    Supports multiple providers with automatic fallback:
    - OpenAI (GPT-4, GPT-3.5)
    - Groq (Llama 3.1)
    - Anthropic (Claude)
    """
    try:
        logger.info(f"Generating text with provider: {request.provider}")
        
        content = await llm_manager.generate(
            prompt=request.prompt,
            provider=LLMProvider(request.provider.value),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_message=request.system_message
        )
        
        return GenerateResponse(
            content=content,
            provider=request.provider.value,
            tokens_used=None  # Could be calculated if needed
        )
    
    except Exception as e:
        logger.error(f"Text generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stream")
async def generate_text_stream(request: GenerateRequest):
    """
    Generate text with streaming response
    
    Returns Server-Sent Events (SSE) stream
    """
    if not request.stream:
        raise HTTPException(status_code=400, detail="Streaming must be enabled")
    
    async def event_generator():
        try:
            async for chunk in llm_manager.generate_streaming(
                prompt=request.prompt,
                provider=LLMProvider(request.provider.value),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_message=request.system_message
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            yield "data: [DONE]\n\n"
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.post("/embeddings")
async def generate_embeddings(texts: list[str], model: str = "text-embedding-3-small"):
    """
    Generate embeddings for texts
    
    Used for semantic search and RAG
    """
    try:
        embeddings = await llm_manager.get_embeddings(
            texts=texts,
            provider=LLMProvider.OPENAI,
            model=model
        )
        
        return {
            "embeddings": embeddings,
            "model": model,
            "count": len(embeddings)
        }
    
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
