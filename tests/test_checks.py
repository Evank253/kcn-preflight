from pathlib import Path
from kcn_preflight.checks import run_source_checks

def test_source_checker_parses_project_and_runs_secret_scan():
    root = Path(__file__).resolve().parents[1]
    results = run_source_checks(root)
    assert {item.check for item in results} == {"python_syntax", "literal_secret_scan"}
    assert all(item.disposition in {"PASS", "FAIL"} for item in results)

def test_source_checker_rejects_missing_root(tmp_path):
    results = run_source_checks(tmp_path / "missing")
    assert len(results) == 1
    assert results[0].disposition == "FAIL"
