"""KCN Link Bridge boundary primitives; transport never grants authority."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class BridgeWriteResult:
    accepted: bool
    intended_digest: str
    landed_digest: str
    detail: str


def verify_exact_write(intended: bytes, landed: bytes) -> BridgeWriteResult:
    """Accept only byte-identical output; normalization must happen before this gate."""
    left, right = sha256(intended).hexdigest(), sha256(landed).hexdigest()
    accepted = intended == landed
    return BridgeWriteResult(
        accepted, left, right,
        "Exact bytes verified." if accepted else "Landed bytes differ from intended bytes.",
    )


@dataclass(frozen=True)
class BridgeRequest:
    source_system: str
    target_system: str
    operation: str
    resource: str
    artifact_digest: str
    requested_scope: tuple[str, ...]


def validate_bridge_request(request: BridgeRequest) -> bool:
    """Structural validation only. This function does not authorize the request."""
    return all((
        bool(request.source_system.strip()),
        bool(request.target_system.strip()),
        bool(request.operation.strip()),
        bool(request.resource.strip()),
        len(request.artifact_digest) == 64,
        all(c in "0123456789abcdef" for c in request.artifact_digest),
        bool(request.requested_scope),
    ))
