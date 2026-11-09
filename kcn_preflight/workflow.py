"""Stage adapter and repair-routing contracts for CPG-001."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import Stage


class StageAdapter(Protocol):
    stage: Stage
    def build_or_repair(self, artifact: bytes, findings: tuple[object, ...]) -> bytes: ...


@dataclass(frozen=True)
class RepairRoute:
    failed_stage: Stage
    target_stage: Stage
    reason: str


def repair_route(stage: Stage, reason: str) -> RepairRoute:
    """A failed checkpoint routes only to its own stage's adapter."""
    return RepairRoute(stage, stage, reason)


def artifacts_changed(previous: bytes, current: bytes) -> bool:
    """Byte-level mutation invalidates evidence for the prior artifact."""
    return previous != current
