-- ic_v2 Sprint1: DB hardening (append-only + idempotency)
-- Append-only: fact forbids UPDATE/DELETE/TRUNCATE (triggers)
-- Idempotency: fact fingerprint unique (partial), source (system, external_id) unique (partial)

BEGIN;

CREATE OR REPLACE FUNCTION ic_v2.enforce_append_only()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'append-only violation on %.%: % not permitted', TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP
    USING ERRCODE = 'P0001';
END;
$$;

DROP TRIGGER IF EXISTS fact_append_only_ud ON ic_v2.fact;
CREATE TRIGGER fact_append_only_ud
BEFORE UPDATE OR DELETE ON ic_v2.fact
FOR EACH ROW
EXECUTE FUNCTION ic_v2.enforce_append_only();

DROP TRIGGER IF EXISTS fact_append_only_trunc ON ic_v2.fact;
CREATE TRIGGER fact_append_only_trunc
BEFORE TRUNCATE ON ic_v2.fact
FOR EACH STATEMENT
EXECUTE FUNCTION ic_v2.enforce_append_only();

CREATE UNIQUE INDEX IF NOT EXISTS fact_fingerprint_uq
ON ic_v2.fact (fingerprint)
WHERE fingerprint IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS source_system_external_uq
ON ic_v2.source (system, external_id)
WHERE system IS NOT NULL AND external_id IS NOT NULL;

COMMIT;