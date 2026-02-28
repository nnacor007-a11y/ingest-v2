import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable


SENSITIVE_KEYS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "apikey",
    "api_key",
    "connection_string",
    "database_url",
    "dsn",
    "auth",
    "authorization",
}


def _redact(obj: Any, path: Iterable[str] = ()) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            k_str = str(k)
            if k_str.lower() in SENSITIVE_KEYS:
                out[k_str] = "***REDACTED***"
            else:
                out[k_str] = _redact(v, (*path, k_str))
        return out
    if isinstance(obj, list):
        return [_redact(x, path) for x in obj]
    if isinstance(obj, str) and len(obj) > 500:
        return obj[:200] + "...(truncated)..."
    return obj


def log_event(event: str, **fields: Any) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **_redact(fields),
    }
    sys.stderr.write(json.dumps(record, ensure_ascii=False) + "\n")