-- Seed data for workflow_activity_dependencies
-- Generated from: workflow_activity_dependencies.json
-- Rows: 17

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(37, 'Planning', 'Review Generated Attributes', 'Generate Attributes', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(38, 'Planning', 'Submit for Approval', 'Review Generated Attributes', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(39, 'Planning', 'Report Owner Approval', 'Submit for Approval', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(40, 'Planning', 'Complete Planning Phase', 'Report Owner Approval', 'approval', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(41, 'Scoping', 'Review Scoping Results', 'Execute Scoping', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(42, 'Scoping', 'Scoping Approval', 'Review Scoping Results', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(43, 'Scoping', 'Complete Scoping Phase', 'Scoping Approval', 'approval', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(44, 'Sample Selection', 'Review and Tag Samples', 'Generate Samples', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(45, 'Sample Selection', 'Complete Sample Selection', 'Review and Tag Samples', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(46, 'Request for Information', 'Upload Data', 'Send Data Request', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(47, 'Request for Information', 'Validate Data Upload', 'Upload Data', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(48, 'Request for Information', 'Generate Test Cases', 'Validate Data Upload', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(49, 'Test Execution', 'Review Test Results', 'Execute Tests', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(50, 'Test Execution', 'Document Test Evidence', 'Execute Tests', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(51, 'Observation Management', 'Review Observations', 'Create Observations', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(52, 'Observation Management', 'Data Owner Response', 'Review Observations', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

INSERT INTO workflow_activity_dependencies (dependency_id, phase_name, activity_name, depends_on_activity, dependency_type, is_active, created_at, created_by_id, updated_by_id) VALUES
(53, 'Observation Management', 'Finalize Observations', 'Data Owner Response', 'completion', TRUE, '2025-07-11T12:54:50.823319+00:00', NULL, NULL);

