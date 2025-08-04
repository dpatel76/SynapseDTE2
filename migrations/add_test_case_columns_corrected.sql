-- Add new columns to cycle_report_test_cases table for data owner tracking
-- These columns link test cases to scoped non-PK attributes approved during scoping

-- Add sample and attribute references
ALTER TABLE cycle_report_test_cases 
ADD COLUMN IF NOT EXISTS sample_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS attribute_id INTEGER,
ADD COLUMN IF NOT EXISTS attribute_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS lob_id INTEGER;

-- Add data owner assignment columns
ALTER TABLE cycle_report_test_cases
ADD COLUMN IF NOT EXISTS data_owner_id INTEGER,
ADD COLUMN IF NOT EXISTS assigned_by INTEGER,
ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add submission tracking columns
ALTER TABLE cycle_report_test_cases
ADD COLUMN IF NOT EXISTS submission_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS special_instructions TEXT;

-- Add foreign key constraints
ALTER TABLE cycle_report_test_cases
ADD CONSTRAINT fk_test_case_attribute FOREIGN KEY (attribute_id) REFERENCES cycle_report_planning_attributes(id),
ADD CONSTRAINT fk_test_case_lob FOREIGN KEY (lob_id) REFERENCES line_of_business(lob_id),
ADD CONSTRAINT fk_test_case_data_owner FOREIGN KEY (data_owner_id) REFERENCES users(user_id),
ADD CONSTRAINT fk_test_case_assigned_by FOREIGN KEY (assigned_by) REFERENCES users(user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_test_case_data_owner ON cycle_report_test_cases(data_owner_id);
CREATE INDEX IF NOT EXISTS idx_test_case_attribute ON cycle_report_test_cases(attribute_id);
CREATE INDEX IF NOT EXISTS idx_test_case_lob ON cycle_report_test_cases(lob_id);
CREATE INDEX IF NOT EXISTS idx_test_case_phase_data_owner ON cycle_report_test_cases(phase_id, data_owner_id);
CREATE INDEX IF NOT EXISTS idx_test_case_sample ON cycle_report_test_cases(sample_id);

-- Query to verify which attributes should have test cases created
-- Only scoped non-PK attributes that were approved during scoping
SELECT 
    attr.id,
    attr.attribute_name,
    attr.is_primary_key,
    scope.is_in_scope,
    scope.tester_approval_status,
    scope.report_owner_approval_status
FROM cycle_report_planning_attributes attr
JOIN cycle_report_scoping_attributes scope ON scope.attribute_id = attr.id
WHERE attr.is_primary_key = false
    AND scope.is_in_scope = true
    AND scope.tester_approval_status = 'Approved'
    AND scope.report_owner_approval_status = 'Approved';