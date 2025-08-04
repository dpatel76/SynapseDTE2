-- Drop the incorrect foreign key constraint
ALTER TABLE cycle_report_test_execution_results 
DROP CONSTRAINT IF EXISTS cycle_report_test_execution_results_evidence_id_fkey;

-- Add the correct foreign key constraint pointing to cycle_report_test_cases_evidence
ALTER TABLE cycle_report_test_execution_results 
ADD CONSTRAINT cycle_report_test_execution_results_evidence_id_fkey 
FOREIGN KEY (evidence_id) 
REFERENCES cycle_report_test_cases_evidence(id);