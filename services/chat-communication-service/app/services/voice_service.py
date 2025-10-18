"""
Voice Service for Chat & Communication
Handles text-to-speech (ElevenLabs) and speech-to-text (Whisper)
"""

import logging
import httpx
from typing import Optional
from openai import AsyncOpenAI

from app.config.settings import settings

logger = logging.getLogger(__name__)


class VoiceService:
    """Voice processing service"""
    
    def __init__(self):
        """Initialize voice service"""
        self.openai_client: Optional[AsyncOpenAI] = None
        self.elevenlabs_url = "https://api.elevenlabs.io/v1"
        self._initialized = False
    
    async def initialize(self):
        """Initialize voice service clients"""
        if self._initialized:
            return
        
        try:
            # Initialize OpenAI for Whisper
            if settings.openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            self._initialized = True
            logger.info("Voice service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice service: {e}")
            raise
    
    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs
        
        Args:
            text: Text to convert
            voice_id: ElevenLabs voice ID (optional)
            
        Returns:
            Audio bytes
        """
        try:
            if not settings.elevenlabs_api_key:
                raise Exception("ElevenLabs API key not configured")
            
            voice_id = voice_id or settings.elevenlabs_voice_id
            
            url = f"{self.elevenlabs_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": settings.elevenlabs_api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                audio_bytes = response.content
                logger.info(f"Generated TTS audio: {len(audio_bytes)} bytes")
                
                return audio_bytes
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            raise
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str = "en"
    ) -> dict:
        """
        Convert speech to text using OpenAI Whisper
        
        Args:
            audio_data: Audio bytes
            language: Language code
            
        Returns:
            Transcription result with text and confidence
        """
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not initialized")
            
            # Create a temporary file-like object
            from io import BytesIO
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.mp3"
            
            # Transcribe using Whisper
            transcription = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
            
            result = {
                "text": transcription.text,
                "language": language,
                "confidence": 0.95  # Whisper doesn't provide confidence, using default
            }
            
            logger.info(f"Transcribed audio: {result['text'][:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            raise
    
    async def get_available_voices(self) -> list:
        """Get list of available ElevenLabs voices"""
        try:
            if not settings.elevenlabs_api_key:
                return []
            
            url = f"{self.elevenlabs_url}/voices"
            
            headers = {
                "Accept": "application/json",
                "xi-api-key": settings.elevenlabs_api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                voices = data.get("voices", [])
                
                return [
                    {
                        "voice_id": v["voice_id"],
                        "name": v["name"],
                        "category": v.get("category", ""),
                        "description": v.get("description", "")
                    }
                    for v in voices
                ]
                
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []


# Global voice service instance
voice_service = VoiceService()
