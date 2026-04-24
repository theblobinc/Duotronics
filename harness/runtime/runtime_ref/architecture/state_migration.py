from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class StateMigrationPlan:
    plan_id: str = ""
    schema_version: str = "state-migration-plan@v1"
    version: int = 1
    from_generation: int = 0
    to_generation: int = 0
    from_schema_version: str = ""
    to_schema_version: str = ""
    dry_run_replay_spec_hash: str = ""
    defaulting_rules: dict = field(default_factory=dict)
    dropped_fields: list[str] = field(default_factory=list)
    new_fields: list[str] = field(default_factory=list)
    rollback_compatible: bool = True

    def __post_init__(self) -> None:
        if not self.plan_id:
            self.plan_id = f"mig-{uuid.uuid4().hex[:8]}"

    @property
    def plan_hash(self) -> str:
        payload = json.dumps(
            {
                "version": self.version,
                "from_generation": self.from_generation,
                "to_generation": self.to_generation,
                "from_schema_version": self.from_schema_version,
                "to_schema_version": self.to_schema_version,
                "defaulting_rules": self.defaulting_rules,
                "dropped_fields": self.dropped_fields,
                "new_fields": self.new_fields,
                "rollback_compatible": self.rollback_compatible,
            },
            sort_keys=True,
        )
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:16]

    def dry_run(self, state_snapshot: dict, *, transform_fn: Callable[[dict], dict] | None = None) -> dict:
        migrated = dict(state_snapshot)
        defaulted_fields: list[dict] = []
        dropped_fields: list[dict] = []
        errors: list[str] = []

        for field_name in self.new_fields:
            if field_name not in migrated:
                migrated[field_name] = self.defaulting_rules.get(field_name)
                defaulted_fields.append({"field": field_name, "default": migrated[field_name]})

        for field_name in self.dropped_fields:
            if field_name in migrated:
                dropped_fields.append({"field": field_name, "was": migrated.pop(field_name)})

        if transform_fn is not None:
            try:
                migrated = transform_fn(migrated)
            except Exception as exc:
                errors.append(f"transform_failed:{exc}")

        checksum_before = hashlib.sha256(json.dumps(state_snapshot, sort_keys=True, default=str).encode()).hexdigest()[:16]
        checksum_after = hashlib.sha256(json.dumps(migrated, sort_keys=True, default=str).encode()).hexdigest()[:16]
        return {
            "schema_version": "state-migration-dry-run@v1",
            "success": not errors,
            "defaulted_fields": defaulted_fields,
            "dropped_fields": dropped_fields,
            "checksum_before": checksum_before,
            "checksum_after": checksum_after,
            "errors": errors,
            "rollback_compatible": self.rollback_compatible,
            "migrated_state": migrated,
        }

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "schema_version": self.schema_version,
            "version": self.version,
            "plan_hash": self.plan_hash,
            "from_generation": self.from_generation,
            "to_generation": self.to_generation,
            "from_schema_version": self.from_schema_version,
            "to_schema_version": self.to_schema_version,
            "dry_run_replay_spec_hash": self.dry_run_replay_spec_hash,
            "defaulting_rules": dict(self.defaulting_rules),
            "dropped_fields": list(self.dropped_fields),
            "new_fields": list(self.new_fields),
            "rollback_compatible": self.rollback_compatible,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "StateMigrationPlan":
        if not payload:
            return cls()
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})
