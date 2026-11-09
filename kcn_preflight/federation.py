"""Fail-closed federation authorization with resource-owner scope control."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FederationDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    NOT_MEASURED = "NOT_MEASURED"


@dataclass(frozen=True)
class Delegation:
    principal: str
    resource_owner: str
    resource: str
    operations: frozenset[str]
    scopes: frozenset[str]
    delegation_id: str
    active: bool = True


@dataclass(frozen=True)
class FederationRequest:
    principal: str
    resource_owner: str
    resource: str
    operation: str
    required_scope: str


def authorize(request: FederationRequest,
              delegations: tuple[Delegation, ...] | list[Delegation],
              identity_verified: bool) -> FederationDecision:
    """Identity alone is insufficient; exact owner/resource/operation/scope must match."""
    if not identity_verified:
        return FederationDecision.NOT_MEASURED
    matches = [
        d for d in delegations
        if d.active
        and d.principal == request.principal
        and d.resource_owner == request.resource_owner
        and d.resource == request.resource
        and request.operation in d.operations
        and request.required_scope in d.scopes
    ]
    return FederationDecision.ALLOW if len(matches) == 1 else FederationDecision.DENY


def revoke(delegations: tuple[Delegation, ...] | list[Delegation],
           delegation_id: str) -> tuple[Delegation, ...]:
    """Return a new immutable snapshot with the named grant inactive."""
    return tuple(
        Delegation(d.principal, d.resource_owner, d.resource, d.operations,
                   d.scopes, d.delegation_id, False if d.delegation_id == delegation_id else d.active)
        for d in delegations
    )
