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
