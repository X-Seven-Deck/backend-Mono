"""
LLM Provider Manager

Handles multiple LLM providers (OpenAI, Groq, Anthropic) with fallback support
and unified interface for AI operations.
"""

from typing import Optional, List, Dict, Any, AsyncIterator
from enum import Enum
import openai
from groq import Groq
from anthropic import Anthropic
from app.config import settings
from app.utils import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"


class LLMManager:
    """
    Unified LLM manager with multi-provider support and automatic fallback
    """
    
    def __init__(self):
        self.openai_client: Optional[openai.AsyncOpenAI] = None
        self.groq_client: Optional[Groq] = None
        self.anthropic_client: Optional[Anthropic] = None
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize all available LLM clients"""
        
        # OpenAI
        if settings.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")
        
        # Groq
        if settings.groq_api_key:
            self.groq_client = Groq(api_key=settings.groq_api_key)
            logger.info("Groq client initialized")
        
        # Anthropic
        if settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        prompt: str,
        provider: LLMProvider = LLMProvider.OPENAI,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion from LLM
        
        Args:
            prompt: User prompt
            provider: LLM provider to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_message: Optional system message
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Generated text
        """
        try:
            if provider == LLMProvider.OPENAI and self.openai_client:
                return await self._generate_openai(
                    prompt, temperature, max_tokens, system_message, **kwargs
                )
            elif provider == LLMProvider.GROQ and self.groq_client:
                return await self._generate_groq(
                    prompt, temperature, max_tokens, system_message, **kwargs
                )
            elif provider == LLMProvider.ANTHROPIC and self.anthropic_client:
                return await self._generate_anthropic(
                    prompt, temperature, max_tokens, system_message, **kwargs
                )
            else:
                # Fallback to available provider
                return await self._generate_with_fallback(
                    prompt, temperature, max_tokens, system_message, **kwargs
                )
        except Exception as e:
            logger.error(f"LLM generation error with {provider}: {e}")
            # Try fallback
            return await self._generate_with_fallback(
                prompt, temperature, max_tokens, system_message, **kwargs
            )
    
    async def _generate_openai(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_message: Optional[str],
        **kwargs
    ) -> str:
        """Generate using OpenAI"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=kwargs.get("model", settings.openai_model),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **{k: v for k, v in kwargs.items() if k != "model"}
        )
        
        return response.choices[0].message.content
    
    async def _generate_groq(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_message: Optional[str],
        **kwargs
    ) -> str:
        """Generate using Groq"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        response = self.groq_client.chat.completions.create(
            model=kwargs.get("model", settings.groq_model),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
    
    async def _generate_anthropic(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_message: Optional[str],
        **kwargs
    ) -> str:
        """Generate using Anthropic"""
        response = self.anthropic_client.messages.create(
            model=kwargs.get("model", settings.anthropic_model),
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_message or "You are a helpful AI assistant.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_with_fallback(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_message: Optional[str],
        **kwargs
    ) -> str:
        """Try all available providers in order"""
        providers = [
            (LLMProvider.OPENAI, self.openai_client),
            (LLMProvider.GROQ, self.groq_client),
            (LLMProvider.ANTHROPIC, self.anthropic_client),
        ]
        
        for provider, client in providers:
            if client:
                try:
                    logger.info(f"Attempting fallback to {provider}")
                    if provider == LLMProvider.OPENAI:
                        return await self._generate_openai(
                            prompt, temperature, max_tokens, system_message, **kwargs
                        )
                    elif provider == LLMProvider.GROQ:
                        return await self._generate_groq(
                            prompt, temperature, max_tokens, system_message, **kwargs
                        )
                    elif provider == LLMProvider.ANTHROPIC:
                        return await self._generate_anthropic(
                            prompt, temperature, max_tokens, system_message, **kwargs
                        )
                except Exception as e:
                    logger.warning(f"Fallback to {provider} failed: {e}")
                    continue
        
        raise Exception("All LLM providers failed")
    
    async def generate_streaming(
        self,
        prompt: str,
        provider: LLMProvider = LLMProvider.OPENAI,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate streaming text completion
        
        Args:
            prompt: User prompt
            provider: LLM provider to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_message: Optional system message
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Text chunks as they are generated
        """
        if provider == LLMProvider.OPENAI and self.openai_client:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            stream = await self.openai_client.chat.completions.create(
                model=kwargs.get("model", settings.openai_model),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
    
    async def get_embeddings(
        self,
        texts: List[str],
        provider: LLMProvider = LLMProvider.OPENAI,
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of texts to embed
            provider: LLM provider to use
            model: Embedding model name
        
        Returns:
            List of embedding vectors
        """
        if provider == LLMProvider.OPENAI and self.openai_client:
            response = await self.openai_client.embeddings.create(
                model=model,
                input=texts
            )
            return [item.embedding for item in response.data]
        else:
            raise ValueError(f"Embeddings not supported for provider: {provider}")


# Global LLM manager instance
llm_manager = LLMManager()
