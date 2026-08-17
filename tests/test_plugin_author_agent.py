from __future__ import annotations

from pathlib import Path

from integrations.ai.check import check_plugin_package
from integrations.ai.filespec import parse_file_blocks
from integrations.ai.scaffold import scaffold_plugin, template_files


def test_parse_file_blocks() -> None:
    text = """
### FILE: packages/demo/plugin.yaml
name: demo

### FILE: packages/demo/demo/plugin.py
print("x")
"""
    files = parse_file_blocks(text)
    assert len(files) == 2
    assert files[0].path == "packages/demo/plugin.yaml"
    assert "name: demo" in files[0].content


def test_template_scaffold_dry_run(tmp_path: Path) -> None:
    result = scaffold_plugin(name="demo_tool", brief="hello", dry_run=True, root=tmp_path)
    assert result.mode == "template"
    assert result.dry_run is True
    assert not result.errors
    assert any(f["path"].endswith("plugin.yaml") for f in result.files)
    assert not (tmp_path / "packages/demo_tool/plugin.yaml").exists()


def test_template_scaffold_write_and_check(tmp_path: Path) -> None:
    result = scaffold_plugin(name="demo_tool", brief="hello", dry_run=False, root=tmp_path)
    assert result.dry_run is False
    assert (tmp_path / "packages/demo_tool/plugin.yaml").is_file()
    assert (tmp_path / "packages/demo_tool/demo_tool/plugin.py").is_file()
    check = check_plugin_package(tmp_path / "packages/demo_tool", root=tmp_path)
    assert check.ok, check.errors


def test_template_files_name() -> None:
    files = template_files("abc")
    assert any("AbcPlugin" in f.content for f in files if f.path.endswith("plugin.py"))
