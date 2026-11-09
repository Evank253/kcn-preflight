"""Three-stage CPG-001 orchestration; each checkpoint is independent."""
from __future__ import annotations

from dataclasses import dataclass
from .constitution import ConstitutionalPreflight
from .ledger import EvidenceLedger
from .models import Checkpoint, Stage


@dataclass(frozen=True)
class PipelineResult:
    checkpoints: tuple[Checkpoint, ...]
    blocked_at: Stage | None

    @property
    def ready_for_external_review(self) -> bool:
        return self.blocked_at is None and len(self.checkpoints) == 3


class CPG001Pipeline:
    ORDER = (Stage.VIBE_CODER, Stage.VIBE_DEVELOPER, Stage.HYBRID)

    def __init__(self, preflight: ConstitutionalPreflight,
                 ledger: EvidenceLedger | None = None) -> None:
        self.preflight = preflight
        self.ledger = ledger or EvidenceLedger()

    def evaluate(self, artifacts: dict[Stage, bytes]) -> PipelineResult:
        checkpoints: list[Checkpoint] = []
        for stage in self.ORDER:
            if stage not in artifacts:
                self.ledger.append({"event": "checkpoint_missing_artifact", "stage": stage.value})
                return PipelineResult(tuple(checkpoints), stage)
            checkpoint = self.preflight.run_checkpoint(stage, artifacts[stage])
            checkpoints.append(checkpoint)
            self.ledger.append({"event": "checkpoint", "record": checkpoint.to_dict()})
            if not self.preflight.may_progress(checkpoint):
                self.ledger.append({
                    "event": "progression_blocked",
                    "stage": stage.value,
                    "disposition": checkpoint.disposition.value,
                    "repair_target": stage.value,
                })
                return PipelineResult(tuple(checkpoints), stage)
        return PipelineResult(tuple(checkpoints), None)
