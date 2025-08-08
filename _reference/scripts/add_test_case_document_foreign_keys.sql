-- Add foreign key constraints for test case document submissions

-- Add test_case_id foreign key
ALTER TABLE cycle_report_test_case_document_submissions
ADD CONSTRAINT fk_test_case_id 
    FOREIGN KEY (test_case_id) REFERENCES cycle_report_test_cases(id);

-- Add data_provider_id foreign key
ALTER TABLE cycle_report_test_case_document_submissions
ADD CONSTRAINT fk_data_provider_id 
    FOREIGN KEY (data_provider_id) REFERENCES users(user_id);

-- Add parent_submission_id foreign key
ALTER TABLE cycle_report_test_case_document_submissions
ADD CONSTRAINT fk_parent_submission_id 
    FOREIGN KEY (parent_submission_id) REFERENCES cycle_report_test_case_document_submissions(submission_id);

-- Add validated_by foreign key
ALTER TABLE cycle_report_test_case_document_submissions
ADD CONSTRAINT fk_validated_by 
    FOREIGN KEY (validated_by) REFERENCES users(user_id);

-- Show all constraints on the table
SELECT conname AS constraint_name, 
       contype AS constraint_type,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint 
WHERE conrelid = 'cycle_report_test_case_document_submissions'::regclass;