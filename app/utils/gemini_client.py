"""Gemini API client with structured output support."""
import json
from typing import Any, Optional, Type

import google.generativeai as genai
import structlog
from pydantic import BaseModel

from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()

# Configure Gemini
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)


class GeminiClient:
    """Client for Google Gemini API with structured output support."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name
        self.model = None
        if settings.gemini_api_key:
            self.model = genai.GenerativeModel(model_name)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text from a prompt."""
        if not self.model:
            raise ValueError("Gemini API key not configured")

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if system_prompt:
            chat = self.model.start_chat(
                history=[
                    {"role": "user", "parts": [system_prompt]},
                    {"role": "model", "parts": ["Understood. I will follow these instructions."]},
                ]
            )
            response = chat.send_message(prompt, generation_config=generation_config)
        else:
            response = self.model.generate_content(
                prompt, generation_config=generation_config
            )

        return response.text

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> BaseModel:
        """Generate structured JSON output using a Pydantic model."""
        if not self.model:
            raise ValueError("Gemini API key not configured")

        # Build the prompt with JSON schema instructions
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)

        full_prompt = (
            f"{prompt}\n\n"
            f"Respond ONLY with valid JSON matching this schema:\n"
            f"{schema_json}\n\n"
            f"Output:"
        )

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "response_mime_type": "application/json",
        }

        try:
            if system_prompt:
                chat = self.model.start_chat(
                    history=[
                        {"role": "user", "parts": [system_prompt]},
                        {"role": "model", "parts": ["Understood. I will follow these instructions."]},
                    ]
                )
                response = chat.send_message(full_prompt, generation_config=generation_config)
            else:
                response = self.model.generate_content(
                    full_prompt, generation_config=generation_config
                )

            # Parse the response into the Pydantic model
            text = response.text.strip()
            # Handle markdown code blocks
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            parsed = json.loads(text)
            return response_model.model_validate(parsed)

        except json.JSONDecodeError as e:
            log.error("gemini.json_parse_error", error=str(e), response=text)
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
        except Exception as e:
            log.error("gemini.generation_error", error=str(e))
            raise

    async def analyze_image(
        self,
        image_url: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Analyze an image using Gemini Vision."""
        if not self.model:
            raise ValueError("Gemini API key not configured")

        try:
            # Fetch the image
            import httpx
            async with httpx.AsyncClient() as client:
                image_response = await client.get(image_url)
                image_response.raise_for_status()
                image_bytes = image_response.content

            image_part = {
                "mime_type": "image/jpeg",
                "data": image_bytes,
            }

            full_prompt = prompt

            if system_prompt:
                chat = self.model.start_chat(
                    history=[
                        {"role": "user", "parts": [system_prompt]},
                        {"role": "model", "parts": ["Understood."]},
                    ]
                )
                response = chat.send_message([image_part, full_prompt])
            else:
                response = self.model.generate_content([image_part, full_prompt])

            return response.text

        except Exception as e:
            log.error("gemini.image_analysis_error", error=str(e))
            raise

    async def analyze_image_structured(
        self,
        image_url: str,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        """Analyze an image and return structured JSON."""
        if not self.model:
            raise ValueError("Gemini API key not configured")

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                image_response = await client.get(image_url)
                image_response.raise_for_status()
                image_bytes = image_response.content

            image_part = {
                "mime_type": "image/jpeg",
                "data": image_bytes,
            }

            schema_json = json.dumps(response_model.model_json_schema(), indent=2)

            full_prompt = (
                f"{prompt}\n\n"
                f"Respond ONLY with valid JSON matching this schema:\n"
                f"{schema_json}\n\n"
                f"Output:"
            )

            generation_config = {
                "temperature": 0.3,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json",
            }

            if system_prompt:
                chat = self.model.start_chat(
                    history=[
                        {"role": "user", "parts": [system_prompt]},
                        {"role": "model", "parts": ["Understood."]},
                    ]
                )
                response = chat.send_message([image_part, full_prompt], generation_config=generation_config)
            else:
                response = self.model.generate_content(
                    [image_part, full_prompt], generation_config=generation_config
                )

            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            parsed = json.loads(text)
            return response_model.model_validate(parsed)

        except json.JSONDecodeError as e:
            log.error("gemini.image_json_parse_error", error=str(e))
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
        except Exception as e:
            log.error("gemini.image_analysis_error", error=str(e))
            raise


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get the Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client