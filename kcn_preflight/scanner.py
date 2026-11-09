"""Scanner and repair adapter contracts; repair is separate from classification."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class FindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


@dataclass(frozen=True)
class ScannerFinding:
    scanner: str
    finding_id: str
    severity: FindingSeverity
    summary: str
    artifact_digest: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepairProposal:
    finding_id: str
    target_stage: str
    proposed_patch_digest: str
    rationale: str


class ScannerAdapter(Protocol):
    name: str
    def scan(self, artifact: bytes) -> tuple[ScannerFinding, ...]: ...


class RepairAdapter(Protocol):
    name: str
    def propose(self, artifact: bytes,
                findings: tuple[ScannerFinding, ...]) -> tuple[RepairProposal, ...]: ...


def validate_findings(findings: tuple[ScannerFinding, ...],
                      expected_artifact_digest: str) -> bool:
    """Reject findings that cannot be tied to the exact artifact under review."""
    return all(
        f.scanner and f.finding_id and f.summary
        and f.artifact_digest == expected_artifact_digest
        for f in findings
    )
