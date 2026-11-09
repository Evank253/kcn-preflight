"""Adapters for preserved KCN Governance Substrate bridge and evidence trace."""
from __future__ import annotations

from .vendor.governance_bridge import NormalizationGate
from .vendor.evidence_trace import EvidenceTrace


class SubstrateBridgeAdapter:
    """Reuses the original exact-write and identifier-check capability."""

    def __init__(self) -> None:
        self._gate = NormalizationGate()

    def canonicalize_python(self, source: str) -> str | None:
        return self._gate.canonicalize(source)

    def verify_write(self, intended: bytes, landed: bytes) -> tuple[bool, dict | None]:
        # The original bridge accepts text. UTF-8 decoding is strict; invalid bytes fail.
        try:
            left, right = intended.decode("utf-8"), landed.decode("utf-8")
        except UnicodeDecodeError:
            return False, {"reason": "invalid_utf8"}
        return self._gate.validate_write(left, right)

    def check_identifier(self, actual: str, expected: str) -> bool:
        return self._gate.check_identifier(actual, expected)


class SubstrateEvidenceAdapter:
    """Preserves the original per-gate trace shape and adds hash-stamped events."""

    def __init__(self) -> None:
        self._trace = EvidenceTrace()

    def stamp(self, gate: str, status: str, commit_sha: str,
              before_hash: str, axis_data: dict | None = None) -> dict:
        return self._trace.stamp(gate, status, commit_sha, before_hash, axis_data)

    def divergence(self, expected_green: str, actual_red: str,
                   gate_pair: str) -> dict:
        return self._trace.divergence_log(expected_green, actual_red, gate_pair)

    @property
    def traces(self) -> tuple[dict, ...]:
        return tuple(dict(item) for item in self._trace.traces)
