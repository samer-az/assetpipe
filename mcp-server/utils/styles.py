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


def save_style(data: dict, target_dir: Path | None = None) -> Path:
    """Write .assetpipe-style.json to target_dir (defaults to cwd)."""
    directory = Path(target_dir) if target_dir else Path.cwd()
    path = directory / STYLE_FILENAME
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Saved project style to {path}")
    return path


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
