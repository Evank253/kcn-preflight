"""Run English-only Prometheus tests and CPG-001 with all twelve evaluators registered.

Missing evidence remains NOT_MEASURED. It is not converted to PASS, and it is
not itself a test-runner error. CPG qualification remains separate from tests.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL_DIR = Path(__file__).resolve().parent
TEST_DIR = TOOL_DIR / "tests"
ARTIFACT = TOOL_DIR / "prometheus_interface.py"


def main() -> int:
    env = os.environ.copy()
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(TOOL_DIR) + (os.pathsep + prior if prior else "")
    test_run = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(TEST_DIR), "-v"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120, check=False,
    )
    artifact = ARTIFACT.read_bytes()

    sys.path.insert(0, str(ROOT))
    from kcn_preflight.constitution import ConstitutionalPreflight
    from kcn_preflight.evidence_evaluators import build_production_evaluators, evaluator_registry_report
    from kcn_preflight.ledger import EvidenceLedger
    from kcn_preflight.models import Stage
    from kcn_preflight.pipeline import CPG001Pipeline

    ledger = EvidenceLedger()
    test_evidence = {
        "event": "external_validation_test_run",
        "artifact_path": str(ARTIFACT.relative_to(ROOT)),
        "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "command": "python -m unittest discover -s validation/prometheus_ueii/tests -v",
        "exit_code": test_run.returncode,
        "stdout_sha256": hashlib.sha256(test_run.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(test_run.stderr.encode()).hexdigest(),
        "test_output": (test_run.stdout + "\n" + test_run.stderr)[-12000:],
        "execution_scope": "temporary GitHub Actions runner workspace",
    }
    ledger.append(test_evidence)

    evaluators = build_production_evaluators()
    registry_report = evaluator_registry_report(evaluators)
    pipeline = CPG001Pipeline(
        preflight=ConstitutionalPreflight(evaluators=evaluators),
        ledger=ledger,
        enable_kronos=True,
    )
    pipeline_result = pipeline.evaluate({Stage.VIBE_CODER: artifact})
    report = {
        "tool": "PROMETHEUS-UEII-001",
        "tool_version": "0.1.0",
        "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "unit_tests": {
            "exit_code": test_run.returncode,
            "status": "PASS" if test_run.returncode == 0 else "FAIL",
            "stdout": test_run.stdout,
            "stderr": test_run.stderr,
        },
        "cpg001": {
            "pipeline": "CPG-001",
            "branch": "cpg-001-combined",
            "checkpoint_count": len(pipeline_result.checkpoints),
            "blocked_at": pipeline_result.blocked_at.value if pipeline_result.blocked_at else None,
            "checkpoint_dispositions": [item.disposition.value for item in pipeline_result.checkpoints],
            "kronos_reports": len(pipeline_result.swarm_reports),
            "kronos_finding_counts": [item.get("finding_count") for item in pipeline_result.swarm_reports],
            "kronos_findings": [[{"scanner": finding.get("scanner"), "severity": finding.get("severity"), "summary": finding.get("summary"), "evidence_refs": finding.get("evidence_refs", [])} for finding in item.get("findings", [])] for item in pipeline_result.swarm_reports],
            "kronos_roles": [item.get("agent_roles", []) for item in pipeline_result.swarm_reports],
            "provenance_brackets": len(pipeline_result.provenance_brackets),
            "ledger_entries": len(ledger.entries),
            "ledger_integrity": "PASS" if ledger.verify() else "FAIL",
            "evaluator_registry": registry_report,
            "registered_evaluators": len(evaluators),
            "requirements_with_evidence": sum(
                1 for checkpoint in pipeline_result.checkpoints
                for result in checkpoint.results if result.disposition.value == "PASS"
            ),
            "qualification": (
                "NOT_MEASURED" if any(
                    checkpoint.disposition.value == "NOT_MEASURED"
                    for checkpoint in pipeline_result.checkpoints
                ) else (
                    "FAIL" if any(checkpoint.disposition.value == "FAIL"
                                  for checkpoint in pipeline_result.checkpoints)
                    else "PASS_PENDING_HUMAN_REVIEW"
                )
            ),
            "reason": "All twelve evaluator adapters are registered. Missing trusted, artifact-bound evidence remains NOT_MEASURED; no PASS is inferred.",
        },
        "interpretation": "Unit-test results do not qualify the tool or establish production readiness.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    hard_failure = (
        test_run.returncode != 0
        or not ledger.verify()
        or not registry_report["registry_complete"]
        or any(item.disposition.value == "FAIL"
               for checkpoint in pipeline_result.checkpoints for item in checkpoint.results)
    )
    return 1 if hard_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
