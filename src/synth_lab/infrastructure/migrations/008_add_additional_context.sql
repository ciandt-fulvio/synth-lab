-- Migration 008: Add additional_context to research_executions
-- This stores the optional context provided when starting an interview

ALTER TABLE research_executions ADD COLUMN additional_context TEXT;
