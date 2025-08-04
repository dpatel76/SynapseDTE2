-- Add audit columns to LOBs table
ALTER TABLE lobs 
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

-- Add comments
COMMENT ON COLUMN lobs.created_by_id IS 'ID of user who created this record';
COMMENT ON COLUMN lobs.updated_by_id IS 'ID of user who last updated this record';