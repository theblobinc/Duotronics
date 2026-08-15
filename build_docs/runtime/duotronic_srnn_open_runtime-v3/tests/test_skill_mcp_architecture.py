from pathlib import Path
import asyncio

import pytest

from app.duotronic_runtime.skill_mcp import (
    call_skill_tool,
    read_skill_resource,
    skill_resources,
    skill_tool_manifest,
)


@pytest.fixture()
def corpus(tmp_path: Path) -> Path:
    skill = tmp_path / "skills" / "concretecms" / "building-blocktypes" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: building-blocktypes\ndescription: Modern Concrete blocks\n---\n# Blocks\nUse db.xml.")
    return tmp_path


def test_manifest_uses_canonical_skill_namespace():
    names = {item["name"] for item in skill_tool_manifest()}
    assert names == {"skills.list", "skills.read", "skills.search"}


def test_resources_are_individual_and_canonical(corpus: Path):
    resources = skill_resources(corpus)
    uris = {item["uri"] for item in resources}
    assert "skills://concretecms" in uris
    assert "skills://concretecms/building-blocktypes/skill.md" in uris


def test_tool_and_resource_progressive_disclosure(corpus: Path):
    async def exercise():
        listed = await call_skill_tool(corpus, "skills.list", {"namespace": "concretecms"})
        assert listed["count"] == 1
        read = await call_skill_tool(corpus, "skills.read", {"name": "concretecms/building-blocktypes"})
        assert "Use db.xml" in read["content"]
        legacy = await call_skill_tool(corpus, "runtime.skills_read", {"name": "concretecms/building-blocktypes"})
        assert legacy["shake256_512"] == read["shake256_512"]
        resource = await read_skill_resource(corpus, "skills://concretecms/building-blocktypes/skill.md")
        assert resource is not None
        assert resource["mimeType"] == "text/markdown"
        assert "Use db.xml" in resource["contents"]
        legacy_resource = await read_skill_resource(corpus, "xavi-runtime://skills/concretecms/building-blocktypes")
        assert legacy_resource is not None
        assert legacy_resource["metadata"]["shake256_512"] == resource["metadata"]["shake256_512"]
    asyncio.run(exercise())
