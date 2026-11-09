"""Run the Prometheus suite, then submit its source to the CPG-001 assurance pipeline.

The CPG kernel intentionally has no production evaluators configured here.
A NOT_MEASURED checkpoint is therefore expected and must not be represented as
qualification. Unit-test success and CPG qualification are reported separately.
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

    pipeline = CPG001Pipeline(
        preflight=ConstitutionalPreflight(),
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
            "kronos_roles": [item.get("agent_roles", []) for item in pipeline_result.swarm_reports],
            "provenance_brackets": len(pipeline_result.provenance_brackets),
            "ledger_entries": len(ledger.entries),
            "ledger_integrity": "PASS" if ledger.verify() else "FAIL",
            "qualification": "NOT_MEASURED",
            "reason": "No production evaluators are registered for the twelve constitutional requirements.",
        },
        "interpretation": "Unit-test results do not qualify the tool or establish production readiness.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return test_run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
