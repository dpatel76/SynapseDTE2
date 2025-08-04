-- Complete Database Redesign: Base Tables
-- Following business-oriented naming conventions

-- Drop existing tables if needed (for clean start)
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ENUMS
-- =====================================================

-- User roles
CREATE TYPE user_role_enum AS ENUM (
    'Admin',
    'Data Executive',
    'Report Owner',
    'Tester',
    'Observer',
    'Data Provider'
);

-- Report status
CREATE TYPE report_status_enum AS ENUM (
    'Active',
    'Inactive',
    'Under Review',
    'Archived'
);

-- Cycle status
CREATE TYPE cycle_status_enum AS ENUM (
    'Draft',
    'Planning',
    'In Progress',
    'Review',
    'Completed',
    'Cancelled'
);

-- Phase status
CREATE TYPE phase_status_enum AS ENUM (
    'Not Started',
    'In Progress',
    'Pending Approval',
    'Approved',
    'Rejected',
    'Completed'
);

-- Data types
CREATE TYPE data_type_enum AS ENUM (
    'Text',
    'Number',
    'Date',
    'Boolean',
    'Currency',
    'Percentage',
    'JSON'
);

-- Information security classification
CREATE TYPE security_classification_enum AS ENUM (
    'Public',
    'Internal',
    'Confidential',
    'Restricted',
    'HRCI'
);

-- =====================================================
-- BASE TABLES
-- =====================================================

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role user_role_enum NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

-- Lines of Business (LOBs)
CREATE TABLE lobs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Report Inventory (master list of all reports)
CREATE TABLE report_inventory (
    id SERIAL PRIMARY KEY,
    report_number VARCHAR(50) UNIQUE NOT NULL,
    report_name VARCHAR(255) NOT NULL,
    description TEXT,
    frequency VARCHAR(50), -- Monthly, Quarterly, Annual
    business_unit VARCHAR(100),
    regulatory_requirement BOOLEAN DEFAULT false,
    status report_status_enum DEFAULT 'Active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Test Cycles (testing periods)
CREATE TABLE test_cycles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    description TEXT,
    status cycle_status_enum DEFAULT 'Draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Cycle Reports (instances of reports for specific test cycles)
CREATE TABLE cycle_reports (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES test_cycles(id),
    report_id INTEGER NOT NULL REFERENCES report_inventory(id),
    report_owner_id INTEGER REFERENCES users(id),
    tester_id INTEGER REFERENCES users(id),
    current_phase VARCHAR(50),
    status phase_status_enum DEFAULT 'Not Started',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    UNIQUE(cycle_id, report_id)
);

-- Data Sources Configuration
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- PostgreSQL, Oracle, SQL Server, etc.
    connection_string TEXT, -- Encrypted
    schema_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    security_classification security_classification_enum DEFAULT 'Internal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Report Data Sources (many-to-many)
CREATE TABLE report_data_sources (
    report_id INTEGER NOT NULL REFERENCES report_inventory(id),
    data_source_id INTEGER NOT NULL REFERENCES data_sources(id),
    table_name VARCHAR(255),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    PRIMARY KEY (report_id, data_source_id)
);

-- Indexes for base tables
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_report_inventory_number ON report_inventory(report_number);
CREATE INDEX idx_test_cycles_dates ON test_cycles(start_date, end_date);
CREATE INDEX idx_cycle_reports_cycle ON cycle_reports(cycle_id);
CREATE INDEX idx_cycle_reports_report ON cycle_reports(report_id);
CREATE INDEX idx_cycle_reports_status ON cycle_reports(status);

-- Comments
COMMENT ON TABLE report_inventory IS 'Master list of all reports in the organization';
COMMENT ON TABLE cycle_reports IS 'Instances of reports being tested in specific test cycles';
COMMENT ON TABLE data_sources IS 'Configuration for data sources used by reports';