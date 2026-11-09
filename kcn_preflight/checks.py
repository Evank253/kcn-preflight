"""Initial local source checker. This is a baseline, not a full security sandbox."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass(frozen=True)
class Finding:
    check: str
    path: str
    disposition: str
    detail: str

_SECRET_PATTERNS = (
    re.compile(r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)

def check_python_syntax(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            findings.append(Finding("python_syntax", str(path), "FAIL", str(exc)))
    if not findings:
        findings.append(Finding("python_syntax", ".", "PASS", "All discovered Python files parsed."))
    return findings

def scan_literal_secrets(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in _SECRET_PATTERNS):
                findings.append(Finding("literal_secret_scan", f"{path}:{number}", "FAIL",
                                        "Possible hard-coded credential pattern; manual triage required."))
    if not findings:
        findings.append(Finding("literal_secret_scan", ".", "PASS",
                                "No configured literal-secret patterns found; this is not exhaustive."))
    return findings

def run_source_checks(root: Path) -> list[Finding]:
    if not root.exists() or not root.is_dir():
        return [Finding("source_root", str(root), "FAIL", "Source root is not a directory.")]
    return check_python_syntax(root) + scan_literal_secrets(root)
