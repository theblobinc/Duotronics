from pathlib import Path

import pytest

from app.duotronic_runtime.dev_bundle_mcp import XaviDevBundleTools
from app.duotronic_runtime.skill_library import SkillLibrary


def test_skill_library_list_read_search(tmp_path: Path):
    skill = tmp_path / "concretecms" / "building-blocktypes" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: building-blocktypes\ndescription: Build modern blocks\n---\n# Blocks\nUse controller.php and db.xml.")
    library = SkillLibrary(tmp_path)
    assert library.list("concretecms")["count"] == 1
    assert library.read("concretecms/building-blocktypes")["name"] == "building-blocktypes"
    assert library.search("controller db.xml", namespace="concretecms")["count"] == 1
    with pytest.raises(ValueError):
        library.read("../outside")


def test_concrete_block_scaffold_is_read_only():
    tool = object.__new__(XaviDevBundleTools)
    result = tool.concrete_block_scaffold({
        "handle": "xavi_demo",
        "name": "Xavi Demo",
        "fields": [{"name": "title", "type": "string"}],
    })
    assert result["written"] is False
    assert result["web_component"] == "xavi-demo"
    assert "controller.php" in result["files"]
    assert "db.xml" in result["files"]
    assert "xavi-demo" in result["files"]["view.php"]
