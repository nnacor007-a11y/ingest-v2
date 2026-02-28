import os
from contextlib import contextmanager
from typing import Any, Dict, Iterator

from .errors import DbError

try:
    import psycopg2
except Exception as e:
    raise DbError("DbError:MissingDependency:psycopg2") from e


def _get_dsn() -> str:
    dsn = os.getenv("DATABASE_URL") or os.getenv("PG_DSN") or ""
    if not dsn:
        raise DbError("DbError:MissingEnv:DATABASE_URL")
    return dsn


def connect():
    try:
        conn = psycopg2.connect(_get_dsn())
        conn.autocommit = False
        return conn
    except Exception as e:
        raise DbError("DbError:ConnectFailed") from e


@contextmanager
def tx(conn) -> Iterator[Any]:
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def advisory_xact_lock(cur, key64: int) -> None:
    cur.execute("SELECT pg_advisory_xact_lock(%s);", (key64,))


def get_table_columns(cur, schema: str, table: str) -> Dict[str, str]:
    cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (schema, table),
    )
    return {r[0]: r[1] for r in cur.fetchall()}