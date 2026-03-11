-- ic_v2 Sprint2: migration execution log (runner idempotency control)

BEGIN;

CREATE TABLE IF NOT EXISTS ic_v2.migration_log (
    id              BIGSERIAL PRIMARY KEY,
    filename        TEXT NOT NULL,
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    checksum        TEXT NOT NULL,
    UNIQUE (filename)
);

COMMIT;