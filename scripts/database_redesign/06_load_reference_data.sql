-- Load reference data for the redesigned database

-- =====================================================
-- WORKFLOW CONFIGURATION
-- =====================================================

INSERT INTO workflow_configuration (phase_name, phase_order, required_role, approval_required, approver_role, sla_days) VALUES
('Planning', 1, 'Report Owner', true, 'Data Executive', 5),
('Data Profiling', 2, 'Tester', false, NULL, 3),
('Scoping', 3, 'Tester', true, 'Report Owner', 3),
('Sample Selection', 4, 'Tester', true, 'Report Owner', 2),
('Data Owner Identification', 5, 'Report Owner', false, NULL, 5),
('Source Evidence', 6, 'Data Provider', false, NULL, 7),
('Test Execution', 7, 'Tester', false, NULL, 10),
('Observations', 8, 'Tester', true, 'Report Owner', 5),
('Final Report', 9, 'Report Owner', true, 'Data Executive', 3);

-- =====================================================
-- PERMISSIONS
-- =====================================================

-- Admin permissions
INSERT INTO permissions (permission_code, permission_name, resource_type, action) VALUES
('admin.users.view', 'View all users', 'user', 'view'),
('admin.users.create', 'Create users', 'user', 'create'),
('admin.users.update', 'Update users', 'user', 'update'),
('admin.users.delete', 'Delete users', 'user', 'delete'),
('admin.reports.manage', 'Manage report inventory', 'report', 'manage'),
('admin.cycles.manage', 'Manage test cycles', 'cycle', 'manage'),
('admin.config.manage', 'Manage system configuration', 'system', 'manage');

-- Data Executive permissions
INSERT INTO permissions (permission_code, permission_name, resource_type, action) VALUES
('exec.reports.view', 'View all reports', 'report', 'view'),
('exec.cycles.view', 'View all cycles', 'cycle', 'view'),
('exec.planning.approve', 'Approve planning phase', 'planning', 'approve'),
('exec.report.approve', 'Approve final reports', 'report', 'approve'),
('exec.dashboard.view', 'View executive dashboard', 'dashboard', 'view');

-- Report Owner permissions
INSERT INTO permissions (permission_code, permission_name, resource_type, action) VALUES
('owner.reports.view', 'View assigned reports', 'report', 'view'),
('owner.planning.create', 'Create planning attributes', 'planning', 'create'),
('owner.planning.update', 'Update planning attributes', 'planning', 'update'),
('owner.scoping.approve', 'Approve scoping decisions', 'scoping', 'approve'),
('owner.samples.approve', 'Approve sample selection', 'samples', 'approve'),
('owner.observations.review', 'Review observations', 'observations', 'review'),
('owner.dataowner.assign', 'Assign data owners', 'dataowner', 'assign');

-- Tester permissions
INSERT INTO permissions (permission_code, permission_name, resource_type, action) VALUES
('tester.reports.view', 'View assigned reports', 'report', 'view'),
('tester.profiling.execute', 'Execute data profiling', 'profiling', 'execute'),
('tester.scoping.create', 'Create scoping decisions', 'scoping', 'create'),
('tester.samples.select', 'Select test samples', 'samples', 'create'),
('tester.tests.execute', 'Execute tests', 'tests', 'execute'),
('tester.observations.create', 'Create observations', 'observations', 'create');

-- Observer permissions
INSERT INTO permissions (permission_code, permission_name, resource_type, action) VALUES
('observer.reports.view', 'View reports (read-only)', 'report', 'view'),
('observer.cycles.view', 'View cycles (read-only)', 'cycle', 'view'),
('observer.dashboard.view', 'View dashboards', 'dashboard', 'view');

-- Data Provider permissions
INSERT INTO permissions (permission_code, permission_name, resource_type, action) VALUES
('provider.assignments.view', 'View data assignments', 'assignment', 'view'),
('provider.evidence.submit', 'Submit evidence', 'evidence', 'create'),
('provider.documents.upload', 'Upload documents', 'document', 'create');

-- =====================================================
-- ROLE PERMISSIONS MAPPING
-- =====================================================

-- Admin gets all permissions
INSERT INTO role_permissions (role, permission_id)
SELECT 'Admin', id FROM permissions;

-- Data Executive permissions
INSERT INTO role_permissions (role, permission_id)
SELECT 'Data Executive', id FROM permissions 
WHERE permission_code LIKE 'exec.%' OR permission_code LIKE 'observer.%';

-- Report Owner permissions
INSERT INTO role_permissions (role, permission_id)
SELECT 'Report Owner', id FROM permissions 
WHERE permission_code LIKE 'owner.%' OR permission_code LIKE 'observer.%';

-- Tester permissions
INSERT INTO role_permissions (role, permission_id)
SELECT 'Tester', id FROM permissions 
WHERE permission_code LIKE 'tester.%' OR permission_code IN ('observer.reports.view', 'observer.cycles.view');

-- Observer permissions
INSERT INTO role_permissions (role, permission_id)
SELECT 'Observer', id FROM permissions 
WHERE permission_code LIKE 'observer.%';

-- Data Provider permissions
INSERT INTO role_permissions (role, permission_id)
SELECT 'Data Provider', id FROM permissions 
WHERE permission_code LIKE 'provider.%';

-- =====================================================
-- TEST TEMPLATES
-- =====================================================

INSERT INTO test_templates (template_name, template_type, test_query, expected_result_pattern) VALUES
('Completeness Check', 'Completeness', 'SELECT COUNT(*) FROM {table} WHERE {column} IS NULL', 'Count should be 0'),
('Date Range Validation', 'Validity', 'SELECT COUNT(*) FROM {table} WHERE {date_column} NOT BETWEEN :start_date AND :end_date', 'Count should be 0'),
('Duplicate Check', 'Uniqueness', 'SELECT {column}, COUNT(*) FROM {table} GROUP BY {column} HAVING COUNT(*) > 1', 'No rows should be returned'),
('Referential Integrity', 'Consistency', 'SELECT COUNT(*) FROM {child_table} WHERE {fk_column} NOT IN (SELECT {pk_column} FROM {parent_table})', 'Count should be 0'),
('Format Validation', 'Validity', 'SELECT COUNT(*) FROM {table} WHERE NOT REGEXP_LIKE({column}, :pattern)', 'Count should be 0');

-- =====================================================
-- SAMPLE REGULATORY REQUIREMENTS
-- =====================================================

INSERT INTO regulatory_requirements (code, name, description, effective_date) VALUES
('SOX', 'Sarbanes-Oxley Act', 'Financial reporting and internal controls', '2002-07-30'),
('GDPR', 'General Data Protection Regulation', 'EU data protection and privacy', '2018-05-25'),
('CCPA', 'California Consumer Privacy Act', 'California consumer data privacy', '2020-01-01'),
('HIPAA', 'Health Insurance Portability and Accountability Act', 'Healthcare data privacy', '1996-08-21'),
('PCI-DSS', 'Payment Card Industry Data Security Standard', 'Credit card data security', '2006-09-07');

-- =====================================================
-- SAMPLE LOBS
-- =====================================================

INSERT INTO lobs (name, description) VALUES
('Retail Banking', 'Consumer banking products and services'),
('Commercial Banking', 'Business banking and lending'),
('Wealth Management', 'Investment and advisory services'),
('Insurance', 'Life and property insurance products'),
('Capital Markets', 'Trading and investment banking'),
('Technology', 'IT and digital services'),
('Operations', 'Back-office and support functions'),
('Risk Management', 'Risk assessment and compliance'),
('Human Resources', 'Employee management and benefits'),
('Finance', 'Financial planning and accounting');

\echo 'Reference data loaded successfully!'