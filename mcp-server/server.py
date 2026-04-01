#!/usr/bin/env python3
"""
AssetPipe — MCP Server
Generates web design assets (heroes, icons, backgrounds, etc.) using Google Gemini.
"""

import asyncio
import base64
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from providers.gemini import GeminiProvider

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("assetpipe")

IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", "./generated-images")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# ---------------------------------------------------------------------------
# Prompt Enhancement Templates
# ---------------------------------------------------------------------------

ASSET_TEMPLATES = {
    "hero": {
        "prefix": "Professional hero banner image for a website.",
        "suffix": "High resolution, cinematic composition, modern web design aesthetic, wide aspect ratio, clean and impactful.",
        "default_size": "1536x768",
    },
    "icon": {
        "prefix": "Minimal vector-style icon for web UI.",
        "suffix": "Clean lines, flat design, centered composition, transparent-friendly, consistent stroke weight, modern UI style.",
        "default_size": "512x512",
    },
    "logo": {
        "prefix": "Professional logo design.",
        "suffix": "Clean, memorable, scalable, modern typography, balanced composition, works on light and dark backgrounds.",
        "default_size": "1024x1024",
    },
    "background": {
        "prefix": "Seamless website background pattern or texture.",
        "suffix": "Subtle, non-distracting, tileable, modern aesthetic, suitable as CSS background, low visual noise.",
        "default_size": "1024x1024",
    },
    "thumbnail": {
        "prefix": "Eye-catching thumbnail image.",
        "suffix": "Bold composition, high contrast, clear focal point, works at small sizes, engaging and clickable.",
        "default_size": "640x360",
    },
    "illustration": {
        "prefix": "Modern web illustration.",
        "suffix": "Flat design style, vibrant but harmonious colors, clean shapes, suitable for landing pages and feature sections.",
        "default_size": "1024x768",
    },
    "avatar": {
        "prefix": "User avatar or profile picture placeholder.",
        "suffix": "Friendly, approachable, clean circular composition, modern flat style, neutral background.",
        "default_size": "256x256",
    },
    "banner": {
        "prefix": "Promotional web banner.",
        "suffix": "Attention-grabbing, clear visual hierarchy, space for text overlay, modern marketing design.",
        "default_size": "1200x628",
    },
    "product": {
        "prefix": "Product showcase image for e-commerce.",
        "suffix": "Clean white or neutral background, professional lighting, centered subject, high detail, commercial photography style.",
        "default_size": "1024x1024",
    },
    "custom": {
        "prefix": "",
        "suffix": "High quality, professional, suitable for web use.",
        "default_size": "1024x1024",
    },
}

STYLE_MODIFIERS = {
    "photorealistic": "Photorealistic, high-resolution photograph, natural lighting, realistic textures and materials.",
    "flat": "Flat design, solid colors, minimal shadows, clean geometric shapes, modern UI aesthetic.",
    "3d": "3D rendered, soft lighting, subtle shadows, depth and dimension, modern 3D illustration style.",
    "watercolor": "Watercolor painting style, soft edges, organic color blending, artistic and elegant.",
    "minimal": "Minimalist design, lots of whitespace, simple shapes, restrained color palette, elegant simplicity.",
    "gradient": "Modern gradient design, smooth color transitions, vibrant yet professional, contemporary web aesthetic.",
    "isometric": "Isometric perspective, 3D-like flat design, consistent angle, technical but friendly illustration style.",
    "line-art": "Line art illustration, clean outlines, minimal fills, hand-drawn feel, modern sketch style.",
    "glassmorphism": "Glassmorphism style, frosted glass effect, transparency, subtle blur, modern UI trend.",
    "neon": "Neon glow style, dark background, vibrant glowing elements, cyberpunk-inspired, bold and modern.",
}

# ---------------------------------------------------------------------------
# Server Setup
# ---------------------------------------------------------------------------

app = Server("assetpipe")
provider: Optional[GeminiProvider] = None


def get_provider() -> GeminiProvider:
    global provider
    if provider is None:
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Get one free at https://aistudio.google.com/"
            )
        provider = GeminiProvider(api_key=GEMINI_API_KEY, model=GEMINI_MODEL)
    return provider


def ensure_output_dir(subdir: str = "") -> Path:
    path = Path(IMAGE_OUTPUT_DIR)
    if subdir:
        path = path / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_enhanced_prompt(
    user_prompt: str,
    asset_type: str = "custom",
    style: str = "",
    color_palette: str = "",
    brand_context: str = "",
) -> str:
    """Build an enhanced prompt from user input + asset template + style."""
    template = ASSET_TEMPLATES.get(asset_type, ASSET_TEMPLATES["custom"])
    parts = []

    if template["prefix"]:
        parts.append(template["prefix"])

    parts.append(user_prompt)

    if style and style in STYLE_MODIFIERS:
        parts.append(STYLE_MODIFIERS[style])

    if color_palette:
        parts.append(f"Color palette: {color_palette}.")

    if brand_context:
        parts.append(f"Brand context: {brand_context}.")

    if template["suffix"]:
        parts.append(template["suffix"])

    return " ".join(parts)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate_web_asset",
            description=(
                "Generate a web design image asset using AI. Supports: hero images, "
                "icons, logos, backgrounds, thumbnails, illustrations, avatars, banners, "
                "product images, and custom assets. Automatically enhances prompts for "
                "web design quality."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Description of the image to generate",
                    },
                    "asset_type": {
                        "type": "string",
                        "enum": list(ASSET_TEMPLATES.keys()),
                        "default": "custom",
                        "description": "Type of web asset to generate",
                    },
                    "style": {
                        "type": "string",
                        "enum": list(STYLE_MODIFIERS.keys()),
                        "default": "",
                        "description": "Visual style modifier (optional)",
                    },
                    "filename": {
                        "type": "string",
                        "default": "",
                        "description": "Output filename (without extension). Auto-generated if empty.",
                    },
                    "color_palette": {
                        "type": "string",
                        "default": "",
                        "description": "Desired color palette, e.g. '#FF5733, #33FF57, #3357FF' or 'warm earth tones'",
                    },
                    "brand_context": {
                        "type": "string",
                        "default": "",
                        "description": "Brand or project context for consistency, e.g. 'Tech startup, modern and clean'",
                    },
                    "negative_prompt": {
                        "type": "string",
                        "default": "",
                        "description": "What to avoid in the image",
                    },
                },
                "required": ["prompt"],
            },
        ),
        Tool(
            name="edit_web_asset",
            description=(
                "Edit an existing image — modify colors, add/remove elements, "
                "change style, resize conceptually, or transform for web use."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "input_image_path": {
                        "type": "string",
                        "description": "Path to the image file to edit",
                    },
                    "edit_prompt": {
                        "type": "string",
                        "description": "Description of the edit to apply",
                    },
                    "filename": {
                        "type": "string",
                        "default": "",
                        "description": "Output filename (without extension). Auto-generated if empty.",
                    },
                },
                "required": ["input_image_path", "edit_prompt"],
            },
        ),
        Tool(
            name="enhance_prompt",
            description=(
                "Preview the enhanced prompt that would be sent to the AI model "
                "without generating an image. Useful for refining prompts before generation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Your image description",
                    },
                    "asset_type": {
                        "type": "string",
                        "enum": list(ASSET_TEMPLATES.keys()),
                        "default": "custom",
                    },
                    "style": {
                        "type": "string",
                        "enum": list(STYLE_MODIFIERS.keys()),
                        "default": "",
                    },
                    "color_palette": {"type": "string", "default": ""},
                    "brand_context": {"type": "string", "default": ""},
                },
                "required": ["prompt"],
            },
        ),
        Tool(
            name="list_asset_types",
            description="List all available web asset types, styles, and their default configurations.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="batch_generate",
            description=(
                "Generate multiple related web assets in one call. "
                "Useful for creating a consistent set of images for a project."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string"},
                                "asset_type": {"type": "string", "default": "custom"},
                                "style": {"type": "string", "default": ""},
                                "filename": {"type": "string", "default": ""},
                            },
                            "required": ["prompt"],
                        },
                        "description": "List of assets to generate",
                    },
                    "brand_context": {
                        "type": "string",
                        "default": "",
                        "description": "Shared brand context for consistency across all assets",
                    },
                    "color_palette": {
                        "type": "string",
                        "default": "",
                        "description": "Shared color palette for consistency",
                    },
                },
                "required": ["assets"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    try:
        if name == "generate_web_asset":
            return await handle_generate(arguments)
        elif name == "edit_web_asset":
            return await handle_edit(arguments)
        elif name == "enhance_prompt":
            return await handle_enhance_prompt(arguments)
        elif name == "list_asset_types":
            return await handle_list_asset_types()
        elif name == "batch_generate":
            return await handle_batch_generate(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.exception("Tool call failed")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_generate(args: dict) -> list[TextContent | ImageContent]:
    prompt = args["prompt"]
    asset_type = args.get("asset_type", "custom")
    style = args.get("style", "")
    filename = args.get("filename", "")
    color_palette = args.get("color_palette", "")
    brand_context = args.get("brand_context", "")
    negative_prompt = args.get("negative_prompt", "")

    enhanced = build_enhanced_prompt(prompt, asset_type, style, color_palette, brand_context)

    if negative_prompt:
        enhanced += f" Avoid: {negative_prompt}."

    gen = get_provider()
    image_bytes = await gen.generate_image(enhanced)

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{asset_type}_{ts}"

    out_dir = ensure_output_dir(asset_type)
    out_path = out_dir / f"{filename}.png"
    out_path.write_bytes(image_bytes)

    abs_path = str(out_path.resolve())
    b64 = base64.b64encode(image_bytes).decode()

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "success",
                    "path": abs_path,
                    "asset_type": asset_type,
                    "style": style or "default",
                    "enhanced_prompt": enhanced,
                    "size_bytes": len(image_bytes),
                },
                indent=2,
            ),
        ),
        ImageContent(type="image", data=b64, mimeType="image/png"),
    ]


async def handle_edit(args: dict) -> list[TextContent | ImageContent]:
    input_path = args["input_image_path"]
    edit_prompt = args["edit_prompt"]
    filename = args.get("filename", "")

    if not Path(input_path).exists():
        return [TextContent(type="text", text=f"File not found: {input_path}")]

    input_bytes = Path(input_path).read_bytes()
    gen = get_provider()
    image_bytes = await gen.edit_image(input_bytes, edit_prompt)

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"edited_{ts}"

    out_dir = ensure_output_dir("edited")
    out_path = out_dir / f"{filename}.png"
    out_path.write_bytes(image_bytes)

    abs_path = str(out_path.resolve())
    b64 = base64.b64encode(image_bytes).decode()

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "success",
                    "path": abs_path,
                    "edit_prompt": edit_prompt,
                    "size_bytes": len(image_bytes),
                },
                indent=2,
            ),
        ),
        ImageContent(type="image", data=b64, mimeType="image/png"),
    ]


async def handle_enhance_prompt(args: dict) -> list[TextContent]:
    prompt = args["prompt"]
    asset_type = args.get("asset_type", "custom")
    style = args.get("style", "")
    color_palette = args.get("color_palette", "")
    brand_context = args.get("brand_context", "")

    enhanced = build_enhanced_prompt(prompt, asset_type, style, color_palette, brand_context)
    template = ASSET_TEMPLATES.get(asset_type, ASSET_TEMPLATES["custom"])

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "original_prompt": prompt,
                    "enhanced_prompt": enhanced,
                    "asset_type": asset_type,
                    "style": style or "none",
                    "recommended_size": template["default_size"],
                },
                indent=2,
            ),
        )
    ]


async def handle_list_asset_types() -> list[TextContent]:
    info = {
        "asset_types": {
            k: {"default_size": v["default_size"], "description": v["prefix"] or "Custom asset"}
            for k, v in ASSET_TEMPLATES.items()
        },
        "styles": {k: v for k, v in STYLE_MODIFIERS.items()},
    }
    return [TextContent(type="text", text=json.dumps(info, indent=2))]


async def handle_batch_generate(args: dict) -> list[TextContent | ImageContent]:
    assets = args["assets"]
    brand_context = args.get("brand_context", "")
    color_palette = args.get("color_palette", "")
    results: list[TextContent | ImageContent] = []

    for i, asset in enumerate(assets):
        try:
            asset_args = {
                "prompt": asset["prompt"],
                "asset_type": asset.get("asset_type", "custom"),
                "style": asset.get("style", ""),
                "filename": asset.get("filename", ""),
                "brand_context": brand_context,
                "color_palette": color_palette,
            }
            res = await handle_generate(asset_args)
            results.extend(res)
        except Exception as e:
            results.append(
                TextContent(type="text", text=f"Asset {i + 1} failed: {str(e)}")
            )

    summary = TextContent(
        type="text",
        text=f"\nBatch complete: {len(assets)} assets requested.",
    )
    results.append(summary)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    logger.info("Starting AssetPipe MCP Server...")
    logger.info(f"Output directory: {IMAGE_OUTPUT_DIR}")
    logger.info(f"Gemini model: {GEMINI_MODEL}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
