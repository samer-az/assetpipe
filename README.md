# 🔧 AssetPipe

**AI image generation pipeline for web design — Claude Code Skill + MCP Server.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)

Generate professional web assets — hero images, icons, logos, backgrounds, banners, and more — directly from Claude Code while you build websites. Powered by Google Gemini.

---

## How It Works

```
You: "Build me a landing page for a fitness app"
                    ↓
    ┌─────────────────────────────┐
    │  Skill (SKILL.md)           │  ← Recognizes images are needed
    │  Picks asset type + style   │     Optimizes the prompt
    │  Applies brand context      │
    └─────────────┬───────────────┘
                  ↓
    ┌─────────────────────────────┐
    │  MCP Server (Python)        │  ← Calls Gemini API
    │  generate / edit / batch    │     Returns image + metadata
    └─────────────┬───────────────┘
                  ↓
    ┌─────────────────────────────┐
    │  Your Project               │  ← Images saved to project
    │  public/images/hero.png     │     Integrated into your code
    └─────────────────────────────┘
```

**Skill** = Teaches Claude *when* and *how* to generate images during web development  
**MCP Server** = The engine that creates them via Google Gemini's API

---

## Features

- **10 asset types** — hero, icon, logo, background, thumbnail, illustration, avatar, banner, product, custom
- **10 visual styles** — photorealistic, flat, 3D, watercolor, minimal, gradient, isometric, line-art, glassmorphism, neon
- **Smart prompt enhancement** — your simple description gets optimized for web design quality
- **Batch generation** — create a consistent set of assets for an entire page
- **Image editing** — modify existing images (change colors, remove elements, restyle)
- **Brand consistency** — share color palette and brand context across all generations
- **Proactive suggestions** — the Skill teaches Claude to suggest images when building sites

---

## Quick Start

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- Python 3.10+
- Google Gemini API key ([free at aistudio.google.com](https://aistudio.google.com/))

### Install

**Option A: Automated**

```bash
git clone https://github.com/YOUR_USERNAME/assetpipe.git
cd assetpipe
./install.sh
```

**Option B: Manual**

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/assetpipe.git
cd assetpipe

# 2. Install Python deps
pip install -r mcp-server/requirements.txt

# 3. Register MCP server with Claude Code (globally)
claude mcp add assetpipe \
  --scope user \
  --env GEMINI_API_KEY=your-key-here \
  --env IMAGE_OUTPUT_DIR=./generated-images \
  -- python3 $(pwd)/mcp-server/server.py

# 4. Install the Skill
mkdir -p ~/.claude/skills/assetpipe
cp skill/SKILL.md ~/.claude/skills/assetpipe/SKILL.md

# 5. Restart Claude Code
```

### Verify

Open Claude Code and ask:

```
What image generation tools do you have?
```

---

## Usage

### Generate a hero image

```
Generate a hero image for my SaaS landing page —
cloud computing theme, blue and purple gradient, modern and clean
```

### Create a full page asset set

```
I need all images for my portfolio site:
- A hero banner with abstract 3D art
- A subtle dot-grid background texture
- Flat icons for the skills section
- A professional avatar placeholder
```

### Edit an existing image

```
Make the hero image darker so white text is readable on top
```

### Match brand colors

```
Generate product images using our brand palette: #2563EB, #1E40AF, #DBEAFE
```

### Batch with consistency

```
Create 4 feature illustrations for a fintech app,
all in flat style with the same teal color palette
```

---

## Asset Types

| Type | Best For | Default Size |
|------|----------|-------------|
| `hero` | Full-width page headers | 1536×768 |
| `icon` | UI element icons | 512×512 |
| `logo` | Brand marks | 1024×1024 |
| `background` | Page/section backgrounds | 1024×1024 |
| `thumbnail` | Blog post or card thumbnails | 640×360 |
| `illustration` | Feature sections, explainers | 1024×768 |
| `avatar` | User profile placeholders | 256×256 |
| `banner` | Social media or promo banners | 1200×628 |
| `product` | E-commerce product shots | 1024×1024 |
| `custom` | Anything else | 1024×1024 |

## Styles

| Style | Vibe |
|-------|------|
| `photorealistic` | Natural lighting, realistic textures |
| `flat` | Solid colors, clean geometric shapes |
| `3d` | Soft lighting, depth and dimension |
| `watercolor` | Soft edges, organic color blending |
| `minimal` | Lots of whitespace, restrained palette |
| `gradient` | Smooth color transitions, contemporary |
| `isometric` | 3D-like flat design, consistent angle |
| `line-art` | Clean outlines, hand-drawn feel |
| `glassmorphism` | Frosted glass, transparency, blur |
| `neon` | Dark background, vibrant glowing elements |

---

## MCP Tools Reference

| Tool | Description |
|------|-------------|
| `generate_web_asset` | Generate any web image asset with smart prompt enhancement |
| `edit_web_asset` | Modify an existing image based on text instructions |
| `batch_generate` | Generate multiple related assets with shared brand context |
| `enhance_prompt` | Preview the optimized prompt without generating |
| `list_asset_types` | Show all available types, styles, and their defaults |

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ | — | Google AI Studio API key |
| `IMAGE_OUTPUT_DIR` | No | `./generated-images` | Output directory for images |
| `GEMINI_MODEL` | No | `gemini-2.0-flash-exp` | Gemini model to use |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

Copy `.env.example` to `.env` and fill in your values.

---

## Project Structure

```
assetpipe/
├── mcp-server/
│   ├── server.py              # MCP server — 5 tools
│   ├── providers/
│   │   ├── __init__.py
│   │   └── gemini.py          # Google Gemini provider
│   ├── utils/
│   │   └── __init__.py
│   └── requirements.txt
├── skill/
│   └── SKILL.md               # Claude Code skill
├── install.sh                 # Automated installer
├── pyproject.toml             # Python package config
├── .env.example               # Environment template
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

## Adding More Providers

The architecture is designed for multiple providers. To add one:

1. Create `mcp-server/providers/your_provider.py`
2. Implement `generate_image(prompt) -> bytes` and `edit_image(image_bytes, prompt) -> bytes`
3. Register it in `server.py`

Potential additions:

| Provider | Package | Notes |
|----------|---------|-------|
| OpenAI (gpt-image-1) | `openai` | High quality, paid |
| Stability AI | `stability-sdk` | Fine-grained control |
| Replicate (Flux) | `replicate` | Many models available |

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `GEMINI_API_KEY not set` | Pass it in the `claude mcp add` command |
| `No image returned` | Prompt may hit safety filters — rephrase it |
| Images not in project | Check `IMAGE_OUTPUT_DIR` is an absolute path |
| MCP server not showing | Restart Claude Code after registration |
| Style inconsistent | Use `batch_generate` with shared `brand_context` |
| Text in image garbled | Don't ask AI to render text — add it via CSS instead |

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
