-- Seed data for rbac_roles
-- Generated from: rbac_roles.json
-- Rows: 7

INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at, created_by_id, updated_by_id, can_classify_pdes) VALUES
(1, 'Admin', 'System Administrator - Full Access', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00', NULL, NULL, TRUE);

INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at, created_by_id, updated_by_id, can_classify_pdes) VALUES
(3, 'Tester', 'Tester - Execute testing workflows', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00', NULL, NULL, TRUE);

INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at, created_by_id, updated_by_id, can_classify_pdes) VALUES
(4, 'Report Owner', 'Report Owner - Review and approve reports', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00', NULL, NULL, TRUE);

INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at, created_by_id, updated_by_id, can_classify_pdes) VALUES
(2, 'Test Executive', 'Test Manager - Manage testing cycles and assignments', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00', NULL, NULL, TRUE);

INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at, created_by_id, updated_by_id, can_classify_pdes) VALUES
(6, 'Data Owner', 'Data Provider - Provide data for testing', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00', NULL, NULL, TRUE);

INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at, created_by_id, updated_by_id, can_classify_pdes) VALUES
(7, 'Data Executive', 'Chief Data Officer - Manage LOBs and data providers', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00', NULL, NULL, TRUE);

INSERT INTO rbac_roles (role_id, role_name, description, is_system, is_active, created_at, updated_at, created_by_id, updated_by_id, can_classify_pdes) VALUES
(5, 'Report Executive', 'Report Owner Executive - Executive oversight', TRUE, TRUE, '2025-06-07T17:03:29.121592+00:00', '2025-06-07T17:03:29.121592+00:00', NULL, NULL, TRUE);

