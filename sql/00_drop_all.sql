-- Drop all existing tables and types before fresh deploy
DROP SCHEMA IF EXISTS analytics CASCADE;
DO $$ DECLARE r RECORD;
BEGIN
    FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename NOT IN ('spatial_ref_sys') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    FOR r IN SELECT typname FROM pg_type WHERE typtype='e' LOOP
        EXECUTE 'DROP TYPE IF EXISTS ' || r.typname || ' CASCADE';
    END LOOP;
END $$;
DROP FUNCTION IF EXISTS update_timestamp() CASCADE;
DROP FUNCTION IF EXISTS audit_trigger_func() CASCADE;
