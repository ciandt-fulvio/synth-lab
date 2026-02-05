-- SQL initialization script for mechanism tables
-- Feature: 039-narrative-mechanism-config
--
-- This script creates the tables for mechanism definitions, options, and feature types.
-- Run this BEFORE seed_mechanisms.py
--
-- Usage:
--   psql $DATABASE_URL -f scripts/init_mechanism_tables.sql

-- ============================================================================
-- Table: mechanism_definitions
-- ============================================================================

CREATE TABLE IF NOT EXISTS mechanism_definitions (
    id UUID PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    label_pt VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mechanism_definitions_key ON mechanism_definitions(key);

COMMENT ON TABLE mechanism_definitions IS 'Defines mechanisms (e.g., irreversibility, network_effect) for feature configuration';
COMMENT ON COLUMN mechanism_definitions.key IS 'Programmatic key (lowercase with underscores)';
COMMENT ON COLUMN mechanism_definitions.label_pt IS 'Portuguese display label';
COMMENT ON COLUMN mechanism_definitions.description IS 'Explanation of what this mechanism measures';

-- ============================================================================
-- Table: mechanism_options
-- ============================================================================

CREATE TABLE IF NOT EXISTS mechanism_options (
    id UUID PRIMARY KEY,
    mechanism_id UUID NOT NULL REFERENCES mechanism_definitions(id) ON DELETE CASCADE,
    label VARCHAR(100) NOT NULL,
    value NUMERIC(3,2) NOT NULL CHECK (value >= 0 AND value <= 1),
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mechanism_options_mechanism_id ON mechanism_options(mechanism_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mechanism_options_order ON mechanism_options(mechanism_id, display_order);

COMMENT ON TABLE mechanism_options IS 'Text options for each mechanism with mapped numeric values';
COMMENT ON COLUMN mechanism_options.label IS 'Display text for the option (e.g., "totalmente reversível")';
COMMENT ON COLUMN mechanism_options.value IS 'Numeric value mapped to this option [0.0, 1.0]';
COMMENT ON COLUMN mechanism_options.display_order IS 'Order in dropdown (ascending)';

-- ============================================================================
-- Table: feature_types
-- ============================================================================

CREATE TABLE IF NOT EXISTS feature_types (
    id UUID PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    label_pt VARCHAR(100) NOT NULL,
    description TEXT,
    amplifies_mechanisms JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_feature_types_key ON feature_types(key);

COMMENT ON TABLE feature_types IS 'Feature categories that amplify certain mechanisms';
COMMENT ON COLUMN feature_types.amplifies_mechanisms IS 'JSON array of mechanism keys this type amplifies';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Mechanism tables created successfully:';
    RAISE NOTICE '  - mechanism_definitions';
    RAISE NOTICE '  - mechanism_options';
    RAISE NOTICE '  - feature_types';
END
$$;
