from __future__ import annotations

import json
from pathlib import Path

try:
    from .models import AuditEntry
except ImportError:
    from models import AuditEntry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"


def append_audit_entry(entry: AuditEntry) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if AUDIT_PATH.exists():
        existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            raise RuntimeError("output/audit_trail.json must contain a JSON list.")
    else:
        existing = []

    existing.append(entry.model_dump(mode="json"))
    temporary_path = AUDIT_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(AUDIT_PATH)


def recent_audit_entries(limit: int) -> list[dict[str, object]]:
    if not AUDIT_PATH.exists():
        return []
    existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if not isinstance(existing, list):
        raise RuntimeError("output/audit_trail.json must contain a JSON list.")
    return existing[-limit:]