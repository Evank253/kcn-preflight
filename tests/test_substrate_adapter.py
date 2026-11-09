from kcn_preflight.substrate_adapter import (
    SubstrateBridgeAdapter, SubstrateEvidenceAdapter,
)


def test_substrate_bridge_rejects_divergent_write():
    bridge = SubstrateBridgeAdapter()
    ok, diff = bridge.verify_write(b"exact bytes", b"changed bytes")
    assert not ok
    assert diff and diff["intended_sha"] != diff["landed_sha"]


def test_substrate_bridge_accepts_exact_write_and_checks_identifiers():
    bridge = SubstrateBridgeAdapter()
    ok, diff = bridge.verify_write(b"same", b"same")
    assert ok and diff is None
    assert bridge.check_identifier("artifact_id", "artifact_id")
    assert not bridge.check_identifier("artifact_id", "other")


def test_substrate_bridge_rejects_invalid_utf8():
    bridge = SubstrateBridgeAdapter()
    ok, detail = bridge.verify_write(b"\xff", b"\xff")
    assert not ok and detail == {"reason": "invalid_utf8"}


def test_substrate_evidence_adapter_stamps_and_tracks_divergence():
    trace = SubstrateEvidenceAdapter()
    event = trace.stamp("syntax", "PASS", "commit-1", "a" * 64, {"axis": "test"})
    assert event["trace_hash"]
    assert trace.traces[0]["gate"] == "syntax"
    assert trace.divergence("preflight-pass", "ci-fail", "preflight/ci")["type"] == "divergence"
