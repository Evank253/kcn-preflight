import hashlib
import unittest

from prometheus_interface import (
    SCHEMA, interpret, translate, inspect_artifact, render_natural_language,
)


class PrometheusBilingualTests(unittest.TestCase):
    def test_english_request_preserves_source_and_digest(self):
        text = "Build a service that validates incoming records without changing source files"
        ir = interpret(text, language="en")
        self.assertEqual(ir["schema"], SCHEMA)
        self.assertEqual(ir["source"]["text"], text)
        self.assertEqual(ir["source"]["sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertFalse(ir["evidence"]["human_intent_verified"])
        self.assertEqual(ir["evidence"]["authority"], "NONE")

    def test_spanish_request_preserves_source_and_detects_intent(self):
        text = "Construir un sistema que debe conservar los archivos originales sin cambios"
        ir = interpret(text, language="es")
        self.assertIn("BUILD", ir["request"]["intent_candidates"])
        self.assertEqual(ir["source"]["text"], text)
        self.assertTrue(ir["constraints"])

    def test_auto_language_detection_for_supported_examples(self):
        english = interpret("Build the software system and verify the code")
        spanish = interpret("Construir el sistema y verificar el código")
        self.assertEqual(english["source"]["language"], "en")
        self.assertEqual(spanish["source"]["language"], "es")

    def test_english_operation_is_not_a_constraint_word(self):
        ir = interpret("Build a service without changing source files", language="en")
        self.assertEqual(ir["operations"][0]["recognized_verb"], "build")

    def test_spanish_operation_is_not_a_modal_or_constraint_word(self):
        ir = interpret("Construir un sistema que debe conservar los archivos originales sin cambios",
                       language="es")
        self.assertEqual(ir["operations"][0]["recognized_verb"], "construir")

    def test_architecture_adapter_carries_constraints_and_disables_execution(self):
        result = translate("Build a system that must preserve source files",
                           target="architecture", language="en")
        self.assertFalse(result["content"]["execution_authorized"])
        self.assertTrue(result["content"]["constraints"])
        self.assertTrue(result["content"]["verification_required"])

    def test_python_spec_is_specification_not_generated_code(self):
        result = translate("Create a software service and verify it", target="python_spec")
        self.assertFalse(result["content"]["source_code_generated"])
        self.assertFalse(result["content"]["execution_authorized"])

    def test_unknown_adapter_fails_closed(self):
        result = translate("Do something new", target="quantum_compiler")
        self.assertEqual(result["status"], "NOT_MEASURED")
        self.assertEqual(result["reason"], "NO_REGISTERED_ADAPTER")

    def test_json_inspection_and_invalid_json(self):
        valid = inspect_artifact('{"name":"demo"}', artifact_type="json")
        invalid = inspect_artifact("{bad", artifact_type="json")
        self.assertEqual(valid["status"], "INSPECTED_WITH_LIMITS")
        self.assertEqual(invalid["status"], "FAIL")

    def test_python_inspection_reports_structure_not_behavior(self):
        result = inspect_artifact("import os\ndef run():\n    return 1\n", artifact_type="python")
        self.assertEqual(result["status"], "INSPECTED_WITH_LIMITS")
        self.assertTrue(any(item["kind"] == "FUNCTIONDEF" for item in result["findings"]))
        self.assertNotIn("behavior_verified", result)

    def test_math_inspection_does_not_claim_validity(self):
        result = inspect_artifact("x^2 + y^2 = 1", artifact_type="math")
        self.assertTrue(result["unresolved"])
        self.assertIn("NOT_CHECKED", result["unresolved"][0]["reason"])

    def test_bilingual_summaries(self):
        en = interpret("Analyze the system and verify the architecture", language="en")
        es = interpret("Analizar el sistema y verificar la arquitectura", language="es")
        self.assertIn("Interpreted request", render_natural_language(en, language="en"))
        self.assertIn("Solicitud interpretada", render_natural_language(es, language="es"))

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            interpret("   ")


if __name__ == "__main__":
    unittest.main()
