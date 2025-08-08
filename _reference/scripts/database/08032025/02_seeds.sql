-- SynapseDTE Seed Data
-- Essential data for containerized testing
-- Date: 2025-08-03

-- Insert users
INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) VALUES
('admin@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'System', 'Administrator', 'Admin', true),
('report.owner@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Report', 'Owner', 'Report Owner', true),
('tester@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true),
('data.owner@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Data', 'Owner', 'Data Owner', true),
('data.executive@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Data', 'Executive', 'Data Executive', true);

-- Insert roles
INSERT INTO roles (role_name, description) VALUES
('Admin', 'System administrator with full access'),
('Report Owner', 'Owns and manages reports'),
('Tester', 'Performs testing activities'),
('Data Owner', 'Owns and manages data sources'),
('Data Executive', 'Executive oversight of data'),
('Viewer', 'Read-only access');

-- Insert permissions
INSERT INTO permissions (resource, action, description) VALUES
-- User permissions
('users', 'create', 'Create users'),
('users', 'read', 'Read users'),
('users', 'update', 'Update users'),
('users', 'delete', 'Delete users'),
-- Role permissions
('roles', 'create', 'Create roles'),
('roles', 'read', 'Read roles'),
('roles', 'update', 'Update roles'),
('roles', 'delete', 'Delete roles'),
-- Report permissions
('reports', 'create', 'Create reports'),
('reports', 'read', 'Read reports'),
('reports', 'update', 'Update reports'),
('reports', 'delete', 'Delete reports'),
-- Test cycle permissions
('test_cycles', 'create', 'Create test cycles'),
('test_cycles', 'read', 'Read test cycles'),
('test_cycles', 'update', 'Update test cycles'),
('test_cycles', 'delete', 'Delete test cycles'),
-- Test execution permissions
('test_execution', 'create', 'Create test execution'),
('test_execution', 'read', 'Read test execution'),
('test_execution', 'update', 'Update test execution'),
('test_execution', 'delete', 'Delete test execution'),
-- Observation permissions
('observations', 'create', 'Create observations'),
('observations', 'read', 'Read observations'),
('observations', 'update', 'Update observations'),
('observations', 'delete', 'Delete observations'),
-- Data source permissions
('data_sources', 'create', 'Create data sources'),
('data_sources', 'read', 'Read data sources'),
('data_sources', 'update', 'Update data sources'),
('data_sources', 'delete', 'Delete data sources');

-- Assign permissions to Admin role (all permissions)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, permission_id FROM permissions;

-- Assign permissions to Report Owner role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 2, permission_id FROM permissions 
WHERE (resource = 'reports') OR (resource = 'test_cycles' AND action = 'read');

-- Assign permissions to Tester role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 3, permission_id FROM permissions 
WHERE resource IN ('test_execution', 'observations', 'test_cycles', 'reports') 
  AND action IN ('read', 'create', 'update');

-- Assign permissions to Data Owner role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 4, permission_id FROM permissions 
WHERE resource IN ('data_sources', 'reports', 'test_cycles') 
  AND action IN ('read', 'create', 'update');

-- Assign permissions to Viewer role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 6, permission_id FROM permissions 
WHERE action = 'read';

-- Assign roles to users
INSERT INTO user_roles (user_id, role_id) VALUES
(1, 1), -- admin -> Admin
(2, 2), -- report_owner -> Report Owner
(3, 3), -- tester -> Tester
(4, 4), -- data_owner -> Data Owner
(5, 5); -- data_executive -> Data Executive

-- Insert LOBs
INSERT INTO lobs (lob_name, lob_code, description) VALUES
('Retail Banking', 'RB', 'Consumer banking services'),
('Corporate Banking', 'CB', 'Business and corporate services'),
('Investment Banking', 'IB', 'Investment and trading services'),
('Wealth Management', 'WM', 'Private banking and wealth services');

-- Insert reports
INSERT INTO reports (report_name, report_code, description, frequency, regulatory_framework, lob_id) VALUES
('Customer Account Report', 'CAR-001', 'Monthly customer account summary', 'Monthly', 'SOX', 1),
('Transaction Summary Report', 'TSR-001', 'Daily transaction summary', 'Daily', 'SOX', 1),
('Risk Assessment Report', 'RAR-001', 'Quarterly risk assessment', 'Quarterly', 'Basel III', 2),
('Compliance Report', 'CR-001', 'Annual compliance report', 'Annual', 'SOX', 3);

-- Insert report attributes
INSERT INTO report_attributes (report_id, attribute_name, attribute_code, data_type, is_required, description) VALUES
-- Customer Account Report attributes
(1, 'Account Number', 'ACC_NUM', 'STRING', true, 'Customer account number'),
(1, 'Account Balance', 'ACC_BAL', 'DECIMAL', true, 'Current account balance'),
(1, 'Account Status', 'ACC_STATUS', 'STRING', true, 'Active/Inactive status'),
(1, 'Last Transaction Date', 'LAST_TXN_DATE', 'DATE', false, 'Date of last transaction'),
-- Transaction Summary Report attributes
(2, 'Transaction ID', 'TXN_ID', 'STRING', true, 'Unique transaction identifier'),
(2, 'Transaction Amount', 'TXN_AMT', 'DECIMAL', true, 'Transaction amount'),
(2, 'Transaction Type', 'TXN_TYPE', 'STRING', true, 'Type of transaction'),
(2, 'Transaction Date', 'TXN_DATE', 'DATETIME', true, 'Transaction timestamp');

-- Insert test cycles
INSERT INTO test_cycles (cycle_name, cycle_year, cycle_quarter, start_date, end_date, status, created_by_id) VALUES
('Q1 2025 Testing', 2025, 1, '2025-01-01', '2025-03-31', 'planning', 1),
('Q4 2024 Testing', 2024, 4, '2024-10-01', '2024-12-31', 'completed', 1);

-- Insert workflow phases
INSERT INTO workflow_phases (phase_name, phase_order, description) VALUES
('Planning', 1, 'Initial planning phase'),
('Data Profiling', 2, 'Profile data quality and characteristics'),
('Scoping', 3, 'Determine testing scope'),
('Test Execution', 4, 'Execute test cases'),
('Observation Management', 5, 'Manage observations and findings'),
('Report Generation', 6, 'Generate final test report');

-- Insert activity definitions for Planning phase
INSERT INTO activity_definitions (phase_name, activity_name, activity_code, description, activity_type, sequence_order) VALUES
('Planning', 'Initialize Planning', 'PLAN_INIT', 'Initialize the planning phase', 'START', 1),
('Planning', 'Select Attributes', 'PLAN_ATTR', 'Select attributes for testing', 'TASK', 2),
('Planning', 'Review Planning', 'PLAN_REVIEW', 'Review planning decisions', 'REVIEW', 3),
('Planning', 'Approve Planning', 'PLAN_APPROVE', 'Approve the planning phase', 'APPROVAL', 4),
('Planning', 'Complete Planning', 'PLAN_COMPLETE', 'Mark planning as complete', 'COMPLETE', 5);