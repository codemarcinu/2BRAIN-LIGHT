import logging
import google.generativeai as genai
import asyncio
from typing import Optional
from config import ProjectConfig

logger = logging.getLogger("UniversalBrain")

class UniversalBrain:
    def __init__(self, provider: str = "google"):
        self.provider = provider
        self.api_key = ProjectConfig.GOOGLE_API_KEY
        
        if self.provider == "google":
            if not self.api_key:
                logger.warning("GOOGLE_API_KEY not found. AI features might fail.")
            else:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')

    async def generate_content_async(self, user_prompt: str, system_prompt: str, format_type: str = "json", model_name: str = None) -> str:
        if self.provider == "google":
            return await self._generate_google(user_prompt, system_prompt)
        elif self.provider == "ollama":
            return await self._generate_ollama(user_prompt, system_prompt, model_name or ProjectConfig.OLLAMA_RECEIPT_MODEL)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _generate_google(self, user_prompt: str, system_prompt: str) -> str:
        try:
            # Gemini doesn't support system prompt in same way, prepending it
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Run in executor to not block async loop (genai lib is sync mostly)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, full_prompt)
            
            return response.text
        except Exception as e:
            logger.error(f"Google AI Error: {e}")
            raise

    async def _generate_ollama(self, user_prompt: str, system_prompt: str, model: str) -> str:
        # Placeholder for Ollama implementation if needed
        # Could use 'ollama' python lib or http request
        logger.warning("Ollama provider not fully implemented in adapter yet.")
        return ""
