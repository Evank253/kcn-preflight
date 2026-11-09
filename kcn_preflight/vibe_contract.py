"""Python adapter for the original Vibe Developer ↔ Vibe Coder contract.

Preserves the original ordering (Developer publishes pins before Coder works),
while tightening smoke/deploy readiness so a passing smoke test cannot erase
unresolved coder blockers. This is an in-memory contract; no original Vibe files
or shared state are modified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


DEFAULT_PINS = {
    "fastapi": "0.115.0",
    "starlette": "0.38.6",
    "uvicorn": "0.30.6",
    "pydantic": "2.9.2",
}


class VibeStage(str, Enum):
    WAITING_FOR_DEVELOPER = "waiting_for_developer"
    DEVELOPER_DONE = "developer_done"
    CODER_DONE = "coder_done"
    SMOKE_FAILED = "smoke_failed"
    DEPLOY_READY = "deploy_ready"


@dataclass(frozen=True)
class VibeContract:
    schema: str = "vibe.contract.v1"
    stage: VibeStage = VibeStage.WAITING_FOR_DEVELOPER
    pins: tuple[tuple[str, str], ...] = ()
    env: str = ""
    notes: str = ""
    coder_allowed: bool = False
    implemented: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    smoke_status: str = "pending"
    smoke_detail: str = ""
    deploy_ready: bool = False
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VibeContractAdapter:
    def __init__(self) -> None:
        self._contract = VibeContract()

    @property
    def contract(self) -> VibeContract:
        return self._contract

    def developer_publish(self, pins: Mapping[str, str] | None = None,
                          env: str = "project-venv", notes: str = "") -> VibeContract:
        chosen = dict(DEFAULT_PINS if pins is None else pins)
        if not chosen or any(not k.strip() or not v.strip() for k, v in chosen.items()):
            raise ValueError("Dependency pins must contain non-empty names and versions.")
        self._contract = VibeContract(
            stage=VibeStage.DEVELOPER_DONE,
            pins=tuple(sorted(chosen.items())),
            env=env,
            notes=notes,
            coder_allowed=True,
        )
        return self._contract

    def coder_acknowledge(self, implemented: tuple[str, ...] = (),
                          blockers: tuple[str, ...] = ()) -> VibeContract:
        if not self._contract.coder_allowed:
            raise PermissionError("Coder blocked until Developer publishes dependency pins.")
        self._contract = VibeContract(
            stage=VibeStage.CODER_DONE,
            pins=self._contract.pins,
            env=self._contract.env,
            notes=self._contract.notes,
            coder_allowed=True,
            implemented=tuple(implemented),
            blockers=tuple(blockers),
            deploy_ready=False,
        )
        return self._contract

    def smoke_result(self, ok: bool, detail: str = "") -> VibeContract:
        current = self._contract
        if current.stage != VibeStage.CODER_DONE:
            raise PermissionError("Smoke result requires completed Coder acknowledgement.")
        ready = bool(ok) and not current.blockers
        self._contract = VibeContract(
            stage=VibeStage.DEPLOY_READY if ready else VibeStage.SMOKE_FAILED,
            pins=current.pins,
            env=current.env,
            notes=current.notes,
            coder_allowed=current.coder_allowed,
            implemented=current.implemented,
            blockers=current.blockers,
            smoke_status="pass" if ok else "fail",
            smoke_detail=detail,
            deploy_ready=ready,
        )
        return self._contract
