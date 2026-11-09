# KCN Preflight — Constitutional Governance & Engineering Assurance

**Development branch:** `cpg-001-combined`  
**Status:** Initial implementation foundation — NOT QUALIFIED, NOT RATIFIED, NOT LIVE.

KCN Preflight is being rebuilt as a constitutional governance and engineering-assurance system. It combines the original KCN Preflight quality-gate role, the documented Governance Substrate capabilities, and CPG-001's three-stage / three-checkpoint assurance lifecycle.

## Non-negotiable constitutional boundary

The Primordial Rule is that no system may create, grant, modify, or assume its own authority. External Human Authority remains outside the software. Identity is not authority; a test result is not qualification; qualification is not ratification. Automated checks can produce evidence and block progression, but cannot issue human authorization.

## Combined capabilities

- **Constitution:** Primordial Rule, human authority separation, HumanReceipt boundary, H0–H3 model, fail-closed dispositions, and explicit `NOT_MEASURED`.
- **Federation:** independently scoped identities and permissions, KCN Link Bridge interoperability, provenance, revocation/containment boundaries, and cross-system cooperation without permission inheritance.
- **Engineering assurance:** original KCN Preflight's quality-gate intent; substrate ledger, attestation boundary, bridge integrity, evidence trace and deploy-policy concepts; Vibe Coder / Vibe Developer stage interfaces; and Kronos-style scan/classify/repair integration only through verified adapters.
- **CPG-001:** Vibe Coder → Preflight 1 → Vibe Developer → Preflight 2 → Hybrid Coder/Developer → Preflight 3. Every checkpoint evaluates all 12 requirements independently. A failed checkpoint routes to its own stage's repair loop.

## Current implementation boundary

This branch contains an initial executable assurance kernel, not the complete ecosystem integration. Unimplemented integrations remain `NOT_MEASURED`; they are never silently treated as PASS. No live CI workflow is enabled by this build. Live CI and production takeover are deferred until the complete product has been built, audited, tested, and explicitly authorized.

The original `Python-3` branch is retained as the historical KCN Preflight baseline. Its README described the official ecosystem quality gate, formatting, secret scanning, code review, CI generation, badges, and PASS/BLOCK verdict. Its repository tree contained only `README.md` and `KCN_LAUNCH_ALIGNMENT.md`, not an executable checker. The runnable legacy checker mechanisms were found in the separate Governance Substrate repository and are being reconstructed here without modifying that source repository.

## Development validation plan

1. Build the combined implementation on this isolated branch.
2. Run the available original Substrate checker logic as an external/read-only baseline against the candidate.
3. Classify findings; repair only this branch; rerun the baseline after each repair.
4. Run the complete local test suite, static checks, security checks, and integration tests.
5. Execute all three CPG-001 checkpoints with all 12 requirements at each checkpoint.
6. Preserve artifact hashes, policy version, evidence, dispositions, and repair history.
7. Keep live CI and production promotion disabled until the above evidence is complete and external human authorization is recorded.

**No source Governance Substrate files are modified by this branch.** See `docs/architecture.md` for the assurance model and known limitations.
