# Architecture and assurance boundaries

## Product composition

This combined KCN Preflight is intended to unify three capability families:

1. Original KCN Preflight quality-gate intent: code quality, formatting, secret scanning, review findings, CI generation, badges, and PASS/BLOCK release decisions. The original repository branch inspected for this build contained documentation only; these advertised capabilities still require concrete scanner adapters and tests.
2. Governance Substrate mechanisms: append-only hash-chained ledger, immutable-at-write evidence snapshots, canonical artifact integrity, bridge normalization/exact-write checks, per-gate evidence trace, sandbox/deploy policy, and attestation verification. The source substrate remains read-only and untouched.
3. CPG-001: three sequential stages and three independently evaluated checkpoints; all 12 constitutional requirements are evaluated at each checkpoint; failures return to the corresponding stage repair loop.

## Constitutional invariant

The Primordial Rule prohibits any software component, agent, federation, identity provider, test runner, ledger, or automated policy engine from creating or assuming external human authority. This implementation does not contain a mechanism to mint human authority. A future HumanReceipt verifier must validate a human-issued record against an externally provisioned trust root and bind the decision to artifact digest, scope, policy version, and disposition. No automated test result can create that receipt.

## Federation model

Federated identity establishes who or what is presenting a request; it does not establish what that principal may do. Authorization must be evaluated against the resource owner's policy and the delegated scope for each operation. No permissions transfer merely because systems are connected through KCN Link Bridge. Revocation and containment must be propagated as explicit, verifiable policy events. These integrations are not yet implemented and remain NOT_MEASURED.

## Checkpoint rules

- Stage order: VIBE_CODER → VIBE_DEVELOPER → HYBRID.
- Each stage evaluates all 12 requirements independently.
- PASS requires explicit registered evaluators returning evidence-backed PASS for every requirement.
- Any FAIL blocks progression and identifies the same stage as the repair target.
- Any NOT_MEASURED blocks progression.
- Missing stage artifact blocks progression.
- Changed artifact bytes produce a different SHA-256 digest; prior checkpoint evidence must not be reused.
- A later stage's artifact is independently hashed and checked; integration work must additionally invalidate/re-run earlier checkpoints whenever it mutates an earlier stage artifact.
- Automated PASS is not human ratification or permission to deploy.

## Evidence ledger and attestation

The ledger uses canonical JSON and SHA-256 hash chaining, with deep-copy-at-write semantics. This provides tamper-evident sequencing only while the chain's root is independently retained; it is not a signature and does not prove who authored an event. The legacy substrate's keyed-hash construction must not be described as Ed25519 or as an asymmetric digital signature. A future signature adapter must use a vetted cryptographic library, externally managed keys, explicit key IDs, rotation/revocation, and verification tests.

## Runtime / deployment gate

This first kernel does not yet enforce a universal execution gate across shells, APIs, agents, schedulers, deployment systems, subprocesses, or alternate launchers. It must not be represented as doing so. A trusted external launcher and scoped bootstrap policy are required to avoid circular self-authorization. Live CI and production integration are intentionally deferred.

## Known NOT_MEASURED integrations

- Static formatting/lint/security/secret scanning adapters.
- Kronos seven-agent scanner integration and separately verified repair adapters.
- Vibe Coder, Vibe Developer, and hybrid workflow adapters.
- KCN Link Bridge identity, scoped authorization, revocation, and federation adapters.
- HumanReceipt cryptographic verification and external trust-root provisioning.
- Runtime interception and deployment enforcement.
- Original substrate bridge, deploy sandbox, and attestation adapters.
- End-to-end CI and release pipeline.

These are tracked as implementation gaps, not presumed capabilities.


## Isolated integration contracts (initial implementation)

The replacement branch now contains additive adapter boundaries:

- `bridge.py`: exact-byte write verification and structural request validation. It does not grant permission or implement the complete original Link Bridge transport.
- `federation.py`: resource-owner-scoped delegation checks, explicit identity-verification input, and immutable revocation snapshots. It is a policy primitive, not a production federation/identity provider.
- `receipts.py`: Ed25519 HumanReceipt verification against externally provisioned public keys. It never creates receipts or trust roots. The optional `cryptography` dependency must be installed and key provisioning, rotation, revocation, and end-to-end tests remain outstanding.
- `scanner.py`: scanner finding and repair proposal contracts. Kronos agents are not yet connected; classification and repair remain separate.
- `workflow.py`: stage adapter and stage-local repair-routing contracts. Vibe Coder, Vibe Developer, and Hybrid executors are not yet connected.
- `tests/test_integrations.py`: focused tests have been added but have NOT been executed in this environment.

These are additive files on `cpg-001-combined`; no supporting repository was changed. No CI workflow was enabled. No runtime-wide execution gate, production federation, full original quality gate, or replacement qualification is claimed.


## Source-capability integrations added after initial adapter scaffolding

The following actual source capabilities have now been copied into the isolated replacement branch, with source repositories unchanged:

1. **Kronos SwarmScanner built-in scan** — source copied from `Evank253/Kronos-Vibe-Coder/backend/agents/swarm/scanner.py` at observed revision `d08944d6bbaeb1868073c30e6ab02a925ba8f7a5`. `kronos_adapter.py` executes only the scanner's built-in static scan against a temporary copy of submitted bytes. It deliberately does not call the source scanner's full `scan()` because that method runs pytest and optional external tools. Kronos' original agent pool/task manager and all seven-agent orchestration are NOT yet integrated. This is a real scanner capability integration, not the complete Kronos system.
2. **Governance Substrate NormalizationGate** — source copied from `FINAL-VERSION-MMD_002/kcn-governance-substrate/bridge.py`; `substrate_adapter.py` exposes canonicalization, identifier checks, and exact-write validation. This is not the complete cross-system Link Bridge.
3. **Governance Substrate EvidenceTrace** — source copied from `FINAL-VERSION-MMD_002/kcn-governance-substrate/evidence_trace.py`; adapter preserves per-gate stamps and divergence events.
4. **Vibe Developer ↔ Vibe Coder contract** — `vibe_contract.py` implements the original published-pins-before-coder, coder acknowledgement, and smoke-result flow from `vibe-developer/server/services/vibeContract.js` and `vibeBridge.js`. The integration is a Python adapter with isolated in-memory state, not a live connection to the original Node service. It deliberately tightens deployment readiness: smoke PASS cannot clear unresolved coder blockers.

### Still not integrated / not validated

- Kronos' full agent pool, task manager, seven-agent orchestration, and separately approved repair execution.
- Live Vibe Developer / Vibe Coder service connection, hybrid executor, and persistent contract transport.
- Original Governance Substrate deploy simulator and full Preflight source-checker behavior.
- Production federation, identity provider integration, KCN Link Bridge transport, revocation propagation.
- Runtime-wide execution enforcement and trusted bootstrap.
- HumanReceipt trust-root provisioning, key lifecycle, and full cryptographic verification tests.
- Full end-to-end suite execution. Test files have been added, but no test command has been run; status remains NOT_MEASURED.
