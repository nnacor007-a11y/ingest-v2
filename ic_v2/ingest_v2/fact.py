import json
from typing import Any, Dict, Optional, Tuple

from .db import advisory_xact_lock, get_table_columns
from .errors import DbError
from .fingerprint import advisory_lock_key, fingerprint_hex


def _choose_fact_json_column(cols: Dict[str, str]) -> Optional[str]:
    for c in ("meta", "metadata", "payload", "data", "attributes"):
        if c in cols:
            return c
    return None


def _choose_fact_match_predicate(cols: Dict[str, str], json_col: Optional[str]) -> Tuple[str, str]:
    if "fingerprint" in cols:
        return ("fingerprint = %s", "COL:fingerprint")
    if json_col:
        return (f"({json_col} ->> 'ingest_fingerprint') = %s", f"JSON:{json_col}")

    core = []
    for f in ("source_id", "fact_type", "target_entity_type", "target_entity_id"):
        if f in cols:
            core.append(f)

    if core:
        where = " AND ".join([f"{f} = %s" for f in core])
        return (where, "CORE_FIELDS")

    return ("1=0", "NO_MATCH_POSSIBLE")


def ingest_fact_append_only(conn, fact_payload: Dict[str, Any], source_id: int) -> Dict[str, Any]:
    schema, table = "ic_v2", "fact"

    try:
        with conn.cursor() as cur:
            cols = get_table_columns(cur, schema, table)
            json_col = _choose_fact_json_column(cols)

            stable = dict(fact_payload)
            stable["source_id"] = source_id
            fp = fingerprint_hex(stable)

            advisory_xact_lock(cur, advisory_lock_key(fp))

            where_sql, mode = _choose_fact_match_predicate(cols, json_col)

            if mode.startswith("COL:") or mode.startswith("JSON:"):
                check_params = (fp,)
            elif mode == "CORE_FIELDS":
                core_vals = []
                for f in ("source_id", "fact_type", "target_entity_type", "target_entity_id"):
                    if f in cols:
                        core_vals.append(source_id if f == "source_id" else fact_payload.get(f))
                check_params = tuple(core_vals)
            else:
                check_params = tuple()

            exists = False
            row = None

            if mode != "NO_MATCH_POSSIBLE":
                cur.execute(
                    f"SELECT fact_id FROM {schema}.{table} WHERE {where_sql} ORDER BY fact_id ASC LIMIT 1;",
                    check_params,
                )
                row = cur.fetchone()
                exists = bool(row)

            if exists:
                return {
                    "outcome": "NOOP",
                    "reason": "AlreadyIngested",
                    "idempotency_mode": mode,
                    "source_id": source_id,
                    "fact_id": int(row[0]),
                    "fingerprint": fp,
                }

            insert: Dict[str, Any] = {}

            if "source_id" in cols:
                insert["source_id"] = source_id
            if "fact_type" in cols:
                insert["fact_type"] = fact_payload.get("fact_type")
            if "target_entity_type" in cols:
                insert["target_entity_type"] = fact_payload.get("target_entity_type")
            if "target_entity_id" in cols:
                insert["target_entity_id"] = fact_payload.get("target_entity_id")
            if "confidence" in cols:
                insert["confidence"] = fact_payload.get("confidence")
            if "fingerprint" in cols:
                insert["fingerprint"] = fp

            if json_col:
                payload_copy = dict(fact_payload)
                payload_copy["ingest_fingerprint"] = fp
                payload_copy["source_id"] = source_id
                insert[json_col] = json.dumps(payload_copy, ensure_ascii=False)

            if not insert:
                raise DbError("DbError:FactInsertNoColumns")

            cols_sql = ", ".join(insert.keys())
            vals_sql = ", ".join(["%s"] * len(insert))
            params = tuple(insert.values())

            cur.execute(
                f"INSERT INTO {schema}.{table} ({cols_sql}) VALUES ({vals_sql}) RETURNING fact_id;",
                params,
            )

            fact_id = int(cur.fetchone()[0])

            return {
                "outcome": "OK",
                "idempotency_mode": mode,
                "source_id": source_id,
                "fact_id": fact_id,
                "fingerprint": fp,
            }

    except DbError:
        raise
    except Exception as e:
        raise DbError("DbError:FactIngestFailed") from e