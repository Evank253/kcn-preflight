"""Isolated adapter around the original Kronos built-in scanner."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import tempfile

from .models import Disposition
from .scanner import Finding, FindingSeverity, ScannerFinding
from .vendor.kronos_scanner import SwarmScanner


_SEVERITY = {
    "CRITICAL": FindingSeverity.BLOCKER,
    "HIGH": FindingSeverity.BLOCKER,
    "MEDIUM": FindingSeverity.WARNING,
    "LOW": FindingSeverity.INFO,
}


def scan_artifact_with_kronos(artifact: bytes, filename: str = "artifact.py") -> tuple[ScannerFinding, ...]:
    """Run Kronos built-in static checks on an isolated temp copy, never on originals."""
    digest = sha256(artifact).hexdigest()
    suffix = Path(filename).suffix or ".txt"
    with tempfile.TemporaryDirectory(prefix="kcn-kronos-") as temp:
        root = Path(temp)
        candidate = root / ("candidate" + suffix)
        candidate.write_bytes(artifact)
        scanner = SwarmScanner(root)
        # Deliberately avoid scanner.scan(): it invokes pytest and optional external tools.
        issues = scanner._builtin_scan()
    results = []
    for index, issue in enumerate(issues):
        severity = _SEVERITY.get(issue.severity, FindingSeverity.WARNING)
        results.append(ScannerFinding(
            scanner=f"kronos:{issue.tool}",
            finding_id=f"{digest[:12]}-{index:04d}",
            severity=severity,
            summary=f"{issue.category}: {issue.message}",
            artifact_digest=digest,
            evidence_refs=tuple(
                item for item in (issue.path, str(issue.line) if issue.line else None) if item
            ),
        ))
    return tuple(results)
