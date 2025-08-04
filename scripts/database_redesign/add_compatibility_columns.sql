-- Add compatibility columns to report_inventory to support existing code

-- Add missing columns to report_inventory
ALTER TABLE report_inventory 
ADD COLUMN IF NOT EXISTS report_owner_id INTEGER REFERENCES users(user_id),
ADD COLUMN IF NOT EXISTS lob_id INTEGER REFERENCES lobs(lob_id),
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true NOT NULL,
ADD COLUMN IF NOT EXISTS regulation VARCHAR(255);

-- Create the reports_data_sources table for new design
CREATE TABLE IF NOT EXISTS report_data_sources (
    report_id INTEGER NOT NULL REFERENCES report_inventory(id),
    data_source_id INTEGER NOT NULL REFERENCES data_sources(data_source_id),
    table_name VARCHAR(255),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    PRIMARY KEY (report_id, data_source_id)
);

-- Update regulation column based on regulatory_requirement
UPDATE report_inventory 
SET regulation = CASE 
    WHEN regulatory_requirement = true THEN 'Required'
    ELSE NULL
END;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_report_inventory_owner ON report_inventory(report_owner_id);
CREATE INDEX IF NOT EXISTS idx_report_inventory_lob ON report_inventory(lob_id);

\echo 'Compatibility columns added successfully'