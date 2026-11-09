"""HumanReceipt verification boundary. No receipt is minted by this package."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any


class ReceiptStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"
    NOT_MEASURED = "NOT_MEASURED"


@dataclass(frozen=True)
class HumanReceipt:
    decision: str
    artifact_digest: str
    scope: tuple[str, ...]
    policy_version: str
    disposition: str
    human_principal: str
    key_id: str
    signature_hex: str


def canonical_receipt_payload(receipt: HumanReceipt) -> bytes:
    body: dict[str, Any] = {
        "decision": receipt.decision,
        "artifact_digest": receipt.artifact_digest,
        "scope": list(receipt.scope),
        "policy_version": receipt.policy_version,
        "disposition": receipt.disposition,
        "human_principal": receipt.human_principal,
        "key_id": receipt.key_id,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def verify_human_receipt(receipt: HumanReceipt,
                         trusted_public_keys: dict[str, bytes]) -> ReceiptStatus:
    """Verify Ed25519 against an externally provisioned key map; never infer trust."""
    key = trusted_public_keys.get(receipt.key_id)
    if key is None:
        return ReceiptStatus.NOT_MEASURED
    if (len(receipt.artifact_digest) != 64
            or any(c not in "0123456789abcdef" for c in receipt.artifact_digest)
            or not receipt.scope or not receipt.human_principal
            or receipt.disposition not in {"APPROVE", "REJECT"}):
        return ReceiptStatus.INVALID
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(key).verify(
            bytes.fromhex(receipt.signature_hex), canonical_receipt_payload(receipt)
        )
    except ImportError:
        return ReceiptStatus.NOT_MEASURED
    except (ValueError, TypeError):
        return ReceiptStatus.INVALID
    except Exception:
        return ReceiptStatus.INVALID
    return ReceiptStatus.VERIFIED
