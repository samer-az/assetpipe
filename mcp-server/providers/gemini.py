"""
Google Gemini image generation provider.
Uses the google-genai SDK for image generation and editing.
"""

import asyncio
import base64
import logging
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger("assetpipe.gemini")


class GeminiProvider:
    """Handles image generation and editing via Google Gemini."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-preview-image-generation"):
        self.model = model
        self.client = genai.Client(api_key=api_key)
        logger.info(f"Gemini provider initialized with model: {model}")

    async def generate_image(self, prompt: str) -> bytes:
        """Generate an image from a text prompt. Returns PNG bytes."""
        logger.info(f"Generating image with prompt: {prompt[:100]}...")

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None and part.inline_data.mime_type.startswith("image/"):
                return part.inline_data.data

        raise RuntimeError(
            "No image was returned by Gemini. "
            "Try rephrasing your prompt or using a different model."
        )

    async def edit_image(self, image_bytes: bytes, edit_prompt: str) -> bytes:
        """Edit an existing image based on a text prompt. Returns PNG bytes."""
        logger.info(f"Editing image with prompt: {edit_prompt[:100]}...")

        # Encode the input image
        b64_image = base64.b64encode(image_bytes).decode()

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                types.Part.from_text(text=edit_prompt),
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None and part.inline_data.mime_type.startswith("image/"):
                return part.inline_data.data

        raise RuntimeError(
            "No edited image was returned by Gemini. "
            "Try rephrasing your edit prompt."
        )

    async def check_health(self) -> dict:
        """Check if the Gemini API is accessible."""
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents="Say 'OK' in one word.",
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                ),
            )
            return {"status": "healthy", "model": self.model}
        except Exception as e:
            return {"status": "error", "model": self.model, "error": str(e)}
