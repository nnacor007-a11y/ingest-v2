-- migrations/ic_v2/2026-03-01_sprint1_security.sql
-- Sprint 1 ? Security provisioning (NO estructura, NO ontolog?a)
-- Requiere: schema ic_v2 y tablas ic_v2.fact / ic_v2.source existentes.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ingest_writer') THEN
    CREATE ROLE ingest_writer NOLOGIN;
  END IF;
END $$;

-- Schema usage
GRANT USAGE ON SCHEMA ic_v2 TO ingest_writer;

-- Table privileges (least privilege)
GRANT SELECT, INSERT ON TABLE ic_v2.fact   TO ingest_writer;
GRANT SELECT, INSERT ON TABLE ic_v2.source TO ingest_writer;

-- Revoke mutating privileges (defensa en profundidad)
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE ic_v2.fact   FROM ingest_writer;
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE ic_v2.source FROM ingest_writer;

-- Sequences (ids)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ic_v2 TO ingest_writer;

-- Default privileges for future objects created by role "postgres" in schema ic_v2
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA ic_v2
  GRANT SELECT, INSERT ON TABLES TO ingest_writer;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA ic_v2
  GRANT USAGE, SELECT ON SEQUENCES TO ingest_writer;