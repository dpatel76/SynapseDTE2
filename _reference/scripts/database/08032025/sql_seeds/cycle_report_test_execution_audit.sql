-- Seed data for cycle_report_test_execution_audit
-- Generated from: cycle_report_test_execution_audit.json
-- Rows: 49

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(56, 19, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T03:16:03.075389+00:00', NULL, NULL, NULL, '2025-08-01T03:16:03.075389+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(57, 20, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T03:23:21.536812+00:00', NULL, NULL, NULL, '2025-08-01T03:23:21.536812+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(58, 21, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T03:26:50.130890+00:00', NULL, NULL, NULL, '2025-08-01T03:26:50.130890+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(59, 22, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T03:29:19.914812+00:00', NULL, NULL, NULL, '2025-08-01T03:29:19.914812+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(60, 22, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 24}', NULL, 3, '2025-08-01T03:29:19.975340+00:00', NULL, NULL, NULL, '2025-08-01T03:29:19.975340+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(61, 23, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T03:38:30.182339+00:00', NULL, NULL, NULL, '2025-08-01T03:38:30.182339+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(62, 23, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 32}', NULL, 3, '2025-08-01T03:38:30.261300+00:00', NULL, NULL, NULL, '2025-08-01T03:38:30.261300+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(63, 23, 'reviewed', NULL, NULL, NULL, '{"overall_score": 0.0, "review_status": "approved", "requires_retest": false}', NULL, 3, '2025-08-01T03:49:19.065949+00:00', NULL, NULL, NULL, '2025-08-01T03:49:19.065949+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(64, 22, 'reviewed', NULL, NULL, NULL, '{"overall_score": 0.0, "review_status": "approved", "requires_retest": false}', NULL, 3, '2025-08-01T03:49:19.118038+00:00', NULL, NULL, NULL, '2025-08-01T03:49:19.118038+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(65, 23, 'reviewed', NULL, NULL, NULL, '{"overall_score": 0.0, "review_status": "rejected", "requires_retest": true}', NULL, 3, '2025-08-01T03:51:41.501333+00:00', NULL, NULL, NULL, '2025-08-01T03:51:41.501333+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(66, 23, 'reviewed', NULL, NULL, NULL, '{"overall_score": 1.0, "review_status": "approved", "requires_retest": false}', NULL, 3, '2025-08-01T03:53:04.855630+00:00', NULL, NULL, NULL, '2025-08-01T03:53:04.855630+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(67, 22, 'reviewed', NULL, NULL, NULL, '{"overall_score": 0.0, "review_status": "rejected", "requires_retest": true}', NULL, 3, '2025-08-01T03:54:25.379608+00:00', NULL, NULL, NULL, '2025-08-01T03:54:25.379608+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(68, 23, 'reviewed', NULL, NULL, NULL, '{"overall_score": 1.0, "review_status": "approved", "requires_retest": false}', NULL, 3, '2025-08-01T03:55:08.176665+00:00', NULL, NULL, NULL, '2025-08-01T03:55:08.176665+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(69, 27, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T04:04:50.410497+00:00', NULL, NULL, NULL, '2025-08-01T04:04:50.410497+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(70, 27, 'failed', NULL, NULL, NULL, '{"error_message": "HybridLLMService.extract_test_value_from_document() got an unexpected keyword argument ''attribute_name''"}', NULL, 3, '2025-08-01T04:04:50.459331+00:00', NULL, NULL, NULL, '2025-08-01T04:04:50.459331+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(71, 28, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T04:05:19.868841+00:00', NULL, NULL, NULL, '2025-08-01T04:05:19.868841+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(72, 28, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2417}', NULL, 3, '2025-08-01T04:05:22.329769+00:00', NULL, NULL, NULL, '2025-08-01T04:05:22.329769+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(73, 29, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T11:58:25.425168+00:00', NULL, NULL, NULL, '2025-08-01T11:58:25.425168+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(74, 29, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 1141}', NULL, 3, '2025-08-01T11:58:26.621424+00:00', NULL, NULL, NULL, '2025-08-01T11:58:26.621424+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(75, 30, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T11:58:38.574012+00:00', NULL, NULL, NULL, '2025-08-01T11:58:38.574012+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(76, 30, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 1223}', NULL, 3, '2025-08-01T11:58:39.835455+00:00', NULL, NULL, NULL, '2025-08-01T11:58:39.835455+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(77, 31, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T12:00:59.317245+00:00', NULL, NULL, NULL, '2025-08-01T12:00:59.317245+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(78, 31, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 1184}', NULL, 3, '2025-08-01T12:01:00.549862+00:00', NULL, NULL, NULL, '2025-08-01T12:01:00.549862+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(79, 32, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T12:01:36.066536+00:00', NULL, NULL, NULL, '2025-08-01T12:01:36.066536+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(80, 32, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 1393}', NULL, 3, '2025-08-01T12:01:37.502304+00:00', NULL, NULL, NULL, '2025-08-01T12:01:37.502304+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(81, 33, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T12:05:28.561447+00:00', NULL, NULL, NULL, '2025-08-01T12:05:28.561447+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(82, 33, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 1660}', NULL, 3, '2025-08-01T12:05:30.265560+00:00', NULL, NULL, NULL, '2025-08-01T12:05:30.265560+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(83, 34, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T12:06:05.976573+00:00', NULL, NULL, NULL, '2025-08-01T12:06:05.976573+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(84, 34, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 1930}', NULL, 3, '2025-08-01T12:06:07.954190+00:00', NULL, NULL, NULL, '2025-08-01T12:06:07.954190+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(85, 35, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T12:06:50.859445+00:00', NULL, NULL, NULL, '2025-08-01T12:06:50.859445+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(86, 35, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2715}', NULL, 3, '2025-08-01T12:06:53.620220+00:00', NULL, NULL, NULL, '2025-08-01T12:06:53.620220+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(87, 36, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T12:09:01.769500+00:00', NULL, NULL, NULL, '2025-08-01T12:09:01.769500+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(88, 36, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 1384}', NULL, 3, '2025-08-01T12:09:03.196732+00:00', NULL, NULL, NULL, '2025-08-01T12:09:03.196732+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(89, 37, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T12:42:35.584245+00:00', NULL, NULL, NULL, '2025-08-01T12:42:35.584245+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(90, 37, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2827}', NULL, 3, '2025-08-01T12:42:38.459969+00:00', NULL, NULL, NULL, '2025-08-01T12:42:38.459969+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(91, 38, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T13:00:28.960338+00:00', NULL, NULL, NULL, '2025-08-01T13:00:28.960338+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(92, 38, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2470}', NULL, 3, '2025-08-01T13:00:31.472867+00:00', NULL, NULL, NULL, '2025-08-01T13:00:31.472867+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(93, 39, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T13:39:47.638993+00:00', NULL, NULL, NULL, '2025-08-01T13:39:47.638993+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(94, 39, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2943}', NULL, 3, '2025-08-01T13:39:50.626687+00:00', NULL, NULL, NULL, '2025-08-01T13:39:50.626687+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(95, 40, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T13:40:02.365690+00:00', NULL, NULL, NULL, '2025-08-01T13:40:02.365690+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(96, 40, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 3135}', NULL, 3, '2025-08-01T13:40:05.550269+00:00', NULL, NULL, NULL, '2025-08-01T13:40:05.550269+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(97, 41, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T13:45:34.815058+00:00', NULL, NULL, NULL, '2025-08-01T13:45:34.815058+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(98, 41, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2479}', NULL, 3, '2025-08-01T13:45:37.334330+00:00', NULL, NULL, NULL, '2025-08-01T13:45:37.334330+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(99, 42, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T13:50:57.391447+00:00', NULL, NULL, NULL, '2025-08-01T13:50:57.391447+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(100, 42, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2332}', NULL, 3, '2025-08-01T13:50:59.762404+00:00', NULL, NULL, NULL, '2025-08-01T13:50:59.762404+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(101, 43, 'created', NULL, NULL, NULL, '{"execution_reason": "initial"}', NULL, 3, '2025-08-01T13:51:56.618520+00:00', NULL, NULL, NULL, '2025-08-01T13:51:56.618520+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(102, 43, 'completed', NULL, NULL, NULL, '{"test_result": "pending_review", "comparison_result": null, "processing_time_ms": 2353}', NULL, 3, '2025-08-01T13:51:59.015203+00:00', NULL, NULL, NULL, '2025-08-01T13:51:59.015203+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(103, 43, 'reviewed', NULL, NULL, NULL, '{"overall_score": 0.0, "review_status": "rejected", "requires_retest": true}', NULL, 3, '2025-08-01T15:33:45.062881+00:00', NULL, NULL, NULL, '2025-08-01T15:33:45.062881+00:00');

INSERT INTO cycle_report_test_execution_audit (id, execution_id, action, previous_status, new_status, change_reason, action_details, system_info, performed_by, performed_at, ip_address, user_agent, session_id, created_at) VALUES
(104, 40, 'reviewed', NULL, NULL, NULL, '{"overall_score": 0.0, "review_status": "rejected", "requires_retest": true}', NULL, 3, '2025-08-01T15:33:50.049009+00:00', NULL, NULL, NULL, '2025-08-01T15:33:50.049009+00:00');

