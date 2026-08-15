from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .evidence import EvidenceKernel, sha256_ref


class FormalObserverFleet:
    def __init__(self, observer_id: str = "formal-observer-fleet") -> None:
        self.kernel = EvidenceKernel(observer_id=observer_id)

    def status(self) -> dict[str, Any]:
        return {
            "lean": {"available": shutil.which("lean") is not None, "binary": shutil.which("lean")},
            "lake": {"available": shutil.which("lake") is not None, "binary": shutil.which("lake")},
            "tlc": {"available": shutil.which("tlc") is not None or shutil.which("java") is not None, "tlc_binary": shutil.which("tlc"), "java_binary": shutil.which("java")},
        }

    def lean_check(self, file_path: str, timeout_s: int = 30) -> dict[str, Any]:
        path = Path(file_path)
        payload: dict[str, Any] = {"file_path": str(path), "file_exists": path.exists()}
        if not path.exists():
            witness = self.kernel.witness("LeanProofWitness", payload | {"result": "missing_file"}, force="observe", status="rejected")
            return {"ok": False, "witness": witness}
        payload["file_digest"] = sha256_ref(path.read_text(errors="ignore"))
        lean = shutil.which("lean")
        if not lean:
            witness = self.kernel.witness("LeanProofWitness", payload | {"result": "tool_unavailable"}, force="observe", status="recorded")
            return {"ok": False, "witness": witness, "error": "lean binary unavailable in this container"}
        proc = subprocess.run([lean, str(path)], capture_output=True, text=True, timeout=timeout_s)
        accepted = proc.returncode == 0
        witness = self.kernel.witness("LeanProofWitness", payload | {"result": "accepted" if accepted else "rejected", "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}, force="prove" if accepted else "observe", status="accepted" if accepted else "rejected")
        return {"ok": accepted, "witness": witness}

    def tla_check(self, spec_path: str, config_path: str | None = None, timeout_s: int = 60) -> dict[str, Any]:
        spec = Path(spec_path)
        payload: dict[str, Any] = {"spec_path": str(spec), "spec_exists": spec.exists(), "config_path": config_path}
        if not spec.exists():
            witness = self.kernel.witness("TLAObserverWitness", payload | {"result": "missing_file"}, force="observe", status="rejected")
            return {"ok": False, "witness": witness}
        payload["spec_digest"] = sha256_ref(spec.read_text(errors="ignore"))
        if config_path and Path(config_path).exists():
            payload["config_digest"] = sha256_ref(Path(config_path).read_text(errors="ignore"))
        tlc = shutil.which("tlc")
        if not tlc:
            witness = self.kernel.witness("TLAObserverWitness", payload | {"result": "tool_unavailable"}, force="observe", status="recorded")
            return {"ok": False, "witness": witness, "error": "tlc binary unavailable; run the formal pod/container profile"}
        cmd = [tlc, str(spec)] + (["-config", str(config_path)] if config_path else [])
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        accepted = proc.returncode == 0
        witness = self.kernel.witness("TLAObserverWitness", payload | {"result": "pass" if accepted else "counterexample_or_error", "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-8000:]}, force="verify" if accepted else "observe", status="accepted" if accepted else "rejected")
        return {"ok": accepted, "witness": witness}
