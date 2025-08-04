#!/bin/bash

# Script to create Request Info Evidence Versions tables

echo "Creating Request Info Evidence Versions tables..."

# Run the SQL script
psql -U postgres -h localhost -d synapseDTE -f create_request_info_evidence_versions_table.sql

if [ $? -eq 0 ]; then
    echo "✅ Tables created successfully!"
    
    # Verify the tables exist
    echo ""
    echo "Verifying tables..."
    psql -U postgres -h localhost -d synapseDTE -c "\dt cycle_report_request_info*"
else
    echo "❌ Failed to create tables"
    exit 1
fi