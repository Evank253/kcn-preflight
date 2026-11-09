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
