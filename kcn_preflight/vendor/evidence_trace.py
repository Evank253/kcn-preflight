"""Isolated source copy from Evank253/FINAL-VERSION-MMD_002/kcn-governance-substrate/evidence_trace.py.

Source copy only; original repository and file are untouched.
"""
#!/usr/bin/env python3
"""KCN Governance Substrate — Evidence Trace Module.
Build ID: KCN-GS-BUILD-20261029-201200
Dated: 2026-10-29. Stamps each gate: pass/fail, timestamp,
commit SHA, before-state hash. Three axes: simulation-vs-production,
forward-vs-backward loop count, doctrine-vs-enforcement.
"""
import hashlib
import json
from datetime import datetime, timezone


class EvidenceTrace:
    """Per-gate evidence stamping with three-axis tracking."""

    def __init__(self):
        self.traces = []

    def stamp(self, gate, status, commit_sha, before_hash, axis_data=None):
        entry = {
            "gate": gate,
            "status": status,
            "ts": datetime.now(timezone.utc).isoformat(),
            "commit_sha": commit_sha,
            "before_state_hash": before_hash,
            "axes": axis_data or {},
        }
        blob = json.dumps(entry, sort_keys=True, default=str).encode()
        entry["trace_hash"] = hashlib.sha256(blob).hexdigest()
        self.traces.append(entry)
        return entry

    def divergence_log(self, expected_green, actual_red, gate_pair):
        """Log a pre-flight-green/real-CI-red mismatch for lab study."""
        return {
            "type": "divergence",
            "expected": expected_green,
            "actual": actual_red,
            "gate_pair": gate_pair,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
