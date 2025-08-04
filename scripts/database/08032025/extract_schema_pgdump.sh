#!/bin/bash
# Extract schema using pg_dump

echo "Extracting schema from database..."

# Set connection parameters
export PGHOST=localhost
export PGUSER=synapse_user
export PGPASSWORD=synapse_password
export PGDATABASE=synapse_dt

# Extract schema only (no data)
pg_dump --schema-only \
        --no-owner \
        --no-privileges \
        --no-tablespaces \
        --no-security-labels \
        --no-comments \
        --file=01_complete_schema.sql

# Check if successful
if [ $? -eq 0 ]; then
    echo "Schema extracted successfully to 01_complete_schema.sql"
    
    # Add header comment
    sed -i '' '1i\
-- SynapseDTE Complete Database Schema\
-- Generated from existing database: synapse_dt\
-- Date: '$(date)'\
--\
' 01_complete_schema.sql
    
else
    echo "Error extracting schema"
    exit 1
fi