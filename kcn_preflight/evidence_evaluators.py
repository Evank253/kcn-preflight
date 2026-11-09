"""Registered, fail-closed Ed25519 evidence evaluators for all CPG-001 requirements.

No evaluator invents evidence. PASS requires an artifact/stage/policy-bound
attestation signed by a verifier whose public key is provisioned out of band.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Callable

from . import POLICY_VERSION
from .models import Disposition, REQUIREMENTS, RequirementResult, Stage

EvidenceEvaluator = Callable[[Stage, str], RequirementResult]


def _load_json_env(name: str) -> dict:
    path = os.environ.get(name)
    if not path:
        return {}
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"__invalid__": True}
    return value if isinstance(value, dict) else {"__invalid__": True}


def _make_evaluator(requirement: str) -> EvidenceEvaluator:
    def evaluate(stage: Stage, artifact_digest: str) -> RequirementResult:
        bundle = _load_json_env("CPG_EVIDENCE_BUNDLE")
        if bundle.get("__invalid__"):
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Evidence bundle is unreadable or malformed.")
        record = bundle.get("requirements", {}).get(requirement)
        if not isinstance(record, dict):
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "No requirement-specific evidence attestation was supplied.")
        required = ("artifact_digest", "stage", "policy_version", "verifier_key_id",
                    "verification_method", "disposition", "evidence_refs", "signature")
        if any(key not in record for key in required):
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Evidence attestation is incomplete.")
        refs = record["evidence_refs"]
        if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and x for x in refs):
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Evidence references are absent or malformed.")
        if (record["artifact_digest"] != artifact_digest
                or record["stage"] != stage.value
                or record["policy_version"] != POLICY_VERSION):
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Evidence is not bound to this artifact, stage, and policy.",
                                     tuple(refs))
        if not isinstance(record["verification_method"], str) or not record["verification_method"].strip():
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Independent verification method is not specified.", tuple(refs))
        keys = _load_json_env("CPG_TRUSTED_VERIFIER_KEYS")
        if keys.get("__invalid__"):
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Trusted verifier key store is unreadable or malformed.", tuple(refs))
        key_text = keys.get(record["verifier_key_id"])
        if not isinstance(key_text, str):
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Verifier public key is not provisioned out of band.", tuple(refs))
        signed_body = {key: value for key, value in record.items() if key != "signature"}
        canonical = json.dumps(signed_body, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode("utf-8")
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(key_text))
            signature = base64.b64decode(record["signature"], validate=True)
            public_key.verify(signature, canonical)
        except ImportError:
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Ed25519 verification dependency is unavailable.", tuple(refs))
        except (ValueError, TypeError):
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Evidence signature or public-key encoding is invalid.", tuple(refs))
        except Exception:
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Evidence signature verification failed.", tuple(refs))
        if record["disposition"] == "FAIL":
            return RequirementResult(requirement, Disposition.FAIL,
                                     "Trusted verifier reported a requirement failure.", tuple(refs))
        if record["disposition"] != "PASS":
            return RequirementResult(requirement, Disposition.NOT_MEASURED,
                                     "Trusted verifier did not provide a PASS disposition.", tuple(refs))
        return RequirementResult(requirement, Disposition.PASS,
                                 "Artifact-bound evidence attestation verified with a provisioned Ed25519 key.",
                                 tuple(refs))
    return evaluate


def build_production_evaluators() -> dict[str, EvidenceEvaluator]:
    """Return one cryptographic evidence-verification adapter per canonical requirement."""
    return {requirement: _make_evaluator(requirement) for requirement in REQUIREMENTS}


def evaluator_registry_report(evaluators: dict[str, EvidenceEvaluator]) -> dict:
    missing = sorted(set(REQUIREMENTS) - set(evaluators))
    extra = sorted(set(evaluators) - set(REQUIREMENTS))
    return {"registered_count": len(evaluators), "required_count": len(REQUIREMENTS),
            "missing": missing, "extra": extra,
            "registry_complete": not missing and not extra}
