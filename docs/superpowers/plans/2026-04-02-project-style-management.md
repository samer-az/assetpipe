# Project Style Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-project style management so all image generations within a project share a consistent visual style via `.assetpipe-style.json`.

**Architecture:** A new utility module (`utils/styles.py`) handles file discovery, loading, saving, and merging. Three new MCP tools expose style management. Existing generation tools are modified to auto-load and merge project styles before building prompts.

**Tech Stack:** Python 3.10+, MCP SDK, JSON for style files, pytest for tests

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `mcp-server/utils/styles.py` | Style file discovery, load, save, merge |
| Create | `tests/test_styles.py` | Tests for styles utility |
| Create | `tests/__init__.py` | Test package init |
| Modify | `mcp-server/utils/__init__.py` | Export new style functions |
| Modify | `mcp-server/server.py` | 3 new tools + integrate styles into existing tools |
| Modify | `skill/SKILL.md` | Document style management for AI agents |

---

### Task 1: Style Utility — `find_style_file` and `load_style`

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_styles.py`
- Create: `mcp-server/utils/styles.py`

- [ ] **Step 1: Create test package and write failing tests for `find_style_file`**

Create `tests/__init__.py` (empty file).

Create `tests/test_styles.py`:

```python
import json
from pathlib import Path

import pytest


STYLE_FILENAME = ".assetpipe-style.json"


@pytest.fixture
def sample_style():
    return {
        "name": "Test Project",
        "style": "gradient",
        "color_palette": "#FF0000, #00FF00",
        "brand_context": "Test brand",
        "negative_prompt": "blurry, low quality",
        "style_directives": "Keep it warm and friendly",
    }


@pytest.fixture
def style_in_cwd(tmp_path, sample_style):
    style_file = tmp_path / STYLE_FILENAME
    style_file.write_text(json.dumps(sample_style))
    return tmp_path


@pytest.fixture
def style_in_parent(tmp_path, sample_style):
    style_file = tmp_path / STYLE_FILENAME
    style_file.write_text(json.dumps(sample_style))
    child = tmp_path / "src" / "components"
    child.mkdir(parents=True)
    return child


class TestFindStyleFile:
    def test_finds_in_current_dir(self, style_in_cwd):
        from utils.styles import find_style_file

        result = find_style_file(style_in_cwd)
        assert result is not None
        assert result.name == STYLE_FILENAME
        assert result.parent == style_in_cwd

    def test_finds_in_parent_dir(self, style_in_parent, tmp_path):
        from utils.styles import find_style_file

        result = find_style_file(style_in_parent)
        assert result is not None
        assert result.parent == tmp_path

    def test_returns_none_when_not_found(self, tmp_path):
        from utils.styles import find_style_file

        result = find_style_file(tmp_path)
        assert result is None


class TestLoadStyle:
    def test_loads_existing_style(self, style_in_cwd, sample_style):
        from utils.styles import load_style

        result = load_style(style_in_cwd)
        assert result == sample_style

    def test_returns_none_when_no_file(self, tmp_path):
        from utils.styles import load_style

        result = load_style(tmp_path)
        assert result is None

    def test_walks_up_to_find_style(self, style_in_parent, sample_style):
        from utils.styles import load_style

        result = load_style(style_in_parent)
        assert result == sample_style
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/samer/WorkingFolder/assetpipe && python -m pytest tests/test_styles.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.styles'`

- [ ] **Step 3: Implement `find_style_file` and `load_style`**

Create `mcp-server/utils/styles.py`:

```python
"""Project style management for AssetPipe."""

import json
import logging
from pathlib import Path

logger = logging.getLogger("assetpipe.styles")

STYLE_FILENAME = ".assetpipe-style.json"


def find_style_file(start_dir: Path | None = None) -> Path | None:
    """Walk up from start_dir looking for .assetpipe-style.json."""
    current = Path(start_dir) if start_dir else Path.cwd()
    current = current.resolve()

    while True:
        candidate = current / STYLE_FILENAME
        if candidate.is_file():
            logger.debug(f"Found style file: {candidate}")
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_style(start_dir: Path | None = None) -> dict | None:
    """Find and load the project style file. Returns dict or None."""
    path = find_style_file(start_dir)
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        logger.info(f"Loaded project style '{data.get('name', '?')}' from {path}")
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to read style file {path}: {e}")
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -m pytest tests/test_styles.py::TestFindStyleFile tests/test_styles.py::TestLoadStyle -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/__init__.py tests/test_styles.py mcp-server/utils/styles.py
git commit -m "feat: add find_style_file and load_style utilities"
```

---

### Task 2: Style Utility — `save_style`

**Files:**
- Modify: `tests/test_styles.py`
- Modify: `mcp-server/utils/styles.py`

- [ ] **Step 1: Write failing tests for `save_style`**

Append to `tests/test_styles.py`:

```python
class TestSaveStyle:
    def test_creates_style_file(self, tmp_path, sample_style):
        from utils.styles import save_style

        result = save_style(sample_style, tmp_path)
        assert result == tmp_path / STYLE_FILENAME
        assert result.exists()
        saved = json.loads(result.read_text())
        assert saved == sample_style

    def test_defaults_to_cwd(self, tmp_path, sample_style, monkeypatch):
        from utils.styles import save_style

        monkeypatch.chdir(tmp_path)
        result = save_style(sample_style)
        assert result == tmp_path / STYLE_FILENAME

    def test_writes_pretty_json(self, tmp_path, sample_style):
        from utils.styles import save_style

        save_style(sample_style, tmp_path)
        content = (tmp_path / STYLE_FILENAME).read_text()
        assert "\n" in content  # Pretty-printed, not single line
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -m pytest tests/test_styles.py::TestSaveStyle -v`
Expected: FAIL — `ImportError: cannot import name 'save_style'`

- [ ] **Step 3: Implement `save_style`**

Add to `mcp-server/utils/styles.py`:

```python
def save_style(data: dict, target_dir: Path | None = None) -> Path:
    """Write .assetpipe-style.json to target_dir (defaults to cwd)."""
    directory = Path(target_dir) if target_dir else Path.cwd()
    path = directory / STYLE_FILENAME
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Saved project style to {path}")
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -m pytest tests/test_styles.py::TestSaveStyle -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_styles.py mcp-server/utils/styles.py
git commit -m "feat: add save_style utility"
```

---

### Task 3: Style Utility — `merge_style_with_args`

**Files:**
- Modify: `tests/test_styles.py`
- Modify: `mcp-server/utils/styles.py`

- [ ] **Step 1: Write failing tests for `merge_style_with_args`**

Append to `tests/test_styles.py`:

```python
class TestMergeStyleWithArgs:
    def test_fills_missing_args_from_style(self, sample_style):
        from utils.styles import merge_style_with_args

        call_args = {"prompt": "a sunset"}
        merged, notes = merge_style_with_args(sample_style, call_args)
        assert merged["style"] == "gradient"
        assert merged["color_palette"] == "#FF0000, #00FF00"
        assert merged["brand_context"] == "Test brand"
        assert merged["negative_prompt"] == "blurry, low quality"
        assert merged["style_directives"] == "Keep it warm and friendly"
        assert merged["prompt"] == "a sunset"
        assert notes == []

    def test_per_call_overrides_style(self, sample_style):
        from utils.styles import merge_style_with_args

        call_args = {"prompt": "a sunset", "style": "neon", "color_palette": "#000000"}
        merged, notes = merge_style_with_args(sample_style, call_args)
        assert merged["style"] == "neon"
        assert merged["color_palette"] == "#000000"
        assert len(notes) == 2

    def test_override_notes_describe_changes(self, sample_style):
        from utils.styles import merge_style_with_args

        call_args = {"prompt": "a sunset", "style": "neon"}
        merged, notes = merge_style_with_args(sample_style, call_args)
        assert len(notes) == 1
        assert "neon" in notes[0]
        assert "gradient" in notes[0]

    def test_empty_string_does_not_override(self, sample_style):
        from utils.styles import merge_style_with_args

        call_args = {"prompt": "a sunset", "style": ""}
        merged, notes = merge_style_with_args(sample_style, call_args)
        assert merged["style"] == "gradient"
        assert notes == []

    def test_style_directives_always_included(self, sample_style):
        from utils.styles import merge_style_with_args

        call_args = {"prompt": "a sunset"}
        merged, notes = merge_style_with_args(sample_style, call_args)
        assert merged["style_directives"] == "Keep it warm and friendly"

    def test_preserves_extra_call_args(self, sample_style):
        from utils.styles import merge_style_with_args

        call_args = {"prompt": "a sunset", "filename": "test", "transparent": True}
        merged, notes = merge_style_with_args(sample_style, call_args)
        assert merged["prompt"] == "a sunset"
        assert merged["filename"] == "test"
        assert merged["transparent"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -m pytest tests/test_styles.py::TestMergeStyleWithArgs -v`
Expected: FAIL — `ImportError: cannot import name 'merge_style_with_args'`

- [ ] **Step 3: Implement `merge_style_with_args`**

Add to `mcp-server/utils/styles.py`:

```python
MERGEABLE_FIELDS = ("style", "color_palette", "brand_context", "negative_prompt")


def merge_style_with_args(style_data: dict, call_args: dict) -> tuple[dict, list[str]]:
    """Merge project style defaults into call arguments.

    Per-call values win. Returns (merged_args, override_notes).
    """
    merged = dict(call_args)
    notes: list[str] = []

    for field in MERGEABLE_FIELDS:
        project_val = style_data.get(field, "")
        call_val = call_args.get(field, "")

        if call_val:
            # Per-call value provided — use it, note if different from project default
            if project_val and call_val != project_val:
                notes.append(
                    f"{field}: '{call_val}' overrides project default '{project_val}'"
                )
        elif project_val:
            # No per-call value — fill from project style
            merged[field] = project_val

    # style_directives is always included (no per-call equivalent)
    directives = style_data.get("style_directives", "")
    if directives:
        merged["style_directives"] = directives

    return merged, notes
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -m pytest tests/test_styles.py::TestMergeStyleWithArgs -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run all style tests together**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -m pytest tests/test_styles.py -v`
Expected: All 15 tests PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_styles.py mcp-server/utils/styles.py
git commit -m "feat: add merge_style_with_args utility"
```

---

### Task 4: Export styles from utils package

**Files:**
- Modify: `mcp-server/utils/__init__.py`

- [ ] **Step 1: Update `__init__.py` to export style functions**

Replace the content of `mcp-server/utils/__init__.py` with:

```python
from .background import remove_background
from .styles import find_style_file, load_style, save_style, merge_style_with_args

__all__ = [
    "remove_background",
    "find_style_file",
    "load_style",
    "save_style",
    "merge_style_with_args",
]
```

- [ ] **Step 2: Verify imports work**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -c "from utils.styles import find_style_file, load_style, save_style, merge_style_with_args; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add mcp-server/utils/__init__.py
git commit -m "feat: export style utilities from utils package"
```

---

### Task 5: Add 3 new MCP tools — `init_project_style`, `update_project_style`, `get_project_style`

**Files:**
- Modify: `mcp-server/server.py`

- [ ] **Step 1: Add style imports to server.py**

At the top of `server.py`, after `from utils.background import remove_background`, add:

```python
from utils.styles import find_style_file, load_style, save_style, merge_style_with_args
```

- [ ] **Step 2: Add the 3 new tools to `list_tools()`**

Add these 3 entries to the list returned by `list_tools()`, after the `remove_background` tool:

```python
        Tool(
            name="init_project_style",
            description=(
                "Initialize a project style profile (.assetpipe-style.json). "
                "Sets default style, colors, brand context, and directives "
                "that apply to all future image generations in this project."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Project name (for display/logging)",
                    },
                    "style": {
                        "type": "string",
                        "enum": list(STYLE_MODIFIERS.keys()),
                        "default": "",
                        "description": "Default visual style for the project",
                    },
                    "color_palette": {
                        "type": "string",
                        "default": "",
                        "description": "Default color palette, e.g. '#FF5733, #33FF57'",
                    },
                    "brand_context": {
                        "type": "string",
                        "default": "",
                        "description": "Brand or project context for consistency",
                    },
                    "negative_prompt": {
                        "type": "string",
                        "default": "",
                        "description": "Things to always avoid in generated images",
                    },
                    "style_directives": {
                        "type": "string",
                        "default": "",
                        "description": "Free-text style instructions appended to every prompt",
                    },
                    "project_dir": {
                        "type": "string",
                        "default": "",
                        "description": "Directory to create the file in (defaults to cwd)",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="update_project_style",
            description=(
                "Update fields in an existing project style profile. "
                "Only the provided fields are changed — omitted fields stay as-is."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Update project name",
                    },
                    "style": {
                        "type": "string",
                        "enum": list(STYLE_MODIFIERS.keys()),
                        "description": "Update default visual style",
                    },
                    "color_palette": {
                        "type": "string",
                        "description": "Update default color palette",
                    },
                    "brand_context": {
                        "type": "string",
                        "description": "Update brand context",
                    },
                    "negative_prompt": {
                        "type": "string",
                        "description": "Update things to avoid",
                    },
                    "style_directives": {
                        "type": "string",
                        "description": "Update free-text style instructions",
                    },
                    "project_dir": {
                        "type": "string",
                        "default": "",
                        "description": "Directory to search in (defaults to walk-up discovery)",
                    },
                },
            },
        ),
        Tool(
            name="get_project_style",
            description=(
                "Read the current project style profile. Returns the style "
                "configuration and file path, or a message if no style is configured."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "default": "",
                        "description": "Directory to search in (defaults to walk-up discovery)",
                    },
                },
            },
        ),
```

- [ ] **Step 3: Add routing in `call_tool()`**

In the `call_tool()` function, add these 3 branches before the `else` clause:

```python
        elif name == "init_project_style":
            return await handle_init_project_style(arguments)
        elif name == "update_project_style":
            return await handle_update_project_style(arguments)
        elif name == "get_project_style":
            return await handle_get_project_style(arguments)
```

- [ ] **Step 4: Implement the 3 handler functions**

Add these functions in `server.py` after `handle_remove_background`:

```python
async def handle_init_project_style(args: dict) -> list[TextContent]:
    name = args["name"]
    project_dir = args.get("project_dir", "") or None
    target = Path(project_dir) if project_dir else Path.cwd()

    # Check if file already exists in target directory
    existing = target / ".assetpipe-style.json"
    if existing.is_file():
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "error",
                        "message": f"Style file already exists at {existing}. Use update_project_style to modify it.",
                    },
                    indent=2,
                ),
            )
        ]

    style_data = {"name": name}
    for field in ("style", "color_palette", "brand_context", "negative_prompt", "style_directives"):
        val = args.get(field, "")
        if val:
            style_data[field] = val

    path = save_style(style_data, target)

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "success",
                    "message": f"Project style '{name}' created.",
                    "path": str(path.resolve()),
                    "style": style_data,
                },
                indent=2,
            ),
        )
    ]


async def handle_update_project_style(args: dict) -> list[TextContent]:
    project_dir = args.get("project_dir", "") or None
    start = Path(project_dir) if project_dir else None

    style_file = find_style_file(start)
    if style_file is None:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "error",
                        "message": "No .assetpipe-style.json found. Use init_project_style first.",
                    },
                    indent=2,
                ),
            )
        ]

    style_data = json.loads(style_file.read_text(encoding="utf-8"))

    updatable = ("name", "style", "color_palette", "brand_context", "negative_prompt", "style_directives")
    updated_fields = []
    for field in updatable:
        if field in args:
            style_data[field] = args[field]
            updated_fields.append(field)

    if not updated_fields:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "error",
                        "message": "No style fields provided to update.",
                    },
                    indent=2,
                ),
            )
        ]

    save_style(style_data, style_file.parent)

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "success",
                    "message": f"Updated fields: {', '.join(updated_fields)}",
                    "path": str(style_file.resolve()),
                    "style": style_data,
                },
                indent=2,
            ),
        )
    ]


async def handle_get_project_style(args: dict) -> list[TextContent]:
    project_dir = args.get("project_dir", "") or None
    start = Path(project_dir) if project_dir else None

    style_file = find_style_file(start)
    if style_file is None:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "no_style",
                        "message": "No project style configured. Use init_project_style to create one.",
                    },
                    indent=2,
                ),
            )
        ]

    style_data = json.loads(style_file.read_text(encoding="utf-8"))

    return [
        TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "success",
                    "path": str(style_file.resolve()),
                    "style": style_data,
                },
                indent=2,
            ),
        )
    ]
```

- [ ] **Step 5: Verify server starts without errors**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -c "from server import app; print('Server imports OK')"`
Expected: `Server imports OK`

- [ ] **Step 6: Commit**

```bash
git add mcp-server/server.py
git commit -m "feat: add init, update, get project style MCP tools"
```

---

### Task 6: Integrate project style into `build_enhanced_prompt` and `handle_generate`

**Files:**
- Modify: `mcp-server/server.py`

- [ ] **Step 1: Modify `build_enhanced_prompt` to accept `style_directives`**

Update the `build_enhanced_prompt` function signature and body in `server.py`. Add a `style_directives` parameter:

```python
def build_enhanced_prompt(
    user_prompt: str,
    asset_type: str = "custom",
    style: str = "",
    color_palette: str = "",
    brand_context: str = "",
    style_directives: str = "",
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

    if style_directives:
        parts.append(style_directives)

    if template["suffix"]:
        parts.append(template["suffix"])

    return " ".join(parts)
```

- [ ] **Step 2: Modify `handle_generate` to load and merge project style**

Replace the `handle_generate` function:

```python
async def handle_generate(args: dict) -> list[TextContent | ImageContent]:
    # Load project style and merge
    style_data = load_style()
    style_notes = []
    if style_data:
        args, style_notes = merge_style_with_args(style_data, args)

    prompt = args["prompt"]
    asset_type = args.get("asset_type", "custom")
    style = args.get("style", "")
    filename = args.get("filename", "")
    color_palette = args.get("color_palette", "")
    brand_context = args.get("brand_context", "")
    negative_prompt = args.get("negative_prompt", "")
    transparent = args.get("transparent", False)
    style_directives = args.get("style_directives", "")

    enhanced = build_enhanced_prompt(
        prompt, asset_type, style, color_palette, brand_context, style_directives
    )

    if transparent:
        enhanced += " Isolated subject on a plain solid white background, no shadows, no other elements."

    if negative_prompt:
        enhanced += f" Avoid: {negative_prompt}."

    gen = get_provider()
    image_bytes = await gen.generate_image(enhanced)

    if transparent:
        image_bytes = await remove_background(image_bytes)

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{asset_type}_{ts}"

    out_dir = ensure_output_dir(asset_type)
    out_path = out_dir / f"{filename}.png"
    out_path.write_bytes(image_bytes)

    abs_path = str(out_path.resolve())
    b64 = base64.b64encode(image_bytes).decode()

    response_data = {
        "status": "success",
        "path": abs_path,
        "asset_type": asset_type,
        "style": style or "default",
        "transparent": transparent,
        "enhanced_prompt": enhanced,
        "size_bytes": len(image_bytes),
        "project_style": style_data.get("name") if style_data else None,
    }

    if style_notes:
        response_data["style_note"] = "; ".join(style_notes)

    return [
        TextContent(type="text", text=json.dumps(response_data, indent=2)),
        ImageContent(type="image", data=b64, mimeType="image/png"),
    ]
```

- [ ] **Step 3: Commit**

```bash
git add mcp-server/server.py
git commit -m "feat: integrate project style into generate_web_asset"
```

---

### Task 7: Integrate project style into remaining tools

**Files:**
- Modify: `mcp-server/server.py`

- [ ] **Step 1: Update `handle_edit` to use project style**

Replace the `handle_edit` function:

```python
async def handle_edit(args: dict) -> list[TextContent | ImageContent]:
    input_path = args["input_image_path"]
    edit_prompt = args["edit_prompt"]
    filename = args.get("filename", "")
    transparent = args.get("transparent", False)

    if not Path(input_path).exists():
        return [TextContent(type="text", text=f"File not found: {input_path}")]

    # Load project style — only apply style_directives and negative_prompt
    style_data = load_style()
    if style_data:
        directives = style_data.get("style_directives", "")
        if directives:
            edit_prompt = f"{edit_prompt} {directives}"
        neg = style_data.get("negative_prompt", "")
        if neg:
            edit_prompt += f" Avoid: {neg}."

    input_bytes = Path(input_path).read_bytes()
    gen = get_provider()
    image_bytes = await gen.edit_image(input_bytes, edit_prompt)

    if transparent:
        image_bytes = await remove_background(image_bytes)

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
                    "transparent": transparent,
                    "size_bytes": len(image_bytes),
                    "project_style": style_data.get("name") if style_data else None,
                },
                indent=2,
            ),
        ),
        ImageContent(type="image", data=b64, mimeType="image/png"),
    ]
```

- [ ] **Step 2: Update `handle_enhance_prompt` to use project style**

Replace the `handle_enhance_prompt` function:

```python
async def handle_enhance_prompt(args: dict) -> list[TextContent]:
    # Load project style and merge
    style_data = load_style()
    style_notes = []
    if style_data:
        args, style_notes = merge_style_with_args(style_data, args)

    prompt = args["prompt"]
    asset_type = args.get("asset_type", "custom")
    style = args.get("style", "")
    color_palette = args.get("color_palette", "")
    brand_context = args.get("brand_context", "")
    style_directives = args.get("style_directives", "")

    enhanced = build_enhanced_prompt(
        prompt, asset_type, style, color_palette, brand_context, style_directives
    )
    template = ASSET_TEMPLATES.get(asset_type, ASSET_TEMPLATES["custom"])

    response_data = {
        "original_prompt": prompt,
        "enhanced_prompt": enhanced,
        "asset_type": asset_type,
        "style": style or "none",
        "recommended_size": template["default_size"],
        "project_style": style_data.get("name") if style_data else None,
    }

    if style_notes:
        response_data["style_note"] = "; ".join(style_notes)

    return [TextContent(type="text", text=json.dumps(response_data, indent=2))]
```

- [ ] **Step 3: Update `handle_list_asset_types` to include project style**

Replace the `handle_list_asset_types` function:

```python
async def handle_list_asset_types() -> list[TextContent]:
    info = {
        "asset_types": {
            k: {"default_size": v["default_size"], "description": v["prefix"] or "Custom asset"}
            for k, v in ASSET_TEMPLATES.items()
        },
        "styles": {k: v for k, v in STYLE_MODIFIERS.items()},
    }

    style_data = load_style()
    if style_data:
        style_file = find_style_file()
        info["project_style"] = {
            "path": str(style_file.resolve()) if style_file else None,
            **style_data,
        }

    return [TextContent(type="text", text=json.dumps(info, indent=2))]
```

- [ ] **Step 4: Verify server imports still work**

Run: `cd /Users/samer/WorkingFolder/assetpipe && PYTHONPATH=mcp-server python -c "from server import app; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add mcp-server/server.py
git commit -m "feat: integrate project style into edit, enhance_prompt, and list_asset_types"
```

---

### Task 8: Update SKILL.md

**Files:**
- Modify: `skill/SKILL.md`

- [ ] **Step 1: Add new tools to the tool reference table**

In `skill/SKILL.md`, add these rows to the tool table after `batch_generate`:

```markdown
| `init_project_style`  | Create a project style profile for consistent generation |
| `update_project_style` | Update fields in the project style profile              |
| `get_project_style`   | Read the current project style configuration             |
```

- [ ] **Step 2: Add Project Style Management section**

Add this section after the "Brand Consistency" section (before "Troubleshooting"):

```markdown
---

## Project Style Management

AssetPipe supports per-project style profiles that automatically apply to all image generations. Styles are stored in a `.assetpipe-style.json` file in the project root.

### Setting up a project style

On the **first image generation** for a project:

1. Call `get_project_style` to check if a style exists
2. If no style exists, ask the user about their design preferences:
   - What visual style? (flat, gradient, minimal, etc.)
   - What colors? (brand palette or general direction)
   - What's the project about? (brand context)
   - Any style directives? (e.g. "warm and personal", "corporate and clean")
3. Call `init_project_style` with their answers

### How it works

Once a style is configured:
- All `generate_web_asset`, `batch_generate`, `edit_web_asset`, and `enhance_prompt` calls automatically load and apply the project style
- Per-call parameters override project defaults (e.g., passing `style: "neon"` overrides the project's default style)
- When an override is detected, the response includes a `style_note` — mention this to the user so they're aware
- `style_directives` (free-text instructions) are always appended to prompts and cannot be overridden per-call

### Updating styles

Use `update_project_style` to change specific fields without affecting others. Common scenarios:
- User wants to change the color palette mid-project
- User wants to add a negative prompt after seeing unwanted patterns
- User refines the brand context as the project evolves

### Workflow Pattern 7: Setting Up Project Style

```
User: "I'm building a SaaS dashboard for a fintech startup"
You: Check for existing style → none found → ask about preferences

→ Use init_project_style with:
  - name: "Fintech Dashboard"
  - style: "minimal"
  - color_palette: "#1E3A5F, #4DA8DA, #F0F4F8"
  - brand_context: "Fintech SaaS, professional, trustworthy, clean"
  - style_directives: "Modern and data-driven aesthetic, blue tones"

→ All subsequent generate_web_asset calls automatically use these defaults
```
```

- [ ] **Step 3: Commit**

```bash
git add skill/SKILL.md
git commit -m "docs: add project style management to SKILL.md"
```

---

### Task 9: Add pytest configuration

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pytest config to pyproject.toml**

Add this section at the end of `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["mcp-server"]
```

- [ ] **Step 2: Run the full test suite**

Run: `cd /Users/samer/WorkingFolder/assetpipe && python -m pytest tests/ -v`
Expected: All 15 tests PASS

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pytest configuration"
```
