from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .evidence import CorpusRef, EvidenceKernel, canonical_json, sha256_ref


CORPUS_MANIFEST_NAMES = ("manifest.json", "corpus.manifest.json", "duotronic.manifest.json")


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


class CorpusManager:
    """Version-aware corpus loader for mounted, extracted corpus bundles."""

    def __init__(self, corpus_dir: Path, observer_id: str = "srnn-corpus-manager") -> None:
        self.corpus_dir = corpus_dir
        self.observer_id = observer_id

    def _manifest_path(self) -> Path | None:
        for name in CORPUS_MANIFEST_NAMES:
            p = self.corpus_dir / name
            if p.exists():
                return p
        return None

    def inspect(self) -> dict[str, Any]:
        if not self.corpus_dir.exists():
            return {"status": "missing", "corpus_dir": str(self.corpus_dir), "corpus_ref": CorpusRef().to_dict(), "documents": []}
        manifest_path = self._manifest_path()
        manifest: dict[str, Any] = {}
        if manifest_path:
            try:
                manifest = json.loads(manifest_path.read_text())
            except Exception as exc:
                manifest = {"parse_error": str(exc)}
        files = []
        for path in sorted(self.corpus_dir.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                rel = path.relative_to(self.corpus_dir).as_posix()
                if path.stat().st_size <= 5_000_000:
                    digest = file_digest(path)
                else:
                    digest = "sha256:skipped-large-file"
                files.append({"path": rel, "bytes": path.stat().st_size, "digest": digest})
        digest = sha256_ref({"manifest": manifest, "files": files})
        version = str(manifest.get("version") or manifest.get("corpus_version") or "unversioned")
        ref = CorpusRef(version=version, digest=digest, manifest_ref=file_digest(manifest_path) if manifest_path else "derived:no-manifest")
        return {
            "status": "ok",
            "corpus_dir": str(self.corpus_dir),
            "manifest_path": str(manifest_path) if manifest_path else None,
            "manifest": manifest,
            "corpus_ref": ref.to_dict(),
            "file_count": len(files),
            "documents": files[:500],
            "truncated": len(files) > 500,
        }

    def validate(self) -> dict[str, Any]:
        inspected = self.inspect()
        status = inspected.get("status")
        errors: list[str] = []
        warnings: list[str] = []
        if status != "ok":
            errors.append("corpus directory does not exist")
        manifest = inspected.get("manifest") or {}
        if "parse_error" in manifest:
            errors.append("manifest JSON could not be parsed")
        if not inspected.get("manifest_path"):
            warnings.append("no corpus manifest found; derived corpus ref will be used")
        if inspected.get("file_count", 0) == 0:
            errors.append("corpus contains no files")
        valid = not errors
        kernel = EvidenceKernel(observer_id=self.observer_id, corpus=CorpusRef(**inspected.get("corpus_ref", CorpusRef().to_dict())))
        witness = kernel.witness("CorpusValidationWitness", {"valid": valid, "errors": errors, "warnings": warnings, "corpus": inspected.get("corpus_ref")}, force="observe", status="accepted" if valid else "rejected")
        return {"valid": valid, "errors": errors, "warnings": warnings, "inspection": inspected, "witness": witness}

    def activation_plan(self) -> dict[str, Any]:
        validation = self.validate()
        corpus = validation["inspection"].get("corpus_ref", CorpusRef().to_dict())
        steps = [
            "stage mounted corpus read-only",
            "hash all manifest and schema files",
            "validate manifest and schema registry",
            "dry-run migrations and conformance fixtures",
            "register candidate corpus version",
            "activate only through policy/release witness",
        ]
        return {"corpus": corpus, "valid": validation["valid"], "activation_steps": steps, "validation_witness": validation["witness"]}
