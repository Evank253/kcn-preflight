"""Investigation provenance and before/after checkpoint snapshots.

Records tool execution evidence without granting authority or changing artifacts.
All event records are appended to the caller's hash-chained EvidenceLedger.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from .ledger import EvidenceLedger, canonical_json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


@dataclass(frozen=True)
class ArtifactSnapshot:
    snapshot_id: str
    stage: str
    phase: str
    artifact_digest: str
    artifact_size: int
    captured_at: str
    ledger_head: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "stage": self.stage,
            "phase": self.phase,
            "artifact_digest": self.artifact_digest,
            "artifact_size": self.artifact_size,
            "captured_at": self.captured_at,
            "ledger_head": self.ledger_head,
        }


def capture_snapshot(stage: str, phase: str, artifact: bytes,
                     ledger: EvidenceLedger, snapshot_id: str) -> ArtifactSnapshot:
    head = ledger.entries[-1].entry_hash if ledger.entries else "0" * 64
    return ArtifactSnapshot(
        snapshot_id=snapshot_id,
        stage=stage,
        phase=phase,
        artifact_digest=digest_bytes(artifact),
        artifact_size=len(artifact),
        captured_at=utc_now(),
        ledger_head=head,
    )


def record_tool_execution(ledger: EvidenceLedger, *, stage: str, tool: str,
                          input_digest: str, output: Any,
                          disposition: str, detail: str = "") -> dict[str, Any]:
    """Record a reproducible tool invocation summary and digest of its result."""
    output_payload = output
    output_digest = sha256(canonical_json(output_payload)).hexdigest()
    record = {
        "stage": stage,
        "tool": tool,
        "input_digest": input_digest,
        "output_digest": output_digest,
        "disposition": disposition,
        "detail": detail,
        "recorded_at": utc_now(),
    }
    ledger.append({"event": "investigation_tool_execution", "record": record})
    return record


def record_checkpoint_bracket(ledger: EvidenceLedger, before: ArtifactSnapshot,
                              after: ArtifactSnapshot, checkpoint: dict[str, Any],
                              tool_records: tuple[dict[str, Any], ...] = ()) -> dict[str, Any]:
    """Bind pre/post artifact snapshots, checkpoint result, and tool records."""
    bracket = {
        "stage": before.stage,
        "before": before.to_dict(),
        "after": after.to_dict(),
        "artifact_unchanged": before.artifact_digest == after.artifact_digest,
        "checkpoint": checkpoint,
        "tool_records": list(tool_records),
        "recorded_at": utc_now(),
    }
    ledger.append({"event": "checkpoint_provenance_bracket", "record": bracket})
    return bracket
