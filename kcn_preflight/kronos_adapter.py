"""Kronos scanner + six-agent analysis orchestration, isolated and non-writing."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import tempfile

from .scanner import FindingSeverity, ScannerFinding
from .vendor.kronos_scanner import SwarmScanner
from .vendor.kronos_agent_pool import build_agent_pool
from .vendor.kronos_executor import SwarmExecutor


_SEVERITY = {
    "CRITICAL": FindingSeverity.BLOCKER,
    "HIGH": FindingSeverity.BLOCKER,
    "MEDIUM": FindingSeverity.WARNING,
    "LOW": FindingSeverity.INFO,
}


def scan_artifact_with_kronos(artifact: bytes, filename: str = "artifact.py") -> tuple[ScannerFinding, ...]:
    """Run only Kronos built-in static checks against a temporary artifact copy."""
    digest = sha256(artifact).hexdigest()
    suffix = Path(filename).suffix or ".txt"
    with tempfile.TemporaryDirectory(prefix="kcn-kronos-") as temp:
        root = Path(temp)
        (root / ("candidate" + suffix)).write_bytes(artifact)
        issues = SwarmScanner(root)._builtin_scan()
    return tuple(
        ScannerFinding(
            scanner=f"kronos:{issue.tool}",
            finding_id=f"{digest[:12]}-{index:04d}",
            severity=_SEVERITY.get(issue.severity, FindingSeverity.WARNING),
            summary=f"{issue.category}: {issue.message}",
            artifact_digest=digest,
            evidence_refs=tuple(
                item for item in (issue.path, str(issue.line) if issue.line else None) if item
            ),
        )
        for index, issue in enumerate(issues)
    )


def run_kronos_agent_analysis(
    artifact: bytes, filename: str = "artifact.py", max_workers: int = 6
) -> dict:
    """Run scanner plus Kronos' six specialist agents; return proposals, never write them.

    The scanner is the seventh swarm role. The original TaskManager's finalize(write_files=True)
    is intentionally not used: Preflight must preserve the submitted artifact until a
    stage-specific repair is separately authorized and revalidated.
    """
    digest = sha256(artifact).hexdigest()
    suffix = Path(filename).suffix or ".txt"
    with tempfile.TemporaryDirectory(prefix="kcn-kronos-swarm-") as temp:
        root = Path(temp)
        candidate_name = "candidate" + suffix
        (root / candidate_name).write_bytes(artifact)
        scanner = SwarmScanner(root)
        issues = scanner._builtin_scan()
        grouped: dict[str, list[dict]] = {}
        for issue in issues:
            row = issue.to_dict()
            row["path"] = candidate_name
            grouped.setdefault(issue.category, []).append(row)

        pool = build_agent_pool()
        jobs = []
        for category, agent in pool.items():
            category_issues = grouped.get(category, [])
            jobs.append((
                agent.name,
                lambda a=agent, rows=category_issues: a.run(root, rows).to_dict(),
            ))
        results = SwarmExecutor(max_workers=max_workers).run(jobs)
        # Copy data out of temp scope. Proposed updated text is retained as preview only.
        safe_results = {}
        for name, result in results.items():
            safe_results[name] = {
                "agent": result.get("agent", name),
                "category": result.get("category"),
                "status": result.get("status"),
                "issue_count": result.get("issue_count", 0),
                "applied_count": result.get("applied_count", 0),
                "diagnostics": list(result.get("diagnostics", [])),
                "proposals": [
                    {
                        "path": item.get("path"),
                        "updated": item.get("updated"),
                        "diff": item.get("diff"),
                        "priority": item.get("priority"),
                        "agent": item.get("agent"),
                    }
                    for item in result.get("changes", [])
                ],
            }
    findings = scan_artifact_with_kronos(artifact, filename)
    return {
        "artifact_digest": digest,
        "scanner_role": "Kronos SwarmScanner",
        "agent_roles": ("LINT", "FORMAT", "TEST", "SECURITY", "TYPE_CHECK", "COMPLEXITY"),
        "findings": findings,
        "agent_results": safe_results,
        "proposal_only": True,
        "artifact_modified": False,
    }
