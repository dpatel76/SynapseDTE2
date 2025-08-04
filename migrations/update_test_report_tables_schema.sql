-- Migration to update test report tables to match model requirements
-- This adds the missing columns for approval workflow and proper structure

-- First, let's add the missing columns to cycle_report_test_report_sections
ALTER TABLE cycle_report_test_report_sections 
  ADD COLUMN IF NOT EXISTS id SERIAL,
  ADD COLUMN IF NOT EXISTS cycle_id INTEGER REFERENCES test_cycles(cycle_id),
  ADD COLUMN IF NOT EXISTS report_id INTEGER REFERENCES reports(id),
  ADD COLUMN IF NOT EXISTS section_title VARCHAR(255),
  ADD COLUMN IF NOT EXISTS section_content JSONB,
  ADD COLUMN IF NOT EXISTS data_sources JSONB,
  ADD COLUMN IF NOT EXISTS last_generated_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS requires_refresh BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft',
  ADD COLUMN IF NOT EXISTS tester_approved BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS tester_approved_by INTEGER REFERENCES users(user_id),
  ADD COLUMN IF NOT EXISTS tester_approved_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS tester_notes TEXT,
  ADD COLUMN IF NOT EXISTS report_owner_approved BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS report_owner_approved_by INTEGER REFERENCES users(user_id),
  ADD COLUMN IF NOT EXISTS report_owner_approved_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS report_owner_notes TEXT,
  ADD COLUMN IF NOT EXISTS executive_approved BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS executive_approved_by INTEGER REFERENCES users(user_id),
  ADD COLUMN IF NOT EXISTS executive_approved_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS executive_notes TEXT,
  ADD COLUMN IF NOT EXISTS markdown_content TEXT,
  ADD COLUMN IF NOT EXISTS html_content TEXT,
  ADD COLUMN IF NOT EXISTS pdf_path VARCHAR(500);

-- Update constraints if needed
ALTER TABLE cycle_report_test_report_sections 
  ALTER COLUMN phase_id SET NOT NULL,
  ALTER COLUMN cycle_id SET NOT NULL,
  ALTER COLUMN report_id SET NOT NULL,
  ALTER COLUMN section_title SET NOT NULL;

-- Drop the old primary key if it exists and use id instead
ALTER TABLE cycle_report_test_report_sections 
  DROP CONSTRAINT IF EXISTS cycle_report_test_report_sections_pkey;
  
ALTER TABLE cycle_report_test_report_sections 
  ADD PRIMARY KEY (id);

-- Create unique constraint for section_id if it should remain unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_test_report_sections_section_id 
  ON cycle_report_test_report_sections(section_id);

-- Add the missing constraints from the model
ALTER TABLE cycle_report_test_report_sections
  ADD CONSTRAINT IF NOT EXISTS uq_test_report_section_phase 
  UNIQUE(phase_id, section_name);

ALTER TABLE cycle_report_test_report_sections
  ADD CONSTRAINT IF NOT EXISTS uq_test_report_section_report 
  UNIQUE(cycle_id, report_id, section_name);

-- Create the missing indexes
CREATE INDEX IF NOT EXISTS idx_test_report_sections_phase 
  ON cycle_report_test_report_sections(phase_id);
  
CREATE INDEX IF NOT EXISTS idx_test_report_sections_cycle_report 
  ON cycle_report_test_report_sections(cycle_id, report_id);
  
CREATE INDEX IF NOT EXISTS idx_test_report_sections_status 
  ON cycle_report_test_report_sections(status);
  
CREATE INDEX IF NOT EXISTS idx_test_report_sections_approvals 
  ON cycle_report_test_report_sections(tester_approved, report_owner_approved, executive_approved);

-- Migrate existing data if needed
UPDATE cycle_report_test_report_sections 
SET 
  section_title = section_name,
  section_content = COALESCE(content_data, '{}'::jsonb),
  status = 'draft'
WHERE section_title IS NULL;

-- Add comment
COMMENT ON TABLE cycle_report_test_report_sections IS 'Test report sections with built-in approval workflow';