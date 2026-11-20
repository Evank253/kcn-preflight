from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB_PATH = Path(os.getenv("KCN_PREFLIGHT_DB", "kcn-preflight.sqlite3"))
POLICY_VERSION = os.getenv("KCN_PREFLIGHT_POLICY_VERSION", "KHGSI-PREFLIGHT-0.1")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

STAGES = [
    ("vibe_coder", "Vibe Coder inspection", "KCN_VIBE_CODER_URL"),
    ("vibe_developer", "Vibe Developer inspection", "KCN_VIBE_DEVELOPER_URL"),
    ("hybrid", "Combined engineering hybrid", "KCN_HYBRID_URL"),
    ("constitutional_integration", "Constitutional governance integration", "KCN_CONSTITUTIONAL_INTEGRATION_URL"),
    ("final_preflight", "Final independent preflight", None),
    ("ci_qualification", "CI qualification", "KCN_CI_QUALIFICATION_URL"),
    ("human_authorization", "External Human Authority authorization", "KCN_HUMAN_AUTHORITY_URL"),
    ("deployment_handoff", "Deployment handoff", None),
]

REQUIREMENTS = {
    "vibe_coder": [
        "Inspect repository structure, code, architecture, dependencies, and implementation.",
        "Run applicable analysis and tests; record findings and evidence.",
        "Do not silently modify source during inspection.",
    ],
    "vibe_developer": [
        "Perform independent engineering/development inspection.",
        "Verify changes, tests, dependencies, and implementation evidence.",
    ],
    "hybrid": [
        "Run the combined Vibe Coder and Vibe Developer engineering pass.",
        "Reconcile findings and preserve traceable lineage and evidence.",
    ],
    "constitutional_integration": [
        "Inspect actual execution paths for KHGSI governance controls.",
        "Integrate missing controls into the target system, not documentation alone.",
        "Preserve originals; create a reversible change set and rollback reference.",
        "Keep External Human Authority outside software; no proxy or self-granted authority.",
        "Enforce fail-closed behavior and distinguish capability, evidence, qualification, permission, authorization, and ratification.",
        "Verify federation boundaries and Primordial Rule subordination to External Human Authority.",
    ],
    "ci_qualification": [
        "Run the target system's required CI and qualification checks.",
        "Provide immutable evidence and explicit results for all required checks.",
    ],
    "human_authorization": [
        "Route the exact qualified artifact digest, scope, and policy version to External Human Authority.",
        "Return a verifiable HumanReceipt with explicit APPROVED disposition.",
    ],
}

class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    repository_url: HttpUrl
    source_ref: str = Field(min_length=7, max_length=160)
    source_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    scope: str = Field(min_length=3, max_length=500)

class AdapterResult(BaseModel):
    status: str
    evidence: list[str] = Field(default_factory=list)
    artifact_digest: str = ""
    summary: str = ""
    change_set: dict[str, Any] = Field(default_factory=dict)
    human_receipt_id: str = ""
    scope: str = ""
    policy_version: str = ""
    disposition: str = ""

app = FastAPI(title="KCN Preflight", version="0.1.0")

def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db() -> None:
    with db() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, repository_url TEXT NOT NULL,
            source_ref TEXT NOT NULL, source_digest TEXT NOT NULL, scope TEXT NOT NULL,
            created_at TEXT NOT NULL, current_stage INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'IN_PROGRESS'
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS stage_runs (
            id TEXT PRIMARY KEY, project_id TEXT NOT NULL, stage_key TEXT NOT NULL,
            stage_index INTEGER NOT NULL, status TEXT NOT NULL, evidence_json TEXT NOT NULL,
            artifact_digest TEXT NOT NULL, summary TEXT NOT NULL, result_json TEXT NOT NULL,
            created_at TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(id)
        )""")

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def project_row(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)

def get_project(project_id: str) -> dict[str, Any]:
    with db() as connection:
        row = connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Project not found")
    return project_row(row)

def get_runs(project_id: str) -> list[dict[str, Any]]:
    with db() as connection:
        rows = connection.execute(
            "SELECT * FROM stage_runs WHERE project_id=? ORDER BY stage_index", (project_id,)
        ).fetchall()
    return [dict(row) for row in rows]

def record_run(project_id: str, stage_key: str, stage_index: int,
               status: str, result: dict[str, Any]) -> None:
    with db() as connection:
        connection.execute(
            """INSERT INTO stage_runs
            (id, project_id, stage_key, stage_index, status, evidence_json,
             artifact_digest, summary, result_json, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), project_id, stage_key, stage_index, status,
             json.dumps(result.get("evidence", [])), result.get("artifact_digest", ""),
             result.get("summary", ""), json.dumps(result), now()),
        )
        connection.execute(
            "UPDATE projects SET current_stage=?, status=? WHERE id=?",
            (stage_index, "BLOCKED" if status != "PASS" else "IN_PROGRESS", project_id),
        )

def validate_adapter_result(stage_key: str, result: AdapterResult, project: dict[str, Any]) -> tuple[bool, str]:
    if result.status != "PASS":
        return False, "Adapter did not return explicit PASS."
    if not result.evidence:
        return False, "PASS rejected: evidence list is empty."
    if not DIGEST_RE.fullmatch(result.artifact_digest):
        return False, "PASS rejected: missing or malformed artifact digest."
    if stage_key == "human_authorization":
        if result.disposition != "APPROVED":
            return False, "Human authorization is not explicitly APPROVED."
        if not result.human_receipt_id:
            return False, "HumanReceipt identifier is missing."
        if result.artifact_digest != project["source_digest"]:
            return False, "HumanReceipt digest does not match the pinned project digest."
        if result.scope != project["scope"] or result.policy_version != POLICY_VERSION:
            return False, "HumanReceipt scope or policy version does not match."
    if stage_key == "constitutional_integration":
        required = {"created", "modified", "preserved", "rollback_reference"}
        if not required.issubset(result.change_set):
            return False, "Governance integration must return a reversible change set."
        if not result.change_set.get("rollback_reference"):
            return False, "Governance integration rollback reference is empty."
    return True, "Evidence-backed PASS."

async def call_adapter(url: str, payload: dict[str, Any]) -> AdapterResult:
    timeout = float(os.getenv("KCN_PREFLIGHT_ADAPTER_TIMEOUT", "45"))
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return AdapterResult.model_validate(response.json())

def final_preflight(project: dict[str, Any], runs: list[dict[str, Any]]) -> AdapterResult:
    required_prior = ["vibe_coder", "vibe_developer", "hybrid", "constitutional_integration"]
    by_stage = {run["stage_key"]: run for run in runs}
    missing = [key for key in required_prior if key not in by_stage or by_stage[key]["status"] != "PASS"]
    if missing:
        raise HTTPException(409, f"Final preflight blocked; missing passing stages: {', '.join(missing)}")
    evidence: list[str] = []
    for key in required_prior:
        evidence.extend(json.loads(by_stage[key]["evidence_json"]))
    manifest = {
        "project_id": project["id"],
        "source_digest": project["source_digest"],
        "policy_version": POLICY_VERSION,
        "verified_stages": required_prior,
        "evidence": evidence,
        "human_authority_is_external": True,
        "deployment_triggered": False,
    }
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    return AdapterResult(
        status="PASS",
        evidence=[f"preflight-manifest:sha256:{digest}"],
        artifact_digest=f"sha256:{digest}",
        summary="Local gate verified required upstream stage records and produced a final evidence manifest.",
    )

@app.on_event("startup")
def startup() -> None:
    init_db()

@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")

@app.get("/api/config")
def config() -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "stages": [
            {"key": key, "label": label, "configured": bool(os.getenv(env)) if env else True}
            for key, label, env in STAGES
        ],
        "deployment_mode": "HANDOFF_ONLY",
    }

@app.post("/api/projects")
def create_project(payload: ProjectCreate) -> dict[str, Any]:
    project_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            """INSERT INTO projects
            (id, name, repository_url, source_ref, source_digest, scope, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (project_id, payload.name, str(payload.repository_url), payload.source_ref,
             payload.source_digest, payload.scope, now()),
        )
    return get_project(project_id)

@app.get("/api/projects")
def list_projects() -> list[dict[str, Any]]:
    with db() as connection:
        rows = connection.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    return [project_row(row) for row in rows]

@app.get("/api/projects/{project_id}")
def project_detail(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    return {"project": project, "runs": get_runs(project_id), "stages": STAGES}

@app.post("/api/projects/{project_id}/run-next")
async def run_next(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    runs = get_runs(project_id)
    next_index = len(runs)
    if next_index >= len(STAGES):
        raise HTTPException(409, "Workflow is already complete.")
    stage_key, label, env_name = STAGES[next_index]
    if stage_key == "deployment_handoff":
        if not runs or runs[-1]["stage_key"] != "human_authorization" or runs[-1]["status"] != "PASS":
            raise HTTPException(409, "Deployment handoff blocked: External Human Authority approval is required.")
        result = AdapterResult(
            status="PASS",
            evidence=[f"handoff-record:{project_id}"],
            artifact_digest=project["source_digest"],
            summary="Qualified artifact handed off. No deployment was performed.",
        )
    elif stage_key == "final_preflight":
        result = final_preflight(project, runs)
    else:
        url = os.getenv(env_name or "")
        if not url:
            raise HTTPException(503, f"{label} is BLOCKED: configure {env_name}. No stage was marked PASS.")
        payload = {
            "project_id": project_id,
            "project": project,
            "stage": stage_key,
            "policy_version": POLICY_VERSION,
            "prior_evidence": runs,
            "requirements": REQUIREMENTS.get(stage_key, []),
        }
        try:
            result = await call_adapter(url, payload)
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(502, f"{label} adapter failed closed: {type(exc).__name__}.") from exc
    valid, reason = validate_adapter_result(stage_key, result, project)
    status = "PASS" if valid else "BLOCKED"
    record_run(project_id, stage_key, next_index, status, result.model_dump())
    if not valid:
        raise HTTPException(409, f"{label} did not qualify: {reason}")
    return {"stage": stage_key, "label": label, "status": status, "result": result.model_dump()}

@app.get("/api/projects/{project_id}/evidence")
def evidence(project_id: str) -> dict[str, Any]:
    project = get_project(project_id)
    runs = get_runs(project_id)
    return {
        "project_id": project_id,
        "source_digest": project["source_digest"],
        "policy_version": POLICY_VERSION,
        "stages": [
            {
                "stage": run["stage_key"],
                "status": run["status"],
                "evidence": json.loads(run["evidence_json"]),
                "artifact_digest": run["artifact_digest"],
                "summary": run["summary"],
            }
            for run in runs
        ],
    }
