"""Fixture-pack loader.

Each pack is a YAML document under `fixtures/` of shape:

    pack_id: dpfc-core
    description: ...
    cases:
      - case_id: hex6.evaluate.h1h4
        op: evaluate_family_word
        marker: normative   # optional, defaults to normative
        given: { family_id: hex6, word: [h1, h4] }
        expect:
          equals: { value: 10 }   # OR: contains: {...}, OR: matches: { ... }
          must_emit_audit: []     # optional list of expected audit kinds
          must_not_emit_audit: [absence_zero_collision_accepted]
          raises: AssertionError  # optional

Each pack also has a JSON twin at the same path (`*.json`) used by
`tools/extract_fixtures.py --check` to detect drift.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml

from .schema_versions import normalize_fixture_schema_version


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@dataclass(frozen=True)
class Case:
    pack_id: str
    case_id: str
    op: str
    given: dict[str, Any]
    expect: dict[str, Any]
    marker: str = "normative"
    extra_markers: tuple[str, ...] = ()
    description: str = ""

    @property
    def all_markers(self) -> tuple[str, ...]:
        return (self.marker, *self.extra_markers)


@dataclass
class Pack:
    pack_id: str
    description: str
    cases: list[Case] = field(default_factory=list)
    source: Path | None = None
    schema_version: str | None = None
    target_schema_version: str | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_pack(path: Path) -> Pack:
    data = _load_yaml(path)
    pack_id = data.get("pack_id") or path.stem
    description = data.get("description", "")
    schema_version = data.get("schema_version")
    target_schema_version = data.get("target_schema_version")
    cases = []
    for raw in data.get("cases", []):
        cases.append(
            Case(
                pack_id=pack_id,
                case_id=raw["case_id"],
                op=raw["op"],
                given=dict(raw.get("given", {})),
                expect=dict(raw.get("expect", {})),
                marker=raw.get("marker", "normative"),
                extra_markers=tuple(raw.get("extra_markers", [])),
                description=raw.get("description", ""),
            )
        )
    return Pack(
        pack_id=pack_id,
        description=description,
        cases=cases,
        source=path,
        schema_version=(
            normalize_fixture_schema_version(str(schema_version))
            if schema_version is not None
            else None
        ),
        target_schema_version=(
            normalize_fixture_schema_version(str(target_schema_version))
            if target_schema_version is not None
            else None
        ),
    )


def discover_packs(
    directory: Path | None = None,
    *,
    schema_version: str | None = None,
    target_schema_version: str | None = None,
) -> list[Pack]:
    directory = directory or FIXTURES_DIR
    selected_schema = (
        normalize_fixture_schema_version(schema_version)
        if schema_version is not None
        else None
    )
    selected_target = (
        normalize_fixture_schema_version(target_schema_version)
        if target_schema_version is not None
        else None
    )
    packs = []
    for path in sorted(directory.glob("*.yaml")):
        pack = load_pack(path)
        if selected_schema is not None and pack.schema_version not in (None, selected_schema):
            continue
        if selected_target is not None and pack.target_schema_version not in (None, selected_target):
            continue
        packs.append(pack)
    return packs


def iter_cases(
    directory: Path | None = None,
    *,
    schema_version: str | None = None,
    target_schema_version: str | None = None,
) -> Iterator[Case]:
    for pack in discover_packs(
        directory,
        schema_version=schema_version,
        target_schema_version=target_schema_version,
    ):
        yield from pack.cases


def load_yaml_pack_for_check(path: Path) -> dict[str, Any]:
    return _load_yaml(path)


def load_json_twin(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json_twin(yaml_path: Path) -> Path:
    """Used by `tools/extract_fixtures.py` to (re)derive the JSON twin."""
    data = _load_yaml(yaml_path)
    json_path = yaml_path.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return json_path


def yaml_json_drift(directory: Path | None = None) -> list[str]:
    """Return non-empty list of drift descriptions when YAML and JSON disagree."""
    directory = directory or FIXTURES_DIR
    drift: list[str] = []
    for yaml_path in sorted(directory.glob("*.yaml")):
        json_path = yaml_path.with_suffix(".json")
        if not json_path.exists():
            drift.append(f"missing JSON twin for {yaml_path.name}")
            continue
        if _load_yaml(yaml_path) != load_json_twin(json_path):
            drift.append(f"drift between {yaml_path.name} and {json_path.name}")
    return drift
