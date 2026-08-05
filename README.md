# KCN Preflight

**Official development quality gate & assurance pipeline for the entire KCN ecosystem.**

This replaces the previous “vibe coder / vibe developer” concept with a real, inspectable, decision-driven pre-push system.

```
$ preflight check .

VERDICT: PASS or BLOCK
```

---

## What it does

| Feature | Behavior |
|---------|----------|
| **Formatting engine** | Runs `black` (Python), `prettier` (JS/TS), `gofmt` (Go) *before* review — spacing/punctuation issues are silently fixed, never warned about |
| **Secret scanning** | Hard blocker if AWS/GitHub/OpenAI-style keys or high-entropy secrets are found |
| **Code review** | Real tools: `ruff` + `bandit` (Python), `eslint` (JS/TS), `go vet` (Go) |
| **Dependency injection** | Detects missing imports and auto-adds them to manifests |
| **CI/CD generation** | Writes tailored GitHub Actions workflows |
| **Badge generation** | Real shields.io badges (language, license, CI, PASS/BLOCK) |
| **README sync** | Maintains a machine-owned section reflecting current project state |
| **Deployment advice** | Evidence-based recommendations (Vercel, Render, Fly.io, etc.) |

---

## Design Philosophy (Precision, not blindness)

- Auto-fix everything that is mechanically safe (formatting, missing deps, .env.example, badges).
- Only surface real judgment calls or security issues to the human.
- Never silently skip unknown languages or pretend success.
- Exit code 0 = PASS, 1 = BLOCK — safe for git hooks and CI.

This matches the **KCN Assurance Protocol (KAP)** principles, especially:
- Zero unprotected secrets leaked
- Evidence-based attestation
- Transparent, inspectable process

---

## Position in the KCN Ecosystem

```
KCN Command Center (umbrella)
├── kcn-worldview
├── kcn-cyber-security-hq
├── kcn-nano-banana-world-design
├── kcn-human-ai-personal-growth
└── kcn-preflight          ← this tool (official quality gate)
```

Every other KCN system should run `preflight check .` before pushing.

---

## Owner
Fully free for the creator (Evank253).

## Related
- Umbrella portal: https://github.com/Evank253/kcn-worldview-command-center
- KCN Assurance Protocol (KAP) governance standard
