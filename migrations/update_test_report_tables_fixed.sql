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

-- Set default values for NOT NULL columns where needed
UPDATE cycle_report_test_report_sections 
SET 
  cycle_id = 55,  -- Default to current cycle
  report_id = 156  -- Default to current report
WHERE cycle_id IS NULL OR report_id IS NULL;

-- Update phase_id to have a default value for existing null entries
UPDATE cycle_report_test_report_sections 
SET phase_id = 473  -- Use the test report phase we found
WHERE phase_id IS NULL;

-- Now we can safely set NOT NULL constraints
ALTER TABLE cycle_report_test_report_sections 
  ALTER COLUMN phase_id SET NOT NULL,
  ALTER COLUMN cycle_id SET NOT NULL,
  ALTER COLUMN report_id SET NOT NULL;

-- Set section_title from section_name if it's null
UPDATE cycle_report_test_report_sections 
SET section_title = section_name
WHERE section_title IS NULL;

ALTER TABLE cycle_report_test_report_sections 
  ALTER COLUMN section_title SET NOT NULL;

-- Handle primary key change
-- First check if there's already a primary key
DO $$
BEGIN
  -- Drop existing primary key if it exists
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cycle_report_test_report_sections_pkey') THEN
    ALTER TABLE cycle_report_test_report_sections DROP CONSTRAINT cycle_report_test_report_sections_pkey;
  END IF;
  
  -- Add new primary key on id column
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cycle_report_test_report_sections_pkey' AND conrelid = 'cycle_report_test_report_sections'::regclass) THEN
    ALTER TABLE cycle_report_test_report_sections ADD PRIMARY KEY (id);
  END IF;
END
$$;

-- Create unique constraint for section_id if it should remain unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_test_report_sections_section_id 
  ON cycle_report_test_report_sections(section_id);

-- Add the missing constraints from the model
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_test_report_section_phase') THEN
    ALTER TABLE cycle_report_test_report_sections
      ADD CONSTRAINT uq_test_report_section_phase UNIQUE(phase_id, section_name);
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_test_report_section_report') THEN
    ALTER TABLE cycle_report_test_report_sections
      ADD CONSTRAINT uq_test_report_section_report UNIQUE(cycle_id, report_id, section_name);
  END IF;
END
$$;

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
  section_content = COALESCE(content_data::jsonb, '{}'::jsonb),
  status = 'draft'
WHERE section_content IS NULL;

-- Add comment
COMMENT ON TABLE cycle_report_test_report_sections IS 'Test report sections with built-in approval workflow';