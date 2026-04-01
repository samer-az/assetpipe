"""Background removal utility using rembg."""

import asyncio
import io
import logging

from PIL import Image
from rembg import remove

logger = logging.getLogger("assetpipe.background")


async def remove_background(image_bytes: bytes) -> bytes:
    """Remove the background from an image. Returns transparent PNG bytes."""
    logger.info("Removing background...")

    def _remove() -> bytes:
        input_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        output_img = remove(input_img)
        buf = io.BytesIO()
        output_img.save(buf, format="PNG")
        return buf.getvalue()

    return await asyncio.to_thread(_remove)
