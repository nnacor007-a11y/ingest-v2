from typing import Any, Dict, Tuple

from .db import advisory_xact_lock, get_table_columns
from .errors import DbError
from .fingerprint import advisory_lock_key, fingerprint_hex


def _choose_source_match_fields(cols: Dict[str, str]) -> Tuple[str, ...]:
    if "source_key" in cols:
        return ("source_key",)
    if "external_id" in cols and "system" in cols:
        return ("system", "external_id")
    if "url" in cols:
        return ("url",)
    if "name" in cols:
        return ("name",)
    return tuple()


def _choose_insert_fields(cols: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
    candidate = {
        "source_key": payload.get("source_key"),
        "system": payload.get("system"),
        "external_id": payload.get("external_id"),
        "name": payload.get("name"),
        "url": payload.get("url"),
        "description": payload.get("description"),
        "meta": payload.get("meta"),
    }
    return {k: v for k, v in candidate.items() if k in cols and v is not None}


def get_or_create_source(conn, source_payload: Dict[str, Any]) -> Tuple[int, str]:
    schema, table = "ic_v2", "source"
    try:
        with conn.cursor() as cur:
            cols = get_table_columns(cur, schema, table)

            stable = {
                "system": source_payload.get("system"),
                "external_id": source_payload.get("external_id"),
                "source_key": source_payload.get("source_key"),
                "url": source_payload.get("url"),
                "name": source_payload.get("name"),
            }
            fp = fingerprint_hex(stable)
            advisory_xact_lock(cur, advisory_lock_key(fp))

            match_fields = _choose_source_match_fields(cols)

            if match_fields:
                where = " AND ".join([f"{f} = %s" for f in match_fields])
                params = tuple(source_payload.get(f) for f in match_fields)
                cur.execute(
                    f"SELECT source_id FROM {schema}.{table} WHERE {where} ORDER BY source_id ASC LIMIT 1;",
                    params,
                )
                row = cur.fetchone()
                if row:
                    return int(row[0]), "EXISTING"

            insert_fields = _choose_insert_fields(cols, source_payload)

            if insert_fields:
                cols_sql = ", ".join(insert_fields.keys())
                vals_sql = ", ".join(["%s"] * len(insert_fields))
                params = tuple(insert_fields.values())
                cur.execute(
                    f"INSERT INTO {schema}.{table} ({cols_sql}) VALUES ({vals_sql}) RETURNING source_id;",
                    params,
                )
                return int(cur.fetchone()[0]), "CREATED"

            cur.execute(f"INSERT INTO {schema}.{table} DEFAULT VALUES RETURNING source_id;")
            return int(cur.fetchone()[0]), "CREATED"

    except Exception as e:
        raise DbError("DbError:SourceUpsertFailed") from e