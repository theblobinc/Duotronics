from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources


@dataclass(frozen=True)
class MetaObjectOntology:
    payload: dict

    def version(self) -> str:
        return str(self.payload.get("version", "ontology@v1"))

    def domains(self) -> list[str]:
        return sorted((self.payload.get("domains") or {}).keys())

    def relations(self) -> list[str]:
        return sorted(self.payload.get("relations") or [])

    def aliases(self) -> dict[str, str]:
        return dict(self.payload.get("category_aliases") or {})

    def resolve_category_path(self, category: str) -> str:
        normalized = str(category or "").strip().lower().replace(" ", "_")
        return self.aliases().get(normalized, normalized)


@lru_cache(maxsize=1)
def get_ontology() -> MetaObjectOntology:
    with resources.files("runtime_ref.meta_objects").joinpath("ontology.yml").open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return MetaObjectOntology(payload=payload)
