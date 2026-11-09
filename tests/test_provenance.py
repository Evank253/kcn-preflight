from kcn_preflight.ledger import EvidenceLedger
from kcn_preflight.provenance import (
    capture_snapshot, record_checkpoint_bracket, record_tool_execution,
)


def test_snapshot_records_artifact_digest_and_phase():
    ledger = EvidenceLedger()
    snapshot = capture_snapshot("VIBE_CODER", "BEFORE_CHECKPOINT",
                                b"artifact", ledger, "snapshot-1")
    assert snapshot.artifact_digest
    assert snapshot.artifact_size == len(b"artifact")
    assert snapshot.phase == "BEFORE_CHECKPOINT"


def test_tool_execution_is_recorded_with_input_and_output_digests():
    ledger = EvidenceLedger()
    record = record_tool_execution(
        ledger, stage="VIBE_CODER", tool="KRONOS",
        input_digest="a" * 64, output={"finding_count": 2},
        disposition="PASS", detail="analysis completed",
    )
    assert record["input_digest"] == "a" * 64
    assert record["output_digest"]
    assert ledger.entries[-1].payload["event"] == "investigation_tool_execution"
    assert ledger.verify()


def test_checkpoint_bracket_binds_before_after_and_result():
    ledger = EvidenceLedger()
    before = capture_snapshot("HYBRID", "BEFORE_CHECKPOINT", b"same", ledger, "before")
    after = capture_snapshot("HYBRID", "AFTER_CHECKPOINT", b"same", ledger, "after")
    bracket = record_checkpoint_bracket(
        ledger, before, after, {"disposition": "NOT_MEASURED"}, ()
    )
    assert bracket["artifact_unchanged"] is True
    assert bracket["before"]["artifact_digest"] == bracket["after"]["artifact_digest"]
    assert bracket["checkpoint"]["disposition"] == "NOT_MEASURED"
    assert ledger.verify()
