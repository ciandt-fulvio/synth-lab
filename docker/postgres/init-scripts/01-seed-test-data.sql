-- synth-lab Test Database Seed Script
-- This script runs automatically on PostgreSQL container first start
-- Used by the test profile to initialize test data

-- Note: Alembic migrations run first via the backend entrypoint
-- This script only seeds initial test data after tables exist

-- The script is designed to be idempotent (safe to run multiple times)

-- Example: Insert test experiments (commented out - add as needed)
-- INSERT INTO experiments (id, name, description, created_at)
-- VALUES
--     ('test-exp-001', 'Test Experiment 1', 'For E2E testing', NOW()),
--     ('test-exp-002', 'Test Experiment 2', 'For integration testing', NOW())
-- ON CONFLICT (id) DO NOTHING;

-- Log that seeding completed
DO $$
BEGIN
    RAISE NOTICE 'Test database seed script completed successfully';
END $$;
