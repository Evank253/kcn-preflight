import hashlib

from kcn_preflight.bridge import BridgeRequest, validate_bridge_request, verify_exact_write
from kcn_preflight.federation import (
    Delegation, FederationDecision, FederationRequest, authorize, revoke,
)
from kcn_preflight.receipts import HumanReceipt, ReceiptStatus, verify_human_receipt
from kcn_preflight.workflow import artifacts_changed, repair_route
from kcn_preflight.models import Stage


def test_bridge_requires_exact_bytes_and_valid_request():
    result = verify_exact_write(b"approved", b"approved ")
    assert not result.accepted
    digest = hashlib.sha256(b"x").hexdigest()
    request = BridgeRequest("coder", "preflight", "write", "repo/file", digest, ("write",))
    assert validate_bridge_request(request)


def test_federation_is_scoped_to_owner_resource_operation_and_scope():
    grant = Delegation("agent-a", "owner-a", "repo-a", frozenset({"read"}),
                       frozenset({"metadata"}), "d-1")
    req = FederationRequest("agent-a", "owner-a", "repo-a", "read", "metadata")
    assert authorize(req, [grant], True) == FederationDecision.ALLOW
    wrong_owner = FederationRequest("agent-a", "owner-b", "repo-a", "read", "metadata")
    assert authorize(wrong_owner, [grant], True) == FederationDecision.DENY
    assert authorize(req, [grant], False) == FederationDecision.NOT_MEASURED
    assert not revoke([grant], "d-1")[0].active


def test_human_receipt_without_external_key_is_not_measured():
    receipt = HumanReceipt("release", "a" * 64, ("production",), "CPG-001",
                           "APPROVE", "human-1", "key-1", "00")
    assert verify_human_receipt(receipt, {}) == ReceiptStatus.NOT_MEASURED


def test_repair_is_stage_local_and_mutation_is_detectable():
    route = repair_route(Stage.VIBE_DEVELOPER, "missing evidence")
    assert route.failed_stage == route.target_stage == Stage.VIBE_DEVELOPER
    assert artifacts_changed(b"old", b"new")
    assert not artifacts_changed(b"same", b"same")
