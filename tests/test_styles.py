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

    def test_returns_none_for_malformed_json(self, tmp_path):
        from utils.styles import load_style

        style_file = tmp_path / STYLE_FILENAME
        style_file.write_text("{ not valid json !!!")
        result = load_style(tmp_path)
        assert result is None


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
