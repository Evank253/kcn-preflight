"""Registered, fail-closed evidence evaluators for the twelve CPG-001 requirements.

These adapters validate evidence-envelope shape, artifact/stage/policy binding,
and trusted-verifier identity. They do not manufacture evidence or infer PASS.
A deployment must provision a reviewed evidence bundle and trusted verifier IDs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

from . import POLICY_VERSION
from .models import Disposition, REQUIREMENTS, RequirementResult, Stage

EvidenceEvaluator = Callable[[Stage, str], RequirementResult]


def _load_bundle() -> dict:
    path = os.environ.get("CPG_EVIDENCE_BUNDLE")
    if not path:
        return {}
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"__invalid__": True}
    return value if isinstance(value, dict) else {"__invalid__": True}


def _make_evaluator(requirement: str) -> EvidenceEvaluator:
    def evaluate(stage: Stage, artifact_digest: str) -> RequirementResult:
        bundle = _load_bundle()
        if bundle.get("__invalid__"):
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Evidence bundle is unreadable or malformed.")
        record = bundle.get("requirements", {}).get(requirement)
        if not isinstance(record, dict):
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "No requirement-specific evidence record was supplied.")
        required = ("artifact_digest", "stage", "policy_version", "verifier_id",
                    "verification_method", "disposition", "evidence_refs")
        if any(key not in record for key in required):
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Evidence record is incomplete.")
        if (record["artifact_digest"] != artifact_digest
                or record["stage"] != stage.value
                or record["policy_version"] != POLICY_VERSION):
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Evidence is not bound to this artifact, stage, and policy.")
        refs = record["evidence_refs"]
        if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and x for x in refs):
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Evidence references are absent or malformed.")
        trusted = {x.strip() for x in os.environ.get("CPG_TRUSTED_VERIFIERS", "").split(",") if x.strip()}
        if record["verifier_id"] not in trusted:
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Evidence verifier is not in the externally configured trust set.",
                                     tuple(refs))
        if not isinstance(record["verification_method"], str) or not record["verification_method"].strip():
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Independent verification method is not specified.", tuple(refs))
        if record["disposition"] == "FAIL":
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Trusted verifier reported a requirement failure.", tuple(refs))
        if record["disposition"] != "PASS":
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Trusted verifier did not provide a PASS disposition.", tuple(refs))
        return RequirementResult(requirement, Disposition.PASS,
                                 "Requirement evidence is bound and attributed to a configured trusted verifier.",
                                 tuple(refs))
    return evaluate


def build_production_evaluators() -> dict[str, EvidenceEvaluator]:
    """Return one explicit evidence adapter for every canonical requirement."""
    return {requirement: _make_evaluator(requirement) for requirement in REQUIREMENTS}


def evaluator_registry_report(evaluators: dict[str, EvidenceEvaluator]) -> dict:
    missing = sorted(set(REQUIREMENTS) - set(evaluators))
    extra = sorted(set(evaluators) - set(REQUIREMENTS))
    return {"registered_count": len(evaluators), "required_count": len(REQUIREMENTS),
            "missing": missing, "extra": extra,
            "registry_complete": not missing and not extra}
