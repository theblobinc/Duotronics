from __future__ import annotations

import re
from pathlib import Path

from .crypto_primitives import shake256_file
from typing import Any


_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SAFE_NAME = re.compile(r"^[A-Za-z0-9._/-]{1,240}$")


class SkillLibrary:
    """Read-only, path-contained agent skill library."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _parse(self, path: Path) -> dict[str, Any]:
        text = path.read_text(encoding="utf-8", errors="replace")
        metadata: dict[str, str] = {}
        match = _FRONTMATTER.match(text)
        if match:
            for line in match.group(1).splitlines():
                key, sep, value = line.partition(":")
                if sep and key.strip():
                    metadata[key.strip()] = value.strip().strip('"\'')
        rel = path.relative_to(self.root).as_posix()
        name = metadata.get("name") or path.parent.name
        description = metadata.get("description") or ""
        return {
            "name": name,
            "description": description,
            "path": rel,
            "namespace": rel.split("/", 1)[0] if "/" in rel else "default",
            "bytes": path.stat().st_size,
            "shake256_512": shake256_file(path),
            "content": text,
        }

    def list(self, namespace: str | None = None) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        if not self.root.exists():
            return {"root": str(self.root), "items": [], "count": 0}
        for path in sorted(self.root.rglob("SKILL.md")):
            item = self._parse(path)
            if namespace and item["namespace"] != namespace:
                continue
            items.append({k: v for k, v in item.items() if k != "content"})
        return {"root": str(self.root), "namespace": namespace, "items": items, "count": len(items)}

    def _resolve(self, name: str) -> Path:
        value = str(name or "").strip().replace("\\", "/").strip("/")
        if not value or not _SAFE_NAME.fullmatch(value) or ".." in value.split("/"):
            raise ValueError("unsafe skill name")
        candidates = [self.root / value]
        if not value.endswith("SKILL.md"):
            candidates.extend([self.root / value / "SKILL.md", self.root / "concretecms" / value / "SKILL.md"])
        for candidate in candidates:
            resolved = candidate.resolve()
            try:
                resolved.relative_to(self.root)
            except ValueError:
                continue
            if resolved.is_file() and resolved.name == "SKILL.md":
                return resolved
        raise FileNotFoundError(f"skill not found: {value}")

    def read(self, name: str) -> dict[str, Any]:
        return self._parse(self._resolve(name))

    def search(self, query: str, limit: int = 8, namespace: str | None = None) -> dict[str, Any]:
        terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_.:/-]{2,}", query or "")][:32]
        if not terms:
            raise ValueError("query is required")
        rows: list[dict[str, Any]] = []
        for listed in self.list(namespace).get("items", []):
            item = self.read(str(listed["path"]))
            haystack = f"{item['name']}\n{item['description']}\n{item['content']}".lower()
            score = sum(haystack.count(term) for term in terms)
            if score <= 0:
                continue
            positions = [haystack.find(term) for term in terms if haystack.find(term) >= 0]
            start = max(0, (min(positions) if positions else 0) - 240)
            snippet = " ".join(item["content"][start : start + 1400].split())
            rows.append({
                "name": item["name"],
                "description": item["description"],
                "path": item["path"],
                "shake256_512": item["shake256_512"],
                "score": score,
                "snippet": snippet,
            })
        rows.sort(key=lambda row: (row["score"], row["name"]), reverse=True)
        limit = max(1, min(int(limit), 20))
        return {"query": query, "namespace": namespace, "items": rows[:limit], "count": min(len(rows), limit)}
