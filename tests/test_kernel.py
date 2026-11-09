from kcn_preflight.constitution import ConstitutionalPreflight
from kcn_preflight.ledger import EvidenceLedger
from kcn_preflight.models import Disposition, REQUIREMENTS, RequirementResult, Stage
from kcn_preflight.pipeline import CPG001Pipeline


def test_every_checkpoint_evaluates_all_twelve_requirements():
    checkpoint = ConstitutionalPreflight().run_checkpoint(Stage.VIBE_CODER, b"candidate")
    assert len(checkpoint.results) == 12
    assert tuple(item.requirement for item in checkpoint.results) == REQUIREMENTS
    assert checkpoint.disposition is Disposition.NOT_MEASURED


def test_missing_evidence_blocks_progression():
    pipeline = CPG001Pipeline(ConstitutionalPreflight())
    artifacts = {stage: b"same candidate" for stage in Stage}
    result = pipeline.evaluate(artifacts)
    assert result.blocked_at is Stage.VIBE_CODER
    assert len(result.checkpoints) == 1
    assert not result.ready_for_external_review


def test_ledger_snapshots_payload_and_verifies_chain():
    ledger = EvidenceLedger()
    payload = {"nested": {"value": 1}}
    ledger.append(payload)
    payload["nested"]["value"] = 2
    assert ledger.entries[0].payload["nested"]["value"] == 1
    assert ledger.verify()


def test_evaluator_exception_fails_closed():
    def broken(stage, digest):
        raise RuntimeError("failure")
    engine = ConstitutionalPreflight({"truth": broken})
    checkpoint = engine.run_checkpoint(Stage.HYBRID, b"x")
    result = next(r for r in checkpoint.results if r.requirement == "truth")
    assert result.disposition is Disposition.FAIL
    assert checkpoint.disposition is Disposition.FAIL


def test_all_twelve_can_pass_only_with_explicit_evaluators():
    evaluators = {
        name: (lambda stage, digest, n=name: RequirementResult(
            n, Disposition.PASS, "Test-only explicit evaluator.", ("test:evidence",)
        ))
        for name in REQUIREMENTS
    }
    checkpoint = ConstitutionalPreflight(evaluators).run_checkpoint(Stage.HYBRID, b"x")
    assert checkpoint.disposition is Disposition.PASS
