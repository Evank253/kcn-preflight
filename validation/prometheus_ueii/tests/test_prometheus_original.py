import json
import unittest

from prometheus_interface import SCHEMA, interpret, translate, inspect_artifact, render_natural_language


class InterfaceTests(unittest.TestCase):
    def test_english_build_request(self):
        ir = interpret("Build a service that validates incoming records without changing source files", language="en")
        self.assertEqual(ir["schema"], SCHEMA)
        self.assertIn("BUILD", ir["request"]["intent_candidates"])
        self.assertTrue(ir["operations"])
        self.assertTrue(ir["constraints"])
        self.assertEqual(ir["evidence"]["human_intent_verified"], False)

    def test_spanish_request_is_recognized(self):
        ir = interpret("Construir un sistema que debe conservar los archivos originales sin cambios", language="es")
        self.assertIn("BUILD", ir["request"]["intent_candidates"])
        self.assertTrue(ir["constraints"])

    def test_architecture_adapter_preserves_constraints(self):
        result = translate("Build a system that must preserve source files", target="architecture", language="en")
        self.assertEqual(result["content"]["execution_authorized"], False)
        self.assertTrue(result["content"]["constraints"])

    def test_unknown_adapter_fails_closed(self):
        result = translate("Do something new", target="quantum_compiler")
        self.assertEqual(result["status"], "NOT_MEASURED")

    def test_python_inspector_parses_structure_not_behavior(self):
        result = inspect_artifact("import os\ndef run():\n    return 1\n", artifact_type="python")
        self.assertEqual(result["status"], "INSPECTED_WITH_LIMITS")
        self.assertTrue(any(x["kind"] == "FUNCTIONDEF" for x in result["findings"]))
        self.assertNotIn("behavior_verified", result)

    def test_invalid_json_fails(self):
        result = inspect_artifact("{bad", artifact_type="json")
        self.assertEqual(result["status"], "FAIL")

    def test_source_digest_and_text_preserved(self):
        text = "Analyze this API and identify dependencies."
        ir = interpret(text)
        self.assertEqual(ir["source"]["text"], text)
        self.assertEqual(len(ir["source"]["sha256"]), 64)

    def test_spanish_summary_is_available(self):
        ir = interpret("Analizar el sistema y verificar la arquitectura", language="es")
        self.assertIn("Solicitud interpretada", render_natural_language(ir, language="es"))


if __name__ == "__main__":
    unittest.main()
