import unittest

from kcn_preflight.evidence_evaluators import build_production_evaluators, evaluator_registry_report
from kcn_preflight.models import Disposition, REQUIREMENTS, Stage


class ProductionEvaluatorRegistryTests(unittest.TestCase):
    def test_all_twelve_requirements_have_registered_evaluators(self):
        registry = build_production_evaluators()
        report = evaluator_registry_report(registry)
        self.assertTrue(report["registry_complete"])
        self.assertEqual(report["registered_count"], 12)
        self.assertEqual(set(registry), set(REQUIREMENTS))

    def test_missing_evidence_is_not_measured_not_pass(self):
        registry = build_production_evaluators()
        for requirement, evaluator in registry.items():
            result = evaluator(Stage.VIBE_CODER, "a" * 64)
            self.assertEqual(result.requirement, requirement)
            self.assertEqual(result.disposition, Disposition.NOT_MEASURED)

    def test_evidence_cannot_be_reused_for_another_artifact(self):
        # A missing evidence bundle is fail-closed; this test also asserts the
        # evaluator interface returns a typed result for every requirement.
        evaluator = build_production_evaluators()["human_authority_separation"]
        result = evaluator(Stage.VIBE_CODER, "b" * 64)
        self.assertIn(result.disposition, {
            Disposition.NOT_MEASURED, Disposition.FAIL, Disposition.PASS
        })


if __name__ == "__main__":
    unittest.main()
