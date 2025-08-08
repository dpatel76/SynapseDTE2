-- Seed data for audit_logs
-- Generated from: audit_logs.json
-- Rows: 83

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(1, 2, 'ASSIGNMENT_CREATED', 'report_owner_assignments', 2, 'null', '{"type": "Data Upload Request", "title": "Data Upload Required - Report 999", "priority": "High", "assigned_to": 1}', '2025-06-23T01:38:07.614311+00:00', NULL, '2025-06-22T21:38:07.581928+00:00', '2025-06-22T21:38:07.581928+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(2, 2, 'ASSIGNMENT_CREATED', 'report_owner_assignments', 3, 'null', '{"type": "Data Upload Request", "title": "Data Upload Required - Report 160", "priority": "High", "assigned_to": 3}', '2025-06-23T01:38:47.907672+00:00', NULL, '2025-06-22T21:38:47.880273+00:00', '2025-06-22T21:38:47.880273+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(3, 2, 'ASSIGNMENT_CREATED', 'report_owner_assignments', 4, 'null', '{"type": "Data Upload Request", "title": "Data Upload Required - Report 160", "priority": "High", "assigned_to": 4}', '2025-06-23T01:39:24.609634+00:00', NULL, '2025-06-22T21:39:24.585439+00:00', '2025-06-22T21:39:24.585439+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(4, 3, 'ASSIGNMENT_CREATED', 'report_owner_assignments', 5, 'null', '{"type": "Data Upload Request", "title": "Data Upload Required - Report 156", "priority": "High", "assigned_to": 4}', '2025-06-23T01:59:58.821146+00:00', NULL, '2025-06-22T21:59:58.787285+00:00', '2025-06-22T21:59:58.787285+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(5, 4, 'ASSIGNMENT_COMPLETED', 'report_owner_assignments', 5, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-06-22T22:43:43.869200"}', '2025-06-23T02:43:43.869281+00:00', NULL, '2025-06-22T22:43:43.840553+00:00', '2025-06-22T22:43:43.840553+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(6, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Data Upload Request", "title": "Data Upload Required for Report 156", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "8779ce5d-1f1b-4174-986e-e9e2be07278a"}', '2025-06-23T00:10:49.645940+00:00', NULL, '2025-06-23T00:10:49.619990+00:00', '2025-06-23T00:10:49.619990+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(7, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-06-23T00:16:33.468202", "assignment_id": "8779ce5d-1f1b-4174-986e-e9e2be07278a", "completion_notes": "Data files uploaded and validated for Report 156"}', '2025-06-23T00:16:33.468250+00:00', NULL, '2025-06-23T00:16:33.440970+00:00', '2025-06-23T00:16:33.440970+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(8, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Data Profiling Rules Approval - Report 156", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "d003de1a-0587-4451-a587-9fec858cefdf"}', '2025-06-23T19:21:00.311968+00:00', NULL, '2025-06-23T19:21:00.140306+00:00', '2025-06-23T19:21:00.140306+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(9, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Data Profiling Rules Approval - Report 156", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "6f9c8c3e-313e-41c5-9965-6aa525dbeb96"}', '2025-06-23T19:21:41.550434+00:00', NULL, '2025-06-23T19:21:41.524563+00:00', '2025-06-23T19:21:41.524563+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(10, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Data Profiling Rules Approval - Report 156", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "e08391d6-46df-4f85-a6cc-8ff856f3b9c5"}', '2025-06-23T19:52:30.723897+00:00', NULL, '2025-06-23T19:52:30.696643+00:00', '2025-06-23T19:52:30.696643+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(11, 1, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Providers for FR Y-14M Schedule D.1", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "8eb28f54-37dd-45ab-aad2-a2198b6a6f36"}', '2025-06-24T12:42:07.793197+00:00', NULL, '2025-06-24T12:42:07.748119+00:00', '2025-06-24T12:42:07.748119+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(12, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Providers for FR Y-14M Schedule D.1", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "f65a9904-1b5b-4f43-bcbf-5cf587aecb6b"}', '2025-06-24T13:36:49.298842+00:00', NULL, '2025-06-24T13:36:49.266783+00:00', '2025-06-24T13:36:49.266783+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(13, 1, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Phase Review", "title": "Review Planning Phase", "to_role": "Test Manager", "priority": "High", "from_role": "Tester", "assignment_id": "864f787e-e472-4c86-a5b5-4179c09fe31c"}', '2025-06-25T12:57:04.648928+00:00', NULL, '2025-06-25T12:57:04.615037+00:00', '2025-06-25T12:57:04.615037+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(14, 2, 'UNIVERSAL_ASSIGNMENT_ACKNOWLEDGED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Acknowledged", "assignment_id": "864f787e-e472-4c86-a5b5-4179c09fe31c", "acknowledged_at": "2025-06-25T12:57:04.664496"}', '2025-06-25T12:57:04.664540+00:00', NULL, '2025-06-25T12:57:04.661297+00:00', '2025-06-25T12:57:04.661297+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(15, 2, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Acknowledged"}', '{"status": "In Progress", "started_at": "2025-06-25T12:57:04.669413", "assignment_id": "864f787e-e472-4c86-a5b5-4179c09fe31c"}', '2025-06-25T12:57:04.669449+00:00', NULL, '2025-06-25T12:57:04.668022+00:00', '2025-06-25T12:57:04.668022+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(16, 2, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-06-25T12:57:04.672897", "assignment_id": "864f787e-e472-4c86-a5b5-4179c09fe31c", "completion_notes": "Reviewed and approved all test attributes"}', '2025-06-25T12:57:04.672934+00:00', NULL, '2025-06-25T12:57:04.671632+00:00', '2025-06-25T12:57:04.671632+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(17, 1, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Scoping Approval", "title": "Review Scoping Decisions", "to_role": "Test Manager", "priority": "High", "from_role": "Tester", "assignment_id": "5a7bf187-e20a-4542-ac47-caf1db67d4be"}', '2025-06-25T12:57:04.675655+00:00', NULL, '2025-06-25T12:57:04.675197+00:00', '2025-06-25T12:57:04.675197+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(27, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Review Data Profiling Rules", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "43a58fbf-d392-4c80-a1c3-28915d55c74f"}', '2025-07-22T03:30:47.980766+00:00', NULL, '2025-07-22T03:30:47.980766+00:00', '2025-07-22T03:30:47.980766+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(23, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-17T12:36:46.930479", "assignment_id": "dfdbfb47-3102-41a0-9c8c-689931899f16", "completion_notes": "All 12 data profiling rules reviewed - 10 approved, 2 rejected"}', '2025-07-17T12:36:46.930492+00:00', NULL, '2025-07-17T12:36:46.930492+00:00', '2025-07-17T12:36:46.930492+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(24, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-17T15:39:09.315874", "assignment_id": "72418801-0df5-4670-8fb8-428fe2290ae3", "completion_notes": "Reviewed 12 data profiling rules"}', '2025-07-17T15:39:09.315973+00:00', NULL, '2025-07-17T15:39:09.315973+00:00', '2025-07-17T15:39:09.315973+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(25, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-17T21:35:48.267318", "assignment_id": "4bcbce44-b59f-4e0b-a3c9-a823697b9a26", "completion_notes": "Scoping review Declined: n"}', '2025-07-17T21:35:48.267400+00:00', NULL, '2025-07-17T21:35:48.267400+00:00', '2025-07-17T21:35:48.267400+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(26, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Scoping Approval", "title": "Scoping Approval Required - FR Y-14M Schedule D.1", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "380a1d52-f5d3-4657-a492-7caeef8551f8"}', '2025-07-18T05:13:38.200779+00:00', NULL, '2025-07-18T05:13:38.200779+00:00', '2025-07-18T05:13:38.200779+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(28, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-22T12:44:58.859770", "assignment_id": "43a58fbf-d392-4c80-a1c3-28915d55c74f", "completion_notes": "Reviewed 21 data profiling rules"}', '2025-07-22T12:44:58.859901+00:00', NULL, '2025-07-22T12:44:58.859901+00:00', '2025-07-22T12:44:58.859901+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(29, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Review Updated Data Profiling Rules", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "4879955d-246e-4576-b667-9f7c560ba9dd"}', '2025-07-22T14:45:59.012024+00:00', NULL, '2025-07-22T14:45:59.012024+00:00', '2025-07-22T14:45:59.012024+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(30, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-22T14:46:51.616798", "assignment_id": "4879955d-246e-4576-b667-9f7c560ba9dd", "completion_notes": "Reviewed 20 data profiling rules"}', '2025-07-22T14:46:51.616907+00:00', NULL, '2025-07-22T14:46:51.616907+00:00', '2025-07-22T14:46:51.616907+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(31, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Scoping Approval", "title": "Review Updated Scoping Decisions", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "0c45a913-4f34-4dc5-a9c5-acc47c0acd12"}', '2025-07-24T04:11:57.653825+00:00', NULL, '2025-07-24T04:11:57.653825+00:00', '2025-07-24T04:11:57.653825+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(32, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-24T04:29:50.510984", "assignment_id": "0c45a913-4f34-4dc5-a9c5-acc47c0acd12", "completion_notes": "Scoping version approved: Version approved via API"}', '2025-07-24T04:29:50.511044+00:00', NULL, '2025-07-24T04:29:50.511044+00:00', '2025-07-24T04:29:50.511044+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(33, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-25T05:14:14.442616", "assignment_id": "0dfdb205-f184-404d-aacd-4d51e8813036", "completion_notes": "Make Changes"}', '2025-07-25T05:14:14.442748+00:00', NULL, '2025-07-25T05:14:14.442748+00:00', '2025-07-25T05:14:14.442748+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(34, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-25T19:26:45.391909", "assignment_id": "a0353200-428e-42ab-90c9-1c21d229eeea", "completion_notes": "Make changes to samples"}', '2025-07-25T19:26:45.392037+00:00', NULL, '2025-07-25T19:26:45.392037+00:00', '2025-07-25T19:26:45.392037+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(35, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Sample Selection Approval", "title": "Review Sample Selection", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "ea57e290-f945-44d8-94e5-d01ff92d5f58"}', '2025-07-25T21:08:32.675126+00:00', NULL, '2025-07-25T21:08:32.675126+00:00', '2025-07-25T21:08:32.675126+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(36, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners for FR Y-14M Schedule D.1", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "4dc0541e-7a3b-4d4f-bc72-f476b3766754"}', '2025-07-27T03:03:07.441618+00:00', NULL, '2025-07-27T03:03:07.441618+00:00', '2025-07-27T03:03:07.441618+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(37, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners for FR Y-14M Schedule D.1", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "d7a4aa6e-7b25-4b49-ab45-072af4b8db72"}', '2025-07-27T03:27:39.403575+00:00', NULL, '2025-07-27T03:27:39.403575+00:00', '2025-07-27T03:27:39.403575+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(38, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners for FR Y-14M Schedule D.1", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "08621700-5ef3-4d34-bbf8-63265aab7e68"}', '2025-07-27T03:28:01.204253+00:00', NULL, '2025-07-27T03:28:01.204253+00:00', '2025-07-27T03:28:01.204253+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(39, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners for FR Y-14M Schedule D.1", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "b050a2a6-b4bc-4f0b-a1f2-648fcab028f9"}', '2025-07-27T03:30:07.640599+00:00', NULL, '2025-07-27T03:30:07.640599+00:00', '2025-07-27T03:30:07.640599+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(40, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners for FR Y-14M Schedule D.1", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "c15f22c4-6de4-4d29-bb9e-9978632f8cf8"}', '2025-07-27T03:35:16.719880+00:00', NULL, '2025-07-27T03:35:16.719880+00:00', '2025-07-27T03:35:16.719880+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(41, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Review Data Profiling Rules", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "2bb69c03-e3ae-4b22-aa59-d4df2c2c5481"}', '2025-07-27T19:06:54.045510+00:00', NULL, '2025-07-27T19:06:54.045510+00:00', '2025-07-27T19:06:54.045510+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(42, 246, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Phase Review", "title": "Test Assignment with Names", "to_role": "Report Owner", "priority": "Medium", "from_role": "Tester", "assignment_id": "1dde8b08-ed39-4a7d-b4ff-dbbb13b2a4b9"}', '2025-07-27T19:47:10.865511+00:00', NULL, '2025-07-27T19:47:10.865511+00:00', '2025-07-27T19:47:10.865511+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(43, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-27T20:02:45.389328", "assignment_id": "2bb69c03-e3ae-4b22-aa59-d4df2c2c5481", "completion_notes": "Reviewed 24 data profiling rules"}', '2025-07-27T20:02:45.389426+00:00', NULL, '2025-07-27T20:02:45.389426+00:00', '2025-07-27T20:02:45.389426+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(44, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Review Updated Data Profiling Rules", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "f16deb5f-f0e9-4f34-8f26-ec83eb60077e"}', '2025-07-27T20:09:41.260411+00:00', NULL, '2025-07-27T20:09:41.260411+00:00', '2025-07-27T20:09:41.260411+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(45, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Review Data Profiling Rules", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "f69e92b0-24ad-4a43-8bd1-97d44e03ed66"}', '2025-07-27T20:24:43.832982+00:00', NULL, '2025-07-27T20:24:43.832982+00:00', '2025-07-27T20:24:43.832982+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(46, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-27T20:25:37.624251", "assignment_id": "f69e92b0-24ad-4a43-8bd1-97d44e03ed66", "completion_notes": "Reviewed 21 data profiling rules"}', '2025-07-27T20:25:37.624337+00:00', NULL, '2025-07-27T20:25:37.624337+00:00', '2025-07-27T20:25:37.624337+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(47, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Review Updated Data Profiling Rules", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "202d35b8-93a7-4bba-9c10-81e333c15ef0"}', '2025-07-27T20:33:30.053035+00:00', NULL, '2025-07-27T20:33:30.053035+00:00', '2025-07-27T20:33:30.053035+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(48, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Rule Approval", "title": "Review Data Profiling Rules", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "4084e61f-5e43-46b6-acdd-e8d26ffad9c4"}', '2025-07-27T20:33:46.335691+00:00', NULL, '2025-07-27T20:33:46.335691+00:00', '2025-07-27T20:33:46.335691+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(49, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-27T20:48:49.333029", "assignment_id": "4084e61f-5e43-46b6-acdd-e8d26ffad9c4", "completion_notes": "Approved version - all decisions aligned"}', '2025-07-27T20:48:49.333111+00:00', NULL, '2025-07-27T20:48:49.333111+00:00', '2025-07-27T20:48:49.333111+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(50, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "Scoping Approval", "title": "Review Updated Scoping Decisions", "to_role": "Report Owner", "priority": "High", "from_role": "Tester", "assignment_id": "d1c4d791-cb5a-4461-9772-9b69f4136419"}', '2025-07-28T17:53:40.394651+00:00', NULL, '2025-07-28T17:53:40.394651+00:00', '2025-07-28T17:53:40.394651+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(51, 4, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Completed", "completed_at": "2025-07-28T17:56:35.356480", "assignment_id": "6d311836-fdbf-4626-b88d-d4034945678b", "completion_notes": "Scoping version approved: Approved"}', '2025-07-28T17:56:35.356533+00:00', NULL, '2025-07-28T17:56:35.356533+00:00', '2025-07-28T17:56:35.356533+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(52, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "b88bf197-b96e-4d97-903a-ad74aebf30b3"}', '2025-07-29T11:57:44.250791+00:00', NULL, '2025-07-29T11:57:44.250791+00:00', '2025-07-29T11:57:44.250791+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(53, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "401b63bd-730f-4986-a629-24c94b2d48e9"}', '2025-07-29T11:58:48.132375+00:00', NULL, '2025-07-29T11:58:48.132375+00:00', '2025-07-29T11:58:48.132375+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(54, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "a86d3e3a-fa7a-442f-92d9-0fff7c1666c3"}', '2025-07-29T12:33:55.983887+00:00', NULL, '2025-07-29T12:33:55.983887+00:00', '2025-07-29T12:33:55.983887+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(55, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "a85d268a-c6d1-4761-8882-0fef473a6411"}', '2025-07-29T12:59:41.473603+00:00', NULL, '2025-07-29T12:59:41.473603+00:00', '2025-07-29T12:59:41.473603+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(56, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "6f2b6178-cc16-4a55-9deb-cec36375185c"}', '2025-07-29T13:00:52.258289+00:00', NULL, '2025-07-29T13:00:52.258289+00:00', '2025-07-29T13:00:52.258289+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(57, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "a0078759-70b4-4b4f-8996-8a66d51586d2"}', '2025-07-29T13:01:52.052626+00:00', NULL, '2025-07-29T13:01:52.052626+00:00', '2025-07-29T13:01:52.052626+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(58, 5, 'UNIVERSAL_ASSIGNMENT_ACKNOWLEDGED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Acknowledged", "assignment_id": "a0078759-70b4-4b4f-8996-8a66d51586d2", "acknowledged_at": "2025-07-29T13:01:52.570593"}', '2025-07-29T13:01:52.570644+00:00', NULL, '2025-07-29T13:01:52.570644+00:00', '2025-07-29T13:01:52.570644+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(59, 5, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Acknowledged"}', '{"status": "In Progress", "started_at": "2025-07-29T13:01:52.643661", "assignment_id": "a0078759-70b4-4b4f-8996-8a66d51586d2"}', '2025-07-29T13:01:52.643710+00:00', NULL, '2025-07-29T13:01:52.643710+00:00', '2025-07-29T13:01:52.643710+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(60, 5, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T13:01:52.690471", "assignment_id": "a0078759-70b4-4b4f-8996-8a66d51586d2", "completion_notes": null}', '2025-07-29T13:01:52.690522+00:00', NULL, '2025-07-29T13:01:52.690522+00:00', '2025-07-29T13:01:52.690522+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(61, 6, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "In Progress", "started_at": "2025-07-29T13:01:58.059025", "assignment_id": "496acbd6-5022-445c-8153-a909d2d84e60"}', '2025-07-29T13:01:58.059100+00:00', NULL, '2025-07-29T13:01:58.059100+00:00', '2025-07-29T13:01:58.059100+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(62, 6, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T13:01:58.100206", "assignment_id": "496acbd6-5022-445c-8153-a909d2d84e60", "completion_notes": null}', '2025-07-29T13:01:58.100248+00:00', NULL, '2025-07-29T13:01:58.100248+00:00', '2025-07-29T13:01:58.100248+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(63, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "488647b3-5eec-45ac-9795-0f7070103ec2"}', '2025-07-29T13:03:53.746536+00:00', NULL, '2025-07-29T13:03:53.746536+00:00', '2025-07-29T13:03:53.746536+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(64, 5, 'UNIVERSAL_ASSIGNMENT_ACKNOWLEDGED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Acknowledged", "assignment_id": "488647b3-5eec-45ac-9795-0f7070103ec2", "acknowledged_at": "2025-07-29T13:03:54.151530"}', '2025-07-29T13:03:54.151575+00:00', NULL, '2025-07-29T13:03:54.151575+00:00', '2025-07-29T13:03:54.151575+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(65, 5, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Acknowledged"}', '{"status": "In Progress", "started_at": "2025-07-29T13:03:54.198413", "assignment_id": "488647b3-5eec-45ac-9795-0f7070103ec2"}', '2025-07-29T13:03:54.198458+00:00', NULL, '2025-07-29T13:03:54.198458+00:00', '2025-07-29T13:03:54.198458+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(66, 5, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T13:03:54.245017", "assignment_id": "488647b3-5eec-45ac-9795-0f7070103ec2", "completion_notes": null}', '2025-07-29T13:03:54.245078+00:00', NULL, '2025-07-29T13:03:54.245078+00:00', '2025-07-29T13:03:54.245078+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(67, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "8a0b5822-977e-4ed8-8ec4-94690e814835"}', '2025-07-29T13:09:49.535287+00:00', NULL, '2025-07-29T13:09:49.535287+00:00', '2025-07-29T13:09:49.535287+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(68, 5, 'UNIVERSAL_ASSIGNMENT_ACKNOWLEDGED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Acknowledged", "assignment_id": "8a0b5822-977e-4ed8-8ec4-94690e814835", "acknowledged_at": "2025-07-29T13:09:49.959514"}', '2025-07-29T13:09:49.959561+00:00', NULL, '2025-07-29T13:09:49.959561+00:00', '2025-07-29T13:09:49.959561+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(69, 5, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Acknowledged"}', '{"status": "In Progress", "started_at": "2025-07-29T13:09:50.010765", "assignment_id": "8a0b5822-977e-4ed8-8ec4-94690e814835"}', '2025-07-29T13:09:50.010815+00:00', NULL, '2025-07-29T13:09:50.010815+00:00', '2025-07-29T13:09:50.010815+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(70, 5, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T13:09:50.060306", "assignment_id": "8a0b5822-977e-4ed8-8ec4-94690e814835", "completion_notes": null}', '2025-07-29T13:09:50.060362+00:00', NULL, '2025-07-29T13:09:50.060362+00:00', '2025-07-29T13:09:50.060362+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(71, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "eb828328-ad7d-4e96-a230-eca7fb3527d8"}', '2025-07-29T13:17:08.856114+00:00', NULL, '2025-07-29T13:17:08.856114+00:00', '2025-07-29T13:17:08.856114+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(72, 5, 'UNIVERSAL_ASSIGNMENT_ACKNOWLEDGED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Acknowledged", "assignment_id": "eb828328-ad7d-4e96-a230-eca7fb3527d8", "acknowledged_at": "2025-07-29T13:17:09.254651"}', '2025-07-29T13:17:09.254698+00:00', NULL, '2025-07-29T13:17:09.254698+00:00', '2025-07-29T13:17:09.254698+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(73, 5, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Acknowledged"}', '{"status": "In Progress", "started_at": "2025-07-29T13:17:09.299286", "assignment_id": "eb828328-ad7d-4e96-a230-eca7fb3527d8"}', '2025-07-29T13:17:09.299328+00:00', NULL, '2025-07-29T13:17:09.299328+00:00', '2025-07-29T13:17:09.299328+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(74, 5, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T13:17:09.345777", "assignment_id": "eb828328-ad7d-4e96-a230-eca7fb3527d8", "completion_notes": null}', '2025-07-29T13:17:09.345829+00:00', NULL, '2025-07-29T13:17:09.345829+00:00', '2025-07-29T13:17:09.345829+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(75, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "3bb3ced4-afeb-40e4-a812-7a034f7899c8"}', '2025-07-29T13:20:07.954240+00:00', NULL, '2025-07-29T13:20:07.954240+00:00', '2025-07-29T13:20:07.954240+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(76, 5, 'UNIVERSAL_ASSIGNMENT_ACKNOWLEDGED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "Acknowledged", "assignment_id": "3bb3ced4-afeb-40e4-a812-7a034f7899c8", "acknowledged_at": "2025-07-29T13:20:08.347535"}', '2025-07-29T13:20:08.347581+00:00', NULL, '2025-07-29T13:20:08.347581+00:00', '2025-07-29T13:20:08.347581+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(77, 5, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Acknowledged"}', '{"status": "In Progress", "started_at": "2025-07-29T13:20:08.389804", "assignment_id": "3bb3ced4-afeb-40e4-a812-7a034f7899c8"}', '2025-07-29T13:20:08.389845+00:00', NULL, '2025-07-29T13:20:08.389845+00:00', '2025-07-29T13:20:08.389845+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(78, 5, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T13:20:08.431713", "assignment_id": "3bb3ced4-afeb-40e4-a812-7a034f7899c8", "completion_notes": null}', '2025-07-29T13:20:08.431758+00:00', NULL, '2025-07-29T13:20:08.431758+00:00', '2025-07-29T13:20:08.431758+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(79, 6, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Completed"}', '{"status": "Completed", "started_at": "2025-07-29T17:01:58.059025+00:00", "assignment_id": "496acbd6-5022-445c-8153-a909d2d84e60"}', '2025-07-29T13:20:10.829463+00:00', NULL, '2025-07-29T13:20:10.829463+00:00', '2025-07-29T13:20:10.829463+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(80, 6, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Completed"}', '{"status": "Completed", "completed_at": "2025-07-29T13:20:10.859439", "assignment_id": "496acbd6-5022-445c-8153-a909d2d84e60", "completion_notes": null}', '2025-07-29T13:20:10.859483+00:00', NULL, '2025-07-29T13:20:10.859483+00:00', '2025-07-29T13:20:10.859483+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(81, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "692e2caa-0876-49a5-ab3c-2c5a51380acb"}', '2025-07-29T13:36:02.826914+00:00', NULL, '2025-07-29T13:36:02.826914+00:00', '2025-07-29T13:36:02.826914+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(82, 3, 'UNIVERSAL_ASSIGNMENT_CREATED', 'universal_assignments', NULL, 'null', '{"type": "LOB Assignment", "title": "Assign Data Owners - GBM", "to_role": "Data Executive", "priority": "High", "from_role": "Tester", "assignment_id": "3e2b1bca-ac27-4968-9f19-c369662186dd"}', '2025-07-29T13:54:17.300491+00:00', NULL, '2025-07-29T13:54:17.300491+00:00', '2025-07-29T13:54:17.300491+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(83, 6, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "In Progress", "started_at": "2025-07-29T20:27:31.695362", "assignment_id": "53f60b00-f76b-4551-8bae-2fc8b266f32f"}', '2025-07-29T20:27:31.695426+00:00', NULL, '2025-07-29T20:27:31.695426+00:00', '2025-07-29T20:27:31.695426+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(84, 6, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T20:27:31.746278", "assignment_id": "53f60b00-f76b-4551-8bae-2fc8b266f32f", "completion_notes": null}', '2025-07-29T20:27:31.746334+00:00', NULL, '2025-07-29T20:27:31.746334+00:00', '2025-07-29T20:27:31.746334+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(85, 6, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Assigned"}', '{"status": "In Progress", "started_at": "2025-07-29T20:27:31.793837", "assignment_id": "10173f50-d2de-4d67-bb46-9dbb2d58e78a"}', '2025-07-29T20:27:31.793891+00:00', NULL, '2025-07-29T20:27:31.793891+00:00', '2025-07-29T20:27:31.793891+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(86, 6, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "In Progress"}', '{"status": "Completed", "completed_at": "2025-07-29T20:27:31.836569", "assignment_id": "10173f50-d2de-4d67-bb46-9dbb2d58e78a", "completion_notes": null}', '2025-07-29T20:27:31.836634+00:00', NULL, '2025-07-29T20:27:31.836634+00:00', '2025-07-29T20:27:31.836634+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(87, 6, 'UNIVERSAL_ASSIGNMENT_STARTED', 'universal_assignments', NULL, '{"status": "Completed"}', '{"status": "Completed", "started_at": "2025-07-29T17:01:58.059025+00:00", "assignment_id": "496acbd6-5022-445c-8153-a909d2d84e60"}', '2025-07-29T20:27:31.886645+00:00', NULL, '2025-07-29T20:27:31.886645+00:00', '2025-07-29T20:27:31.886645+00:00');

INSERT INTO audit_logs (audit_id, user_id, action, table_name, record_id, old_values, new_values, timestamp, session_id, created_at, updated_at) VALUES
(88, 6, 'UNIVERSAL_ASSIGNMENT_COMPLETED', 'universal_assignments', NULL, '{"status": "Completed"}', '{"status": "Completed", "completed_at": "2025-07-29T20:27:31.937615", "assignment_id": "496acbd6-5022-445c-8153-a909d2d84e60", "completion_notes": null}', '2025-07-29T20:27:31.937692+00:00', NULL, '2025-07-29T20:27:31.937692+00:00', '2025-07-29T20:27:31.937692+00:00');

