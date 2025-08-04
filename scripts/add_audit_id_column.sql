-- Add audit_id column to cycle_report_request_info_audit_logs table

-- First check if the column already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cycle_report_request_info_audit_logs' 
        AND column_name = 'audit_id'
    ) THEN
        -- Add audit_id column
        ALTER TABLE cycle_report_request_info_audit_logs 
        ADD COLUMN audit_id VARCHAR(36) DEFAULT gen_random_uuid()::text;
        
        -- Create unique index since it should be a primary key
        CREATE UNIQUE INDEX idx_audit_logs_audit_id ON cycle_report_request_info_audit_logs(audit_id);
        
        -- Update existing rows to have unique audit_ids
        UPDATE cycle_report_request_info_audit_logs 
        SET audit_id = gen_random_uuid()::text 
        WHERE audit_id IS NULL;
        
        -- Make it NOT NULL after populating
        ALTER TABLE cycle_report_request_info_audit_logs 
        ALTER COLUMN audit_id SET NOT NULL;
    END IF;
END $$;

-- Also add missing columns if they don't exist
ALTER TABLE cycle_report_request_info_audit_logs
ADD COLUMN IF NOT EXISTS cycle_id INTEGER REFERENCES test_cycles(cycle_id);

ALTER TABLE cycle_report_request_info_audit_logs
ADD COLUMN IF NOT EXISTS report_id INTEGER REFERENCES reports(id);

ALTER TABLE cycle_report_request_info_audit_logs
ADD COLUMN IF NOT EXISTS session_id VARCHAR(100);

ALTER TABLE cycle_report_request_info_audit_logs
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(user_id);

ALTER TABLE cycle_report_request_info_audit_logs
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(user_id);