import pytest

from kcn_preflight.vibe_contract import (
    VibeContractAdapter, VibeStage,
)


def test_vibe_coder_is_blocked_until_developer_publishes():
    flow = VibeContractAdapter()
    with pytest.raises(PermissionError):
        flow.coder_acknowledge(("module-a",))


def test_vibe_contract_preserves_dependency_pins_and_orders_stages():
    flow = VibeContractAdapter()
    published = flow.developer_publish({"fastapi": "0.115.0"}, env="test-venv")
    assert published.stage == VibeStage.DEVELOPER_DONE
    assert published.coder_allowed
    coded = flow.coder_acknowledge(("module-a",))
    assert coded.stage == VibeStage.CODER_DONE
    assert coded.pins == published.pins
    ready = flow.smoke_result(True, "smoke passed")
    assert ready.stage == VibeStage.DEPLOY_READY
    assert ready.deploy_ready


def test_smoke_cannot_clear_coder_blockers():
    flow = VibeContractAdapter()
    flow.developer_publish()
    flow.coder_acknowledge(("module-a",), ("unresolved security finding",))
    result = flow.smoke_result(True, "smoke passed")
    assert result.stage == VibeStage.SMOKE_FAILED
    assert not result.deploy_ready


def test_smoke_cannot_run_before_coder_acknowledgement():
    flow = VibeContractAdapter()
    flow.developer_publish()
    with pytest.raises(PermissionError):
        flow.smoke_result(True)
