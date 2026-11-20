# KCN Preflight Application

This directory contains the independent KCN Preflight application. The Natural Language Builder was a tool used to create this application; it is not a runtime dependency or component.

## Workflow

1. Vibe Coder inspection
2. Vibe Developer inspection
3. Combined Vibe Coder / Vibe Developer hybrid inspection
4. Constitutional governance integration
5. Final independent preflight
6. CI qualification
7. External Human Authority authorization
8. Deployment handoff (this application does not deploy systems)

Every stage is fail-closed. A stage cannot pass without a configured adapter returning an explicit PASS and an evidence artifact digest. Missing adapters, malformed responses, missing evidence, timeouts, and failed checks block progression.

## Important implementation boundary

This is the first executable application foundation: workflow state machine, persisted project/stage records, adapter contracts, evidence gates, operator interface, and tests. It does not pretend that the Vibe systems or governance integration are already connected. Their real endpoints must be configured and must implement the adapter contract below. No connector is simulated as successful.

The constitutional integration adapter is expected to inspect the target system and integrate missing KHGSI governance controls into its actual architecture and execution paths, while preserving existing work and recording a reversible change set. It must not merely return a documentation-only compliance statement.

External Human Authority remains outside this application. The human-authorization adapter must route a scoped approval request to the external authority and return a verifiable receipt. This app cannot create its own authority or treat a local button click as ratification.

## Run locally

Python 3.11+

```bash
cd application
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn kcn_preflight.main:app --reload
```

Open http://127.0.0.1:8000.

## Adapter configuration

Set the following environment variables to the actual service endpoints. Do not point them at mock services for qualification.

- `KCN_VIBE_CODER_URL`
- `KCN_VIBE_DEVELOPER_URL`
- `KCN_HYBRID_URL`
- `KCN_CONSTITUTIONAL_INTEGRATION_URL`
- `KCN_CI_QUALIFICATION_URL`
- `KCN_HUMAN_AUTHORITY_URL`

The final independent preflight is performed by this application from persisted stage evidence. Deployment is intentionally a handoff only; no production deployment is triggered.

## Adapter request contract

Each adapter receives a POST request with:

- `project_id`
- `project`: project name, repository URL, immutable source ref, and declared source digest
- `stage`
- `policy_version`
- `prior_evidence`: evidence records from completed prior stages
- `requirements`: stage-specific acceptance requirements

A successful response must be JSON containing:

```json
{
  "status": "PASS",
  "evidence": ["https://... or artifact identifier"],
  "artifact_digest": "sha256:<64 lowercase hex characters>",
  "summary": "What was inspected, changed, and verified",
  "change_set": {
    "created": [],
    "modified": [],
    "preserved": [],
    "rollback_reference": "..."
  }
}
```

For human authorization, the response must additionally contain a non-empty `human_receipt_id`, the exact approved `artifact_digest`, `scope`, `policy_version`, and `disposition` equal to `APPROVED`. A normal PASS response is not sufficient.

## Status semantics

- `NOT_MEASURED` is not PASS.
- `BLOCKED` means a required adapter/evidence/gate is missing or invalid.
- `FAIL` means an adapter explicitly failed.
- Only an explicit, evidence-backed PASS advances the workflow.
- Discovery, capability, evidence, qualification, permission, authorization, and ratification remain distinct.

## Safety and scope

The application does not execute arbitrary project code, grant permissions, create credentials, or deploy to production. Source identity is pinned by immutable ref and declared digest; adapters are responsible for independently verifying the received source digest before processing. Keep the database and service endpoints on a trusted development network until authentication and deployment controls are independently reviewed.
