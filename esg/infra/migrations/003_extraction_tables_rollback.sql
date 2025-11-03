-- Rollback Migration 003: Extraction Tables
-- Description: Drop tables for extracted indicators and ESG scores
-- Date: 2024-01-03
-- Author: ESG Platform Team

-- Drop indexes on esg_scores table
DROP INDEX IF EXISTS idx_scores_overall;
DROP INDEX IF EXISTS idx_scores_report_year;
DROP INDEX IF EXISTS idx_scores_company_id;

-- Drop indexes on extracted_indicators table
DROP INDEX IF EXISTS idx_extracted_company_year;
DROP INDEX IF EXISTS idx_extracted_confidence;
DROP INDEX IF EXISTS idx_extracted_validation;
DROP INDEX IF EXISTS idx_extracted_report_year;
DROP INDEX IF EXISTS idx_extracted_indicator_id;
DROP INDEX IF EXISTS idx_extracted_company_id;
DROP INDEX IF EXISTS idx_extracted_object_key;

-- Drop tables in reverse order of creation (respecting foreign key dependencies)
DROP TABLE IF EXISTS esg_scores CASCADE;
DROP TABLE IF EXISTS extracted_indicators CASCADE;
