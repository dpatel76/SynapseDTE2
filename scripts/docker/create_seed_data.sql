-- Basic seed data that matches current schema

-- Insert LOBs first (no foreign keys to users)
INSERT INTO lobs (lob_id, lob_name, created_at, updated_at) VALUES
(1, 'Corporate Banking', NOW(), NOW()),
(2, 'Retail Banking', NOW(), NOW()),
(3, 'Investment Banking', NOW(), NOW())
ON CONFLICT (lob_id) DO NOTHING;

-- Insert RBAC Roles (no foreign keys to users)
INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at) VALUES
(1, 'Admin', 'System Administrator - Full Access', TRUE, TRUE, NOW(), NOW()),
(2, 'Test Executive', 'Test Manager - Manage testing cycles and assignments', TRUE, TRUE, NOW(), NOW()),
(3, 'Tester', 'Tester - Execute testing workflows', TRUE, TRUE, NOW(), NOW()),
(4, 'Report Owner', 'Report Owner - Review and approve reports', TRUE, TRUE, NOW(), NOW()),
(5, 'Report Executive', 'Report Owner Executive - Executive oversight', TRUE, TRUE, NOW(), NOW()),
(6, 'Data Owner', 'Data Provider - Provide data for testing', TRUE, TRUE, NOW(), NOW()),
(7, 'Data Executive', 'Chief Data Officer - Manage LOBs and data providers', TRUE, TRUE, NOW(), NOW())
ON CONFLICT (role_id) DO NOTHING;

-- Insert RBAC Permissions
INSERT INTO rbac_permissions (permission_id, permission_name, resource, action, description, created_at, updated_at) VALUES
(1, 'users.create', 'users', 'create', 'Create new users', NOW(), NOW()),
(2, 'users.read', 'users', 'read', 'View user information', NOW(), NOW()),
(3, 'users.update', 'users', 'update', 'Update user information', NOW(), NOW()),
(4, 'users.delete', 'users', 'delete', 'Delete users', NOW(), NOW()),
(5, 'reports.create', 'reports', 'create', 'Create new reports', NOW(), NOW()),
(6, 'reports.read', 'reports', 'read', 'View reports', NOW(), NOW()),
(7, 'reports.update', 'reports', 'update', 'Update reports', NOW(), NOW()),
(8, 'reports.delete', 'reports', 'delete', 'Delete reports', NOW(), NOW()),
(9, 'cycles.create', 'cycles', 'create', 'Create test cycles', NOW(), NOW()),
(10, 'cycles.read', 'cycles', 'read', 'View test cycles', NOW(), NOW()),
(11, 'cycles.update', 'cycles', 'update', 'Update test cycles', NOW(), NOW()),
(12, 'cycles.delete', 'cycles', 'delete', 'Delete test cycles', NOW(), NOW())
ON CONFLICT (permission_id) DO NOTHING;

-- Insert test user
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES
(1, 'Test', 'User', 'tester@example.com', 'Tester', 1, TRUE, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRECJsKqRS', NOW(), NOW())
ON CONFLICT (user_id) DO NOTHING;

-- Insert another admin user
INSERT INTO users (user_id, first_name, last_name, email, role, lob_id, is_active, hashed_password, created_at, updated_at) VALUES
(2, 'Admin', 'User', 'admin@example.com', 'Admin', NULL, TRUE, '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRECJsKqRS', NOW(), NOW())
ON CONFLICT (user_id) DO NOTHING;

-- Link users to roles
INSERT INTO rbac_user_roles (user_id, role_id, assigned_at, assigned_by) VALUES
(1, 3, NOW(), 2), -- Test User has Tester role
(2, 1, NOW(), NULL) -- Admin User has Admin role
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Grant all permissions to Admin role
INSERT INTO rbac_role_permissions (role_id, permission_id) 
SELECT 1, permission_id FROM rbac_permissions
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Grant read permissions to Tester role
INSERT INTO rbac_role_permissions (role_id, permission_id) VALUES
(3, 2),  -- users.read
(3, 6),  -- reports.read
(3, 10)  -- cycles.read
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Insert test cycles (need admin user first)
INSERT INTO test_cycles (cycle_id, cycle_name, cycle_description, test_executive_id, start_date, end_date, is_active, created_at, updated_at) VALUES
(1, 'Q1 2025 Testing Cycle', 'First quarter testing cycle for 2025', 2, '2025-01-01', '2025-03-31', TRUE, NOW(), NOW()),
(2, 'Q2 2025 Testing Cycle', 'Second quarter testing cycle for 2025', 2, '2025-04-01', '2025-06-30', FALSE, NOW(), NOW())
ON CONFLICT (cycle_id) DO NOTHING;

-- Insert reports
INSERT INTO reports (report_id, report_name, report_description, country, region, created_at, updated_at) VALUES
(1, 'Annual Risk Report 2025', 'Comprehensive annual risk assessment report', 'United States', 'North America', NOW(), NOW()),
(2, 'Quarterly Compliance Report Q1 2025', 'Q1 2025 regulatory compliance report', 'United States', 'North America', NOW(), NOW())
ON CONFLICT (report_id) DO NOTHING;

-- Reset sequences
SELECT setval('lobs_lob_id_seq', (SELECT COALESCE(MAX(lob_id), 1) FROM lobs));
SELECT setval('rbac_roles_role_id_seq', (SELECT COALESCE(MAX(role_id), 1) FROM rbac_roles));
SELECT setval('rbac_permissions_permission_id_seq', (SELECT COALESCE(MAX(permission_id), 1) FROM rbac_permissions));
SELECT setval('users_user_id_seq', (SELECT COALESCE(MAX(user_id), 1) FROM users));
SELECT setval('test_cycles_cycle_id_seq', (SELECT COALESCE(MAX(cycle_id), 1) FROM test_cycles));
SELECT setval('reports_report_id_seq', (SELECT COALESCE(MAX(report_id), 1) FROM reports));