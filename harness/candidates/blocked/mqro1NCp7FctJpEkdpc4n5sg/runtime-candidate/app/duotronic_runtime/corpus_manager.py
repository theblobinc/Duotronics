from __future__ import annotations

import hashlib
import json
import re
import time
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
    """Version-aware corpus loader for mounted, extracted corpus bundles.

    Interactive consumers must not re-hash the complete mounted corpus on every
    request. ``inspect()`` therefore keeps a short-lived immutable inspection
    snapshot and a per-file digest cache keyed by size + mtime_ns. Explicit
    validation still calls ``inspect(force=True)`` and thus performs a fresh
    directory walk while re-hashing only files whose metadata changed.
    """

    _INSPECT_CACHE_TTL_SECONDS = 300.0

    def __init__(self, corpus_dir: Path, observer_id: str = "srnn-corpus-manager", store: Any | None = None) -> None:
        self.corpus_dir = corpus_dir
        self.observer_id = observer_id
        self.store = store
        self._inspect_cache: dict[str, Any] | None = None
        self._inspect_cache_ts: float = 0.0
        # absolute path -> (size, mtime_ns, sha256 digest)
        self._file_digest_cache: dict[str, tuple[int, int, str]] = {}
        self._index_backend = None
        if store is not None:
            try:
                from .corpus_index import build_backend
                self._index_backend = build_backend(store)
            except Exception:
                self._index_backend = None

    def _manifest_path(self) -> Path | None:
        for name in CORPUS_MANIFEST_NAMES:
            p = self.corpus_dir / name
            if p.exists():
                return p
        return None

    def _cached_file_digest(self, path: Path) -> str:
        stat = path.stat()
        key = str(path)
        cached = self._file_digest_cache.get(key)
        fingerprint = (int(stat.st_size), int(stat.st_mtime_ns))
        if cached is not None and cached[:2] == fingerprint:
            return cached[2]
        digest = file_digest(path)
        self._file_digest_cache[key] = (fingerprint[0], fingerprint[1], digest)
        return digest

    def invalidate_cache(self) -> None:
        self._inspect_cache = None
        self._inspect_cache_ts = 0.0

    def inspect(self, *, force: bool = False) -> dict[str, Any]:
        now = time.monotonic()
        if not force and self._index_backend is not None:
            try:
                indexed = self._index_backend.inspect_active(document_limit=500)
                if indexed:
                    return indexed
            except Exception:
                pass
        if (
            not force
            and self._inspect_cache is not None
            and now - self._inspect_cache_ts < self._INSPECT_CACHE_TTL_SECONDS
        ):
            return self._inspect_cache

        if not self.corpus_dir.exists():
            result = {
                "status": "missing",
                "corpus_dir": str(self.corpus_dir),
                "corpus_ref": CorpusRef().to_dict(),
                "documents": [],
            }
            self._inspect_cache = result
            self._inspect_cache_ts = now
            return result

        manifest_path = self._manifest_path()
        manifest: dict[str, Any] = {}
        if manifest_path:
            try:
                manifest = json.loads(manifest_path.read_text())
            except Exception as exc:
                manifest = {"parse_error": str(exc)}

        files: list[dict[str, Any]] = []
        live_paths: set[str] = set()
        for path in sorted(self.corpus_dir.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            rel = path.relative_to(self.corpus_dir).as_posix()
            stat = path.stat()
            live_paths.add(str(path))
            if stat.st_size <= 5_000_000:
                digest = self._cached_file_digest(path)
            else:
                digest = "sha256:skipped-large-file"
            files.append({"path": rel, "bytes": stat.st_size, "digest": digest})

        # Drop digest-cache entries for files that were removed from the corpus.
        if self._file_digest_cache:
            self._file_digest_cache = {
                key: value for key, value in self._file_digest_cache.items() if key in live_paths
            }

        digest = sha256_ref({"manifest": manifest, "files": files})
        version = str(manifest.get("version") or manifest.get("corpus_version") or "unversioned")
        ref = CorpusRef(
            version=version,
            digest=digest,
            manifest_ref=self._cached_file_digest(manifest_path) if manifest_path else "derived:no-manifest",
        )
        result = {
            "status": "ok",
            "corpus_dir": str(self.corpus_dir),
            "manifest_path": str(manifest_path) if manifest_path else None,
            "manifest": manifest,
            "corpus_ref": ref.to_dict(),
            "file_count": len(files),
            "documents": files[:500],
            "truncated": len(files) > 500,
            "inspection_cache_ttl_seconds": self._INSPECT_CACHE_TTL_SECONDS,
        }
        self._inspect_cache = result
        self._inspect_cache_ts = time.monotonic()
        return result

    def search_documents(self, query: str, *, top_k: int = 5, max_bytes: int = 250_000) -> dict[str, Any]:
        """Search the active indexed corpus release, falling back to canonical files."""
        if self._index_backend is not None:
            try:
                indexed = self._index_backend.search(query, top_k=top_k)
                if indexed.get('results'):
                    return indexed
            except Exception:
                pass
        inspected = self.inspect()
        if inspected.get("status") != "ok":
            return {"status": inspected.get("status"), "corpus_ref": inspected.get("corpus_ref"), "results": []}
        terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_./:-]{3,}", query or "")]
        stop = {"the", "and", "for", "with", "that", "this", "from", "user", "assistant", "system"}
        terms = [t for t in terms if t not in stop][:32]
        rows: list[dict[str, Any]] = []
        for item in inspected.get("documents", []):
            rel = str(item.get("path") or "")
            path = self.corpus_dir / rel
            if not path.is_file() or path.stat().st_size > max_bytes:
                continue
            if path.suffix.lower() not in {".md", ".txt", ".json", ".yaml", ".yml", ".lean", ".tla", ".py"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            haystack = f"{rel}\n{text}".lower()
            score = sum(haystack.count(term) for term in terms) if terms else 0
            if score <= 0 and terms:
                continue
            if score <= 0:
                score = 1 if rel else 0
            first_pos = min([haystack.find(term) for term in terms if haystack.find(term) >= 0] or [0])
            start = max(0, first_pos - 400)
            end = min(len(text), first_pos + 1200)
            snippet = " ".join(text[start:end].split())[:1600]
            rows.append({"path": rel, "digest": item.get("digest"), "bytes": item.get("bytes"), "score": score, "snippet": snippet})
        rows.sort(key=lambda r: (r["score"], -len(str(r.get("path") or ""))), reverse=True)
        return {"status": "ok", "corpus_ref": inspected.get("corpus_ref"), "results": rows[: max(1, min(int(top_k), 10))]}

    def validate(self) -> dict[str, Any]:
        # Validation is the explicit expensive integrity boundary; always refresh
        # the directory walk and re-hash files whose size/mtime changed.
        inspected = self.inspect(force=True)
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
