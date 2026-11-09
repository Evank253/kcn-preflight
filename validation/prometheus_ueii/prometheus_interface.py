"""Prometheus Universal Engineering & Intelligence Interface.

A conservative, extensible bridge from natural-language requests and supported
technical artifacts into a provenance-preserving intermediate representation.
Python 3.10+; standard library only. No generated operation is executed.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

SCHEMA = "PROMETHEUS-UIR-1"
VERSION = "0.1.0"

LEXICON = {
    "en": {
        "build": ("build", "create", "implement", "develop", "construct", "design"),
        "investigate": ("investigate", "analyze", "diagnose", "inspect", "debug", "trace"),
        "translate": ("translate", "convert", "map", "transform"),
        "explain": ("explain", "describe", "document", "reconstruct", "understand"),
        "verify": ("verify", "validate", "test", "prove", "check"),
        "must": ("must", "shall", "required", "need to"),
        "should": ("should", "prefer", "ideally"),
        "without": ("without", "do not", "don't", "never", "must not"),
        "preserve": ("preserve", "retain", "keep", "unchanged"),
    },
    "es": {
        "build": ("construir", "crear", "implementar", "desarrollar", "diseñar"),
        "investigate": ("investigar", "analizar", "diagnosticar", "inspeccionar", "depurar"),
        "translate": ("traducir", "convertir", "transformar", "mapear"),
        "explain": ("explicar", "describir", "documentar", "reconstruir", "comprender"),
        "verify": ("verificar", "validar", "probar", "comprobar"),
        "must": ("debe", "deberá", "obligatorio", "tiene que"),
        "should": ("debería", "preferiblemente"),
        "without": ("sin", "no debe", "nunca"),
        "preserve": ("preservar", "conservar", "mantener", "sin cambios"),
    },
}
DOMAIN_TERMS = {
    "mathematics": ("equation", "theorem", "matrix", "function", "ecuación", "teorema", "matriz", "función"),
    "software": ("software", "code", "program", "api", "database", "schema", "código", "programa", "base de datos"),
    "science": ("experiment", "hypothesis", "simulation", "model", "experimento", "hipótesis", "simulación", "modelo"),
    "cybersecurity": ("security", "vulnerability", "malware", "threat", "seguridad", "vulnerabilidad", "amenaza"),
    "engineering": ("system", "architecture", "interface", "dependency", "sistema", "arquitectura", "interfaz", "dependencia"),
}
CONSTRAINT_PATTERNS = {
    "MUST": r"\b(must|shall|required|debe|deberá|obligatorio|tiene que)\b",
    "SHOULD": r"\b(should|prefer|ideally|debería|preferiblemente)\b",
    "PROHIBITION": r"\b(without|do not|don't|never|must not|sin|no debe|nunca)\b",
    "PRESERVATION": r"\b(preserve|retain|keep unchanged|preservar|conservar|mantener)\b",
}
ACTION_VERBS = sorted({w for lang in LEXICON.values() for group in lang.values() for w in group}, key=len, reverse=True)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _language(text: str, requested: str = "auto") -> tuple[str, str]:
    if requested in ("en", "es"):
        return requested, "USER_SELECTED"
    low = text.casefold()
    en = sum(low.count(w) for w in (" the ", " and ", " without ", " build ", " must "))
    es = sum(low.count(w) for w in (" el ", " la ", " y ", " sin ", " debe ", " construir "))
    if en == es == 0:
        return "und", "INSUFFICIENT_LANGUAGE_EVIDENCE"
    return ("es", "LEXICAL_HEURISTIC") if es > en else ("en", "LEXICAL_HEURISTIC")


def _intent(text: str, lang: str) -> list[str]:
    low = text.casefold()
    scores = []
    for intent, words in LEXICON.get(lang, {}).items():
        if intent in ("must", "should", "without", "preserve"):
            continue
        score = sum(1 for word in words if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", low))
        if score:
            scores.append((score, intent))
    scores.sort(key=lambda x: (-x[0], x[1]))
    return [name.upper() for _, name in scores] or ["UNCLASSIFIED"]


def _domains(text: str) -> list[str]:
    low = text.casefold()
    return sorted(domain for domain, terms in DOMAIN_TERMS.items() if any(t in low for t in terms))


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _constraints(text: str) -> list[dict[str, str]]:
    found = []
    for line_no, line in enumerate(_lines(text), 1):
        for kind, pattern in CONSTRAINT_PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE):
                found.append({"type": kind, "text": line, "source_line": str(line_no),
                              "status": "EXPLICIT_TEXT_CANDIDATE"})
    return found


def _operations(text: str, lang: str) -> list[dict[str, str]]:
    result = []
    for line_no, line in enumerate(_lines(text), 1):
        low = line.casefold()
        verbs = [v for v in ACTION_VERBS if re.search(r"(?<!\w)" + re.escape(v) + r"(?!\w)", low)]
        if verbs:
            result.append({"source_line": str(line_no), "source_text": line,
                           "recognized_verb": verbs[0], "status": "ACTION_CANDIDATE"})
    return result


def interpret(text: str, *, language: str = "auto", context: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Input text must be a non-empty string")
    lang, lang_basis = _language(text, language)
    lines = _lines(text)
    intents = _intent(text, lang) if lang in LEXICON else ["UNCLASSIFIED"]
    operations = _operations(text, lang)
    constraints = _constraints(text)
    unresolved = []
    for i, line in enumerate(lines, 1):
        if not any(op["source_text"] == line for op in operations) and not any(c["text"] == line for c in constraints):
            unresolved.append({"source_line": i, "text": line, "status": "UNRESOLVED",
                               "reason": "NO_SUPPORTED_OPERATION_OR_CONSTRAINT_PATTERN"})
    payload = {
        "schema": SCHEMA, "version": VERSION,
        "source": {"text": text, "sha256": _sha(text), "language": lang, "language_basis": lang_basis},
        "request": {"intent_candidates": intents, "goal_text": lines[0], "context": context or {}},
        "domains": _domains(text), "operations": operations, "constraints": constraints,
        "entities": [], "dependencies": [], "assumptions": [], "unresolved": unresolved,
        "evidence": {"interpretation_status": "CANDIDATE_REQUIRES_REVIEW",
                     "human_intent_verified": False, "authority": "NONE"},
    }
    payload["representation_id"] = _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    return payload


def _architecture(ir: dict[str, Any]) -> dict[str, Any]:
    return {"representation": "ENGINEERING_ARCHITECTURE_SPEC", "status": "DRAFT",
            "problem_statement": ir["request"]["goal_text"], "domains": ir["domains"],
            "functional_requirements": ir["operations"], "constraints": ir["constraints"],
            "dependencies": ir["dependencies"], "unresolved": ir["unresolved"],
            "verification_required": True, "execution_authorized": False}


def _pseudocode(ir: dict[str, Any]) -> dict[str, Any]:
    steps = [{"step": i + 1, "action": x["recognized_verb"], "source": x["source_text"],
              "status": "PROPOSED_NOT_EXECUTED"} for i, x in enumerate(ir["operations"])]
    return {"representation": "PSEUDOCODE_PLAN", "steps": steps,
            "constraints": ir["constraints"], "unresolved": ir["unresolved"],
            "execution_authorized": False}


def _python_spec(ir: dict[str, Any]) -> dict[str, Any]:
    return {"representation": "PYTHON_IMPLEMENTATION_SPEC", "status": "SPECIFICATION_ONLY",
            "module_candidates": [], "functions_to_design": [x["recognized_verb"] for x in ir["operations"]],
            "requirements": ir["operations"], "constraints": ir["constraints"],
            "tests_required": True, "source_code_generated": False, "execution_authorized": False}


def _math(ir: dict[str, Any]) -> dict[str, Any]:
    text = ir["source"]["text"]
    exprs = re.findall(r"(?m)(?:^|[:=]\s*)([A-Za-z0-9_().+\-*/^ <>=]+)", text)
    return {"representation": "MATHEMATICAL_EXPRESSION_CANDIDATE",
            "expressions": [e.strip() for e in exprs if any(c in e for c in "=+-*/^")],
            "status": "EXTRACTED_TEXT_ONLY" if exprs else "NOT_MEASURED",
            "warning": "No theorem proving, symbolic simplification, or correctness claim is performed."}


def translate(text: str, *, target: str = "ir", language: str = "auto") -> dict[str, Any]:
    ir = interpret(text, language=language)
    adapters: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
        "ir": lambda x: x, "architecture": _architecture,
        "pseudocode": _pseudocode, "python_spec": _python_spec, "math": _math,
    }
    if target == "json":
        return {"representation": "JSON", "content": ir, "status": "SERIALIZABLE"}
    if target not in adapters:
        return {"representation": target, "status": "NOT_MEASURED",
                "reason": "NO_REGISTERED_ADAPTER", "source_ir": ir}
    return {"representation": target.upper(), "content": adapters[target](ir),
            "source_representation_id": ir["representation_id"]}


def inspect_artifact(content: str, *, artifact_type: str) -> dict[str, Any]:
    digest = _sha(content)
    result: dict[str, Any] = {"schema": SCHEMA, "artifact_type": artifact_type,
                              "source_sha256": digest, "findings": [], "unresolved": [],
                              "status": "INSPECTED_WITH_LIMITS"}
    if artifact_type == "json":
        try:
            obj = json.loads(content)
            result["findings"] = [{"kind": "JSON_VALUE", "python_type": type(obj).__name__}]
            if isinstance(obj, dict):
                result["findings"].append({"kind": "TOP_LEVEL_KEYS", "keys": sorted(map(str, obj.keys()))})
        except json.JSONDecodeError as exc:
            result["status"] = "FAIL"
            result["unresolved"].append({"reason": "INVALID_JSON", "line": exc.lineno, "column": exc.colno})
    elif artifact_type == "python":
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    result["findings"].append({"kind": type(node).__name__.upper(), "name": node.name,
                                               "line": node.lineno})
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    result["findings"].append({"kind": "IMPORT", "line": node.lineno})
        except SyntaxError as exc:
            result["status"] = "FAIL"
            result["unresolved"].append({"reason": "PYTHON_SYNTAX_ERROR", "line": exc.lineno, "message": exc.msg})
    elif artifact_type == "math":
        result["findings"] = [{"kind": "MATHEMATICAL_TEXT", "text": line}
                              for line in _lines(content) if re.search(r"[=+\-*/^∑∫√≤≥]", line)]
        result["unresolved"].append({"reason": "SEMANTIC_AND_MATHEMATICAL_VALIDITY_NOT_CHECKED"})
    elif artifact_type == "architecture":
        result["findings"] = [{"kind": "HEADING_OR_BULLET", "text": line}
                              for line in _lines(content) if line.startswith(("#", "-", "*"))]
        result["unresolved"].append({"reason": "BEHAVIOR_AND_IMPLEMENTATION_NOT_VERIFIED"})
    else:
        result["status"] = "NOT_MEASURED"
        result["unresolved"].append({"reason": "NO_INSPECTOR_FOR_ARTIFACT_TYPE"})
    result["provenance"] = {"source_text_preserved": True, "source_sha256": digest,
                            "interpretation_is_not_authority": True}
    return result


def render_natural_language(ir: dict[str, Any], *, language: str = "en") -> str:
    if language not in ("en", "es"):
        raise ValueError("language must be 'en' or 'es'")
    intent = ", ".join(ir["request"]["intent_candidates"])
    if language == "es":
        return (f"Solicitud interpretada (candidata): {intent}. Objetivo: {ir['request']['goal_text']}\n"
                f"Dominios detectados: {', '.join(ir['domains']) or 'no determinados'}.\n"
                f"Operaciones candidatas: {len(ir['operations'])}; restricciones candidatas: {len(ir['constraints'])}; "
                f"elementos sin resolver: {len(ir['unresolved'])}.\nTexto original conservado; la intención humana no está verificada.")
    return (f"Interpreted request (candidate): {intent}. Goal: {ir['request']['goal_text']}\n"
            f"Detected domains: {', '.join(ir['domains']) or 'undetermined'}.\n"
            f"Candidate operations: {len(ir['operations'])}; candidate constraints: {len(ir['constraints'])}; "
            f"unresolved items: {len(ir['unresolved'])}.\nOriginal text preserved; human intent is not verified.")
