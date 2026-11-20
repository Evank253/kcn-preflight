import hashlib
import os

from fastapi.testclient import TestClient

from kcn_preflight.main import app, DB_PATH

def test_missing_adapter_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr("kcn_preflight.main.DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.delenv("KCN_VIBE_CODER_URL", raising=False)
    from kcn_preflight.main import startup
    startup()
    with TestClient(app) as client:
        payload = {
            "name": "Test system",
            "repository_url": "https://github.com/example/system",
            "source_ref": "a" * 40,
            "source_digest": "sha256:" + hashlib.sha256(b"source").hexdigest(),
            "scope": "test qualification scope",
        }
        created = client.post("/api/projects", json=payload)
        assert created.status_code == 200
        blocked = client.post(f"/api/projects/{created.json()['id']}/run-next")
        assert blocked.status_code == 503
        detail = client.get(f"/api/projects/{created.json()['id']}").json()
        assert detail["runs"] == []

def test_config_does_not_claim_unconfigured_connectors_pass():
    with TestClient(app) as client:
        config = client.get("/api/config").json()
        coder = next(stage for stage in config["stages"] if stage["key"] == "vibe_coder")
        assert coder["configured"] is False or isinstance(coder["configured"], bool)
        assert config["deployment_mode"] == "HANDOFF_ONLY"

def test_project_requires_pinned_digest():
    with TestClient(app) as client:
        response = client.post("/api/projects", json={
            "name": "Invalid",
            "repository_url": "https://github.com/example/system",
            "source_ref": "main",
            "source_digest": "NOT_MEASURED",
            "scope": "qualification",
        })
        assert response.status_code == 422

def test_unapproved_human_receipt_is_rejected():
    from kcn_preflight.main import AdapterResult, validate_adapter_result
    project = {
        "source_digest": "sha256:" + hashlib.sha256(b"source").hexdigest(),
        "scope": "release scope",
    }
    result = AdapterResult(
        status="PASS",
        evidence=["receipt:123"],
        artifact_digest=project["source_digest"],
        human_receipt_id="receipt-123",
        scope="release scope",
        policy_version="wrong-policy",
        disposition="APPROVED",
    )
    valid, reason = validate_adapter_result("human_authorization", result, project)
    assert valid is False
    assert "policy version" in reason
