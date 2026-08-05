# MCP Agent Skill Architecture

The runtime keeps **instructional skills** separate from **executable MCP tools**.

## Layout

```text
corpus/skills/
├── index.json
└── concretecms/
    ├── building-blocktypes/SKILL.md
    ├── building-packages/SKILL.md
    ├── security/SKILL.md
    └── ...
```

Each skill is a directory containing `SKILL.md` and optional `references/` files. Upstream commit and licence metadata are retained in `UPSTREAM.json`.

## Progressive disclosure

1. `skills.list` returns names, descriptions, paths, sizes and SHA-256 digests.
2. `skills.search` returns small matching excerpts.
3. `skills.read` or `resources/read` loads the selected full `SKILL.md`.
4. Operational changes use separate bounded tools such as `dev.concrete_block_scaffold`; skill text never grants write authority.

Canonical resource URIs use:

```text
skills://concretecms
skills://concretecms/building-blocktypes/skill.md
```

The former `runtime.skills_*` tool names and `xavi-runtime://skills/...` resource paths remain accepted as compatibility aliases but are not advertised.
