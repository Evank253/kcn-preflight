"""Typed records shared by the KCN Preflight assurance kernel."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Disposition(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_MEASURED = "NOT_MEASURED"


class Stage(str, Enum):
    VIBE_CODER = "VIBE_CODER"
    VIBE_DEVELOPER = "VIBE_DEVELOPER"
    HYBRID = "HYBRID"


REQUIREMENTS: tuple[str, ...] = (
    "constitutional_persistence",
    "runtime_enforcement",
    "human_authority_separation",
    "governed_autonomy",
    "non_circumvention",
    "constitutional_cooperation",
    "interoperability",
    "coherence",
    "truth",
    "trust",
    "assurance",
    "evolution_protection",
)


@dataclass(frozen=True)
class RequirementResult:
    requirement: str
    disposition: Disposition
    detail: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["disposition"] = self.disposition.value
        data["evidence_refs"] = list(self.evidence_refs)
        return data


@dataclass(frozen=True)
class Checkpoint:
    stage: Stage
    artifact_digest: str
    policy_version: str
    results: tuple[RequirementResult, ...]
    checkpoint_id: str
    timestamp: str
    repair_target: Stage | None = None

    @property
    def disposition(self) -> Disposition:
        values = {r.disposition for r in self.results}
        if Disposition.FAIL in values:
            return Disposition.FAIL
        if Disposition.NOT_MEASURED in values:
            return Disposition.NOT_MEASURED
        return Disposition.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "artifact_digest": self.artifact_digest,
            "policy_version": self.policy_version,
            "checkpoint_id": self.checkpoint_id,
            "timestamp": self.timestamp,
            "disposition": self.disposition.value,
            "repair_target": self.repair_target.value if self.repair_target else None,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class EvidenceRecord:
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
