# Project Style Management — Design Spec

## Overview

Add per-project style management to AssetPipe so that all image generations within a project share a consistent visual style. Styles are stored in a `.assetpipe-style.json` file in the project root and automatically applied to every generation.

## Style File

### Location & Discovery

File name: `.assetpipe-style.json`

Discovery: Walk up from `cwd` to filesystem root looking for the file. First match wins. If not found, the server behaves exactly as today — no style applied.

### Schema

```json
{
  "name": "My Project",
  "style": "gradient",
  "color_palette": "#2563EB, #1E40AF, #DBEAFE",
  "brand_context": "Fitness app, energetic, modern",
  "negative_prompt": "text, watermarks, blurry",
  "style_directives": "All images should feel warm and motivational"
}
```

| Field              | Required | Description                                                        |
|--------------------|----------|--------------------------------------------------------------------|
| `name`             | Yes      | Project identifier for display/logging                             |
| `style`            | No       | Default style modifier (one of the existing 10)                    |
| `color_palette`    | No       | Default color palette string                                       |
| `brand_context`    | No       | Default brand description                                          |
| `negative_prompt`  | No       | Things to always avoid in generated images                         |
| `style_directives` | No       | Free-text instructions appended to every prompt                    |

## Merge Logic

When a generation tool is called:

1. Load project style (if exists)
2. For each field (`style`, `color_palette`, `brand_context`, `negative_prompt`):
   - Per-call value provided and non-empty → use it (override)
   - Per-call value not provided → use project style default
3. `style_directives` is always appended to the prompt (no per-call equivalent)
4. If a per-call value overrides a project default, include a `"style_note"` in the response JSON (informational only, does not block generation)

Example style note: `"style_note": "Using style 'neon' instead of project default 'minimal'"`

## New MCP Tools

### `init_project_style`

Creates a new `.assetpipe-style.json` file.

| Parameter          | Required | Default | Description                              |
|--------------------|----------|---------|------------------------------------------|
| `name`             | Yes      | —       | Project name                             |
| `style`            | No       | —       | Default style modifier                   |
| `color_palette`    | No       | —       | Default colors                           |
| `brand_context`    | No       | —       | Brand description                        |
| `negative_prompt`  | No       | —       | Things to avoid                          |
| `style_directives` | No       | —       | Free-text style instructions             |
| `project_dir`      | No       | cwd     | Directory to create the file in          |

Fails if `.assetpipe-style.json` already exists in the target directory. Returns the created profile + file path.

### `update_project_style`

Updates fields in an existing `.assetpipe-style.json`.

| Parameter          | Required | Default   | Description                              |
|--------------------|----------|-----------|------------------------------------------|
| `name`             | No       | —         | Update project name                      |
| `style`            | No       | —         | Update default style                     |
| `color_palette`    | No       | —         | Update colors                            |
| `brand_context`    | No       | —         | Update brand description                 |
| `negative_prompt`  | No       | —         | Update things to avoid                   |
| `style_directives` | No       | —         | Update free-text instructions            |
| `project_dir`      | No       | discovery | Directory to look in (or walk-up)        |

At least one style field (not counting `project_dir`) must be provided. Only merges provided fields — does not erase omitted fields. Fails if no style file is found. Returns the updated profile.

### `get_project_style`

Reads the current project style.

| Parameter    | Required | Default   | Description                         |
|--------------|----------|-----------|-------------------------------------|
| `project_dir`| No       | discovery | Directory to look in (or walk-up)   |

Returns the style profile + file path, or a "no style configured" message.

## Changes to Existing Tools

### `generate_web_asset`

- Load project style before building the prompt
- Merge project defaults with per-call params
- Append `style_directives` to the enhanced prompt
- Add `"style_note"` to response if overrides detected
- Add `"project_style"` to response showing which style file was used (or `null`)

### `batch_generate`

- Same as `generate_web_asset` — load once, apply to all assets in the batch

### `edit_web_asset`

- Load project style
- Apply only `style_directives` and `negative_prompt` (edit tool doesn't take `style`, `color_palette`, or `brand_context`)

### `enhance_prompt`

- Load and merge project style so the preview reflects the actual prompt that would be sent

### `list_asset_types`

- If a project style exists, include it in the response under a `"project_style"` key

### `remove_background`

- No changes (doesn't use prompts)

## New Utility Module

**File:** `mcp-server/utils/styles.py`

Four functions:

### `find_style_file(start_dir: Path = None) -> Path | None`

Walk up from `start_dir` (defaults to cwd) looking for `.assetpipe-style.json`. Returns the path or `None`.

### `load_style(start_dir: Path = None) -> dict | None`

Calls `find_style_file`, reads and parses JSON. Returns the dict or `None`.

### `save_style(data: dict, target_dir: Path = None) -> Path`

Writes `.assetpipe-style.json` to `target_dir` (defaults to cwd). Returns the file path.

### `merge_style_with_args(style_data: dict, call_args: dict) -> tuple[dict, list[str]]`

Takes project style + per-call arguments. Returns:
- Merged args dict (per-call values win, missing fields filled from project style)
- List of override note strings (e.g. `["style: 'neon' overrides project default 'minimal'"]`)

## Skill Update

Update `skill/SKILL.md` to document the style system:

1. Add `init_project_style`, `update_project_style`, `get_project_style` to the tool reference table
2. Add a "Project Style Management" section with guidance:
   - On first image generation for a project: check for existing style with `get_project_style`. If none, ask user about preferences and call `init_project_style`.
   - On subsequent generations: style is applied automatically. Mention override notes to user if they appear.
3. Add "Pattern 7: Setting Up Project Style" workflow example
