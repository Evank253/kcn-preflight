from kcn_preflight.constitution import ConstitutionalPreflight
from kcn_preflight.ledger import EvidenceLedger
from kcn_preflight.models import Disposition, REQUIREMENTS, RequirementResult, Stage
from kcn_preflight.pipeline import CPG001Pipeline


def test_pipeline_records_kronos_analysis_for_each_independent_stage():
    evaluators = {}
    for requirement in REQUIREMENTS:
        def make_evaluator(name):
            return lambda stage, digest: RequirementResult(
                name, Disposition.PASS, "test evaluator", (digest,)
            )
        evaluators[requirement] = make_evaluator(requirement)

    ledger = EvidenceLedger()
    pipeline = CPG001Pipeline(
        ConstitutionalPreflight(evaluators=evaluators),
        ledger=ledger,
        enable_kronos=True,
    )
    artifacts = {
        Stage.VIBE_CODER: b"def coder():\n    return True\n",
        Stage.VIBE_DEVELOPER: b"def developer():\n    return True\n",
        Stage.HYBRID: b"def hybrid():\n    return True\n",
    }
    result = pipeline.evaluate(artifacts)
    assert result.blocked_at is None
    assert len(result.checkpoints) == 3
    assert len(result.swarm_reports) == 3
    assert len(result.provenance_brackets) == 3
    assert all(report["artifact_modified"] is False for report in result.swarm_reports)
    assert all(len(report["agent_roles"]) == 6 for report in result.swarm_reports)
    for bracket in result.provenance_brackets:
        assert bracket["before"]["phase"] == "BEFORE_CHECKPOINT"
        assert bracket["after"]["phase"] == "AFTER_CHECKPOINT"
        assert bracket["artifact_unchanged"] is True
    assert ledger.verify()
    assert sum(e.payload.get("event") == "investigation_tool_execution"
               for e in ledger.entries) == 3
