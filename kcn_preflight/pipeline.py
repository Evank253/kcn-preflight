"""Three-stage CPG-001 orchestration with independent Kronos analysis per artifact."""
from __future__ import annotations

from dataclasses import dataclass
from .constitution import ConstitutionalPreflight
from .ledger import EvidenceLedger
from .models import Checkpoint, Stage
from .kronos_adapter import run_kronos_agent_analysis


@dataclass(frozen=True)
class PipelineResult:
    checkpoints: tuple[Checkpoint, ...]
    blocked_at: Stage | None
    swarm_reports: tuple[dict, ...] = ()

    @property
    def ready_for_external_review(self) -> bool:
        return self.blocked_at is None and len(self.checkpoints) == 3


class CPG001Pipeline:
    ORDER = (Stage.VIBE_CODER, Stage.VIBE_DEVELOPER, Stage.HYBRID)

    def __init__(self, preflight: ConstitutionalPreflight,
                 ledger: EvidenceLedger | None = None,
                 enable_kronos: bool = True) -> None:
        self.preflight = preflight
        self.ledger = ledger or EvidenceLedger()
        self.enable_kronos = enable_kronos

    def evaluate(self, artifacts: dict[Stage, bytes]) -> PipelineResult:
        checkpoints: list[Checkpoint] = []
        swarm_reports: list[dict] = []
        for stage in self.ORDER:
            if stage not in artifacts:
                self.ledger.append({"event": "checkpoint_missing_artifact", "stage": stage.value})
                return PipelineResult(tuple(checkpoints), stage, tuple(swarm_reports))

            artifact = artifacts[stage]
            if self.enable_kronos:
                try:
                    report = run_kronos_agent_analysis(
                        artifact, filename=f"{stage.value.lower()}.py"
                    )
                    report_record = {
                        "stage": stage.value,
                        "artifact_digest": report["artifact_digest"],
                        "scanner_role": report["scanner_role"],
                        "agent_roles": list(report["agent_roles"]),
                        "finding_count": len(report["findings"]),
                        "findings": [
                            {
                                "scanner": item.scanner,
                                "finding_id": item.finding_id,
                                "severity": item.severity.value,
                                "summary": item.summary,
                                "artifact_digest": item.artifact_digest,
                                "evidence_refs": list(item.evidence_refs),
                            }
                            for item in report["findings"]
                        ],
                        "agent_results": report["agent_results"],
                        "proposal_only": True,
                        "artifact_modified": False,
                    }
                    swarm_reports.append(report_record)
                    self.ledger.append({"event": "kronos_analysis", "report": report_record})
                except Exception as exc:
                    # Scanner execution failure is evidence failure, never an implicit clean scan.
                    failed_scan = {
                        "stage": stage.value,
                        "disposition": "NOT_MEASURED",
                        "reason": type(exc).__name__,
                    }
                    swarm_reports.append(failed_scan)
                    self.ledger.append({"event": "kronos_analysis_unavailable", "report": failed_scan})

            checkpoint = self.preflight.run_checkpoint(stage, artifact)
            checkpoints.append(checkpoint)
            self.ledger.append({"event": "checkpoint", "record": checkpoint.to_dict()})
            if not self.preflight.may_progress(checkpoint):
                self.ledger.append({
                    "event": "progression_blocked",
                    "stage": stage.value,
                    "disposition": checkpoint.disposition.value,
                    "repair_target": stage.value,
                })
                return PipelineResult(tuple(checkpoints), stage, tuple(swarm_reports))
        return PipelineResult(tuple(checkpoints), None, tuple(swarm_reports))
