import argparse
import json
import sys
from typing import Any, Dict

from .db import connect, tx
from .errors import IngestV2Error, ValidationError
from .fact import ingest_fact_append_only
from .logging_utils import log_event
from .source import get_or_create_source
from .validate import validate_fact_payload


def _load_json_file(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        raise ValidationError("ValidationError:InvalidJsonFile")


def build_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "ingest-fact-v2",
        help="Ingest a V2 fact into ic_v2.fact (append-only, idempotent) and upsert ic_v2.source.",
    )
    p.add_argument("--json", required=True, help="Path to JSON payload file.")
    p.add_argument("--out", choices=["human", "json"], default="human", help="Output format.")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    payload = _load_json_file(args.json)

    if not isinstance(payload, dict) or "source" not in payload or "fact" not in payload:
        raise ValidationError("ValidationError:MissingRootKeys:source,fact")
    if not isinstance(payload["source"], dict) or not isinstance(payload["fact"], dict):
        raise ValidationError("ValidationError:InvalidRootTypes:source,fact")

    source_payload = payload["source"]
    fact_payload = payload["fact"]

    validate_fact_payload(fact_payload)

    log_event("ic_v2.ingest_fact_v2.start", command="ingest-fact-v2")

    conn = connect()
    try:
        with tx(conn):
            source_id, source_outcome = get_or_create_source(conn, source_payload)
            result = ingest_fact_append_only(conn, fact_payload, source_id)

        log_event(
            "ic_v2.ingest_fact_v2.done",
            outcome=result.get("outcome"),
            source_outcome=source_outcome,
            source_id=source_id,
            fact_id=result.get("fact_id"),
        )

        if args.out == "json":
            sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
        else:
            if result["outcome"] == "OK":
                sys.stdout.write(
                    f"OK: fact ingested | source_id={result['source_id']} fact_id={result['fact_id']} mode={result['idempotency_mode']}\n"
                )
            else:
                sys.stdout.write(
                    f"NOOP: already ingested | source_id={result['source_id']} fact_id={result['fact_id']} mode={result['idempotency_mode']}\n"
                )

        return 0

    except IngestV2Error as e:
        sys.stderr.write(str(e) + "\n")
        return getattr(e, "exit_code", 2)
    except Exception:
        sys.stderr.write("Error:Unhandled\n")
        return 10
    finally:
        try:
            conn.close()
        except Exception:
            pass# ---- module entrypoint ----
def main() -> int:
    parser = argparse.ArgumentParser(prog="ingest-fact-v2")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser(subparsers)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
