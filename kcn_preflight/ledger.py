"""Append-only, hash-chained evidence ledger (integrity, not a digital signature)."""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class LedgerEntry:
    sequence: int
    previous_hash: str
    payload: dict[str, Any]
    entry_hash: str


class EvidenceLedger:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def append(self, payload: dict[str, Any]) -> LedgerEntry:
        snapshot = copy.deepcopy(payload)
        previous = self._entries[-1].entry_hash if self._entries else "0" * 64
        body = {"sequence": len(self._entries), "previous_hash": previous, "payload": snapshot}
        digest = hashlib.sha256(canonical_json(body)).hexdigest()
        entry = LedgerEntry(len(self._entries), previous, snapshot, digest)
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        previous = "0" * 64
        for index, entry in enumerate(self._entries):
            if entry.sequence != index or entry.previous_hash != previous:
                return False
            body = {"sequence": index, "previous_hash": previous, "payload": entry.payload}
            expected = hashlib.sha256(canonical_json(body)).hexdigest()
            if expected != entry.entry_hash:
                return False
            previous = entry.entry_hash
        return True
