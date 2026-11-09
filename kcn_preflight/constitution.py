"""Constitutional policy boundary and checkpoint evaluation."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import uuid
from typing import Callable

from . import POLICY_VERSION
from .models import Checkpoint, Disposition, REQUIREMENTS, RequirementResult, Stage

Evaluator = Callable[[Stage, str], RequirementResult]


def artifact_digest(artifact: bytes) -> str:
    return sha256(artifact).hexdigest()


def _not_measured(name: str) -> RequirementResult:
    return RequirementResult(name, Disposition.NOT_MEASURED,
                             "No verified runtime evidence adapter is registered.")


class ConstitutionalPreflight:
    """Runs all 12 requirements at every checkpoint; never infers PASS."""

    def __init__(self, evaluators: dict[str, Evaluator] | None = None,
                 policy_version: str = POLICY_VERSION) -> None:
        self.evaluators = dict(evaluators or {})
        self.policy_version = policy_version

    def run_checkpoint(self, stage: Stage, artifact: bytes) -> Checkpoint:
        digest = artifact_digest(artifact)
        results: list[RequirementResult] = []
        for requirement in REQUIREMENTS:
            evaluator = self.evaluators.get(requirement)
            if evaluator is None:
                result = _not_measured(requirement)
            else:
                try:
                    result = evaluator(stage, digest)
                    if result.requirement != requirement:
                        result = RequirementResult(
                            requirement, Disposition.FAIL,
                            "Evaluator returned a result for a different requirement.")
                except Exception as exc:  # fail closed at the evaluator boundary
                    result = RequirementResult(
                        requirement, Disposition.FAIL,
                        f"Evaluator raised {type(exc).__name__}; checkpoint fails closed.")
            results.append(result)

        return Checkpoint(
            stage=stage,
            artifact_digest=digest,
            policy_version=self.policy_version,
            results=tuple(results),
            checkpoint_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            repair_target=stage if any(r.disposition == Disposition.FAIL for r in results) else None,
        )

    @staticmethod
    def may_progress(checkpoint: Checkpoint) -> bool:
        return checkpoint.disposition == Disposition.PASS
