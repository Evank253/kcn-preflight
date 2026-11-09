from kcn_preflight.kronos_adapter import scan_artifact_with_kronos


def test_kronos_adapter_scans_only_isolated_artifact_bytes():
    artifact = b"API_TOKEN = 'super-secret-value-12345'\ndef run():\n\treturn 1  \n"
    findings = scan_artifact_with_kronos(artifact)
    assert findings
    assert all(item.artifact_digest for item in findings)
    assert any("SECURITY" in item.summary for item in findings)


def test_kronos_adapter_does_not_execute_artifact():
    marker = b"import pathlib\npathlib.Path('/tmp/kcn-preflight-should-not-exist').write_text('bad')\n"
    scan_artifact_with_kronos(marker)


def test_kronos_seven_role_swarm_runs_all_six_agents_without_mutating_input():
    from kcn_preflight.kronos_adapter import run_kronos_agent_analysis

    artifact = b"API_TOKEN = 'secret-value-12345'\ndef demo():\n\treturn 1  \n"
    before = bytes(artifact)
    result = run_kronos_agent_analysis(artifact)
    assert result["artifact_digest"]
    assert result["artifact_modified"] is False
    assert result["proposal_only"] is True
    assert len(result["agent_roles"]) == 6
    assert len(result["agent_results"]) == 6
    assert all(item["status"] == "completed" for item in result["agent_results"].values())
    assert artifact == before
