"""Three-stage CPG-001 pipeline with investigation provenance brackets."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .constitution import ConstitutionalPreflight
from .ledger import EvidenceLedger
from .models import Checkpoint, Stage
from .kronos_adapter import run_kronos_agent_analysis
from .provenance import (
    capture_snapshot,
    record_checkpoint_bracket,
    record_tool_execution,
)


@dataclass(frozen=True)
class PipelineResult:
    checkpoints: tuple[Checkpoint, ...]
    blocked_at: Stage | None
    swarm_reports: tuple[dict, ...] = ()
    provenance_brackets: tuple[dict, ...] = ()

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
        brackets: list[dict] = []
        for stage in self.ORDER:
            if stage not in artifacts:
                self.ledger.append({"event": "checkpoint_missing_artifact", "stage": stage.value})
                return PipelineResult(tuple(checkpoints), stage, tuple(swarm_reports), tuple(brackets))

            artifact = artifacts[stage]
            snapshot_id = str(uuid4())
            before = capture_snapshot(
                stage.value, "BEFORE_INVESTIGATION", artifact, self.ledger,
                snapshot_id + ":before",
            )
            self.ledger.append({"event": "artifact_snapshot", "record": before.to_dict()})
            tool_records: list[dict] = []

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
                    tool_record = record_tool_execution(
                        self.ledger, stage=stage.value, tool="KRONOS_SEVEN_ROLE_ANALYSIS",
                        input_digest=before.artifact_digest, output=report_record,
                        disposition="PASS", detail="Analysis completed; proposals only; no artifact writes.",
                    )
                    tool_records.append(tool_record)
                except Exception as exc:
                    failed_scan = {
                        "stage": stage.value,
                        "disposition": "NOT_MEASURED",
                        "reason": type(exc).__name__,
                    }
                    swarm_reports.append(failed_scan)
                    tool_record = record_tool_execution(
                        self.ledger, stage=stage.value, tool="KRONOS_SEVEN_ROLE_ANALYSIS",
                        input_digest=before.artifact_digest, output=failed_scan,
                        disposition="NOT_MEASURED",
                        detail="Scanner execution failed; no clean-scan inference.",
                    )
                    tool_records.append(tool_record)

            after = capture_snapshot(
                stage.value, "AFTER_INVESTIGATION_BEFORE_CHECKPOINT", artifact,
                self.ledger, snapshot_id + ":after",
            )
            self.ledger.append({"event": "artifact_snapshot", "record": after.to_dict()})

            checkpoint = self.preflight.run_checkpoint(stage, artifact)
            checkpoints.append(checkpoint)
            checkpoint_record = checkpoint.to_dict()
            self.ledger.append({"event": "checkpoint", "record": checkpoint_record})
            bracket = record_checkpoint_bracket(
                self.ledger, before, after, checkpoint_record, tuple(tool_records)
            )
            brackets.append(bracket)

            if not self.preflight.may_progress(checkpoint):
                self.ledger.append({
                    "event": "progression_blocked",
                    "stage": stage.value,
                    "disposition": checkpoint.disposition.value,
                    "repair_target": stage.value,
                })
                return PipelineResult(
                    tuple(checkpoints), stage, tuple(swarm_reports), tuple(brackets)
                )
        return PipelineResult(
            tuple(checkpoints), None, tuple(swarm_reports), tuple(brackets)
        )
