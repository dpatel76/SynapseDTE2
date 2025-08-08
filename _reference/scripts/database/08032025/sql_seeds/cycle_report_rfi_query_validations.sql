-- Seed data for cycle_report_rfi_query_validations
-- Generated from: cycle_report_rfi_query_validations.json
-- Rows: 2

INSERT INTO cycle_report_rfi_query_validations (validation_id, test_case_id, data_source_id, query_text, query_parameters, validation_status, validation_timestamp, execution_time_ms, row_count, column_names, sample_rows, error_message, has_primary_keys, has_target_attribute, missing_columns, validated_by, validation_warnings, created_at, updated_at) VALUES
('9abad1fb-af24-44af-bf9d-ede4fef702f0', 434, 'b182079f-b2ce-473d-bda0-fd08de2e2ec6', 'SELECT bank_id as "Bank ID", customer_id as "Customer ID", period_id as "Period ID", reference_number as "Reference Number", current_credit_limit as "Current Credit limit"
from public.fry14m_scheduled1_data
where
bank_id = ''5184712966'' and
customer_id = ''FNV1K1A5D71Q9QIL49'' and
period_id = ''20240127'' and 
reference_number = ''AAHL8R2OPQWWHIZMDH''', '{}', 'success', '2025-07-30T05:44:47.052243+00:00', 20, 1, '["Bank ID", "Customer ID", "Period ID", "Reference Number", "Current Credit limit"]', '[{"Bank ID": "5184712966", "Period ID": "20240127", "Customer ID": "FNV1K1A5D71Q9QIL49", "Reference Number": "AAHL8R2OPQWWHIZMDH", "Current Credit limit": 49976.19}]', NULL, TRUE, TRUE, '[]', 6, '[]', '2025-07-30T01:44:47.010102+00:00', '2025-07-30T01:44:47.010102+00:00');

INSERT INTO cycle_report_rfi_query_validations (validation_id, test_case_id, data_source_id, query_text, query_parameters, validation_status, validation_timestamp, execution_time_ms, row_count, column_names, sample_rows, error_message, has_primary_keys, has_target_attribute, missing_columns, validated_by, validation_warnings, created_at, updated_at) VALUES
('e0e3536a-e9a3-4fad-a583-cedbf702e8c1', 435, 'b182079f-b2ce-473d-bda0-fd08de2e2ec6', 'SELECT bank_id as "Bank ID", customer_id as "Customer ID", period_id as "Period ID", reference_number as "Reference Number", current_credit_limit as "Current Credit limit"
from public.fry14m_scheduled1_data
where
bank_id = ''5538581236'' and
customer_id = ''8J1GIXNFOR5BHSFVHO'' and
period_id = ''20230526'' and 
reference_number = ''6ZJZ6GFL7ERBN6HA28''', '{}', 'success', '2025-07-30T06:04:27.602609+00:00', 62, 1, '["Bank ID", "Customer ID", "Period ID", "Reference Number", "Current Credit limit"]', '[{"Bank ID": "5538581236", "Period ID": "20230526", "Customer ID": "8J1GIXNFOR5BHSFVHO", "Reference Number": "6ZJZ6GFL7ERBN6HA28", "Current Credit limit": -4935.28}]', NULL, TRUE, TRUE, '[]', 6, '[]', '2025-07-30T02:04:27.512778+00:00', '2025-07-30T02:04:27.512778+00:00');

