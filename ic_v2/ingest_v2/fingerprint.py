import hashlib
import json
from typing import Any, Dict


def _canonicalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _canonicalize(obj[k]) for k in sorted(obj.keys(), key=lambda x: str(x))}
    if isinstance(obj, list):
        return [_canonicalize(x) for x in obj]
    if isinstance(obj, float):
        return float(f"{obj:.12g}")
    return obj


def fingerprint_hex(payload: Dict[str, Any]) -> str:
    canonical = _canonicalize(payload)
    raw = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def advisory_lock_key(fingerprint: str) -> int:
    v = int(fingerprint[:16], 16)
    if v >= 2**63:
        v -= 2**64
    return v