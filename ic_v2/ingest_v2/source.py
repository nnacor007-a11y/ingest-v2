from typing import Dict, Tuple, Any
import psycopg2


def _non_empty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str) and v.strip() == "":
        return False
    return True


def _choose_source_match_fields(cols: Dict[str, str], payload: Dict[str, Any]) -> Tuple[str, ...]:
    # 1) Prefer stable match: (system, external_id)
    if (
        "external_id" in cols
        and "system" in cols
        and _non_empty(payload.get("external_id"))
        and _non_empty(payload.get("system"))
    ):
        return ("system", "external_id")

    # 2) Use source_key only if non-empty
    if "source_key" in cols and _non_empty(payload.get("source_key")):
        return ("source_key",)

    if "url" in cols and _non_empty(payload.get("url")):
        return ("url",)

    if "name" in cols and _non_empty(payload.get("name")):
        return ("name",)

    return tuple()


def get_or_create_source(conn, source_payload: Dict[str, Any]):
    """
    Returns: (source_id, source_outcome)
    source_outcome ∈ {"CREATED", "EXISTING"}
    """

    with conn.cursor() as cur:
        # discover table columns
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'ic_v2'
              AND table_name = 'source'
            """
        )
        cols = {r[0]: r[0] for r in cur.fetchall()}

        match_fields = _choose_source_match_fields(cols, source_payload)

        if not match_fields:
            raise RuntimeError("NO_MATCH_POSSIBLE")

        where_clause = " AND ".join(f"{f} = %s" for f in match_fields)
        values = [source_payload.get(f) for f in match_fields]

        cur.execute(
            f"""
            SELECT source_id
            FROM ic_v2.source
            WHERE {where_clause}
            LIMIT 1
            """,
            values,
        )
        row = cur.fetchone()
        if row:
            return row[0], "EXISTING"

        # insert new source
        insert_cols = [k for k in source_payload.keys() if k in cols and source_payload.get(k) is not None]
        insert_values = [source_payload[k] for k in insert_cols]

        col_list = ", ".join(insert_cols)
        placeholders = ", ".join(["%s"] * len(insert_values))

        cur.execute(
            f"""
            INSERT INTO ic_v2.source ({col_list})
            VALUES ({placeholders})
            RETURNING source_id
            """,
            insert_values,
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id, "CREATED"