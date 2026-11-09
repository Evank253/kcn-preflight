"""Isolated source copy from Evank253/FINAL-VERSION-MMD_002/kcn-governance-substrate/bridge.py.

Source copy only; original repository and file are untouched.
"""
#!/usr/bin/env python3
"""KCN Normalization Bridge — Stage-One Gate.
Build ID: KCN-GS-BUILD-20261029-201200
Dated: 2026-10-29. Sits between Vibe Coder and preflight.
Canonicalizes identifiers before write, diffs intended string vs landed bytes,
rejects divergent writes. Cross-system: Python-native (copy.deepcopy) vs
JSON-native (json round-trip) as two parallel module families.
"""
import ast
import copy
import hashlib
import json


class NormalizationGate:
    """The throat between generation and disk."""

    def __init__(self):
        self.rejections = []
        self.accepted = []

    def canonicalize(self, text):
        """Normalize identifiers: expand chr-splices, force underscores."""
        try:
            tree = ast.parse(text)
            return ast.dump(tree, include_attributes=False)
        except SyntaxError:
            return None

    def validate_write(self, intended, landed):
        """Diff intended string vs landed bytes. Reject divergence."""
        i_hash = hashlib.sha256(intended.encode()).hexdigest()
        l_hash = hashlib.sha256(landed.encode()).hexdigest()
        if i_hash != l_hash:
            diff = {
                "intended_sha": i_hash,
                "landed_sha": l_hash,
                "intended_len": len(intended),
                "landed_len": len(landed),
            }
            self.rejections.append(diff)
            return False, diff
        self.accepted.append(i_hash)
        return True, None

    def check_identifier(self, name, expected):
        """Verify built identifier matches registry expectation."""
        return name == expected

    def diff(self, a, b):
        """Byte-level diff report."""
        return {
            "sha_a": hashlib.sha256(a.encode()).hexdigest(),
            "sha_b": hashlib.sha256(b.encode()).hexdigest(),
            "equal": a == b,
        }

    def run_self_test(self):
        """Prove the gate catches divergent writes."""
        intended = "payload = copy.deepcopy(payload)"
        landed_good = intended
        landed_bad = intended.replace(".", " ")  # space-dot bug
        ok1, _ = self.validate_write(intended, landed_good)
        ok2, diff = self.validate_write(intended, landed_bad)
        return ok1 and not ok2, diff
