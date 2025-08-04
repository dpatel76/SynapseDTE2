-- Add new columns to cycle_report_test_cases table for data owner tracking

-- Add sample and attribute references
ALTER TABLE cycle_report_test_cases 
ADD COLUMN IF NOT EXISTS sample_id VARCHAR(255) NOT NULL DEFAULT 'TEMP',
ADD COLUMN IF NOT EXISTS attribute_id INTEGER,
ADD COLUMN IF NOT EXISTS attribute_name VARCHAR(255) NOT NULL DEFAULT 'TEMP',
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
ADD CONSTRAINT fk_test_case_attribute FOREIGN KEY (attribute_id) REFERENCES report_attributes(attribute_id),
ADD CONSTRAINT fk_test_case_lob FOREIGN KEY (lob_id) REFERENCES line_of_business(lob_id),
ADD CONSTRAINT fk_test_case_data_owner FOREIGN KEY (data_owner_id) REFERENCES users(user_id),
ADD CONSTRAINT fk_test_case_assigned_by FOREIGN KEY (assigned_by) REFERENCES users(user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_test_case_data_owner ON cycle_report_test_cases(data_owner_id);
CREATE INDEX IF NOT EXISTS idx_test_case_attribute ON cycle_report_test_cases(attribute_id);
CREATE INDEX IF NOT EXISTS idx_test_case_lob ON cycle_report_test_cases(lob_id);
CREATE INDEX IF NOT EXISTS idx_test_case_phase_data_owner ON cycle_report_test_cases(phase_id, data_owner_id);

-- Update existing rows to remove temporary defaults (run this after populating real data)
-- UPDATE cycle_report_test_cases SET sample_id = NULL WHERE sample_id = 'TEMP';
-- UPDATE cycle_report_test_cases SET attribute_name = NULL WHERE attribute_name = 'TEMP';