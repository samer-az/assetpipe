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
