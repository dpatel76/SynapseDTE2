#!/bin/bash

# Direct SQL update script for SynapseDTE database
# This script updates sample selection decisions and phase names

echo "Running database updates for SynapseDTE..."

# Database connection parameters - adjust as needed
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-synapsedte}"
DB_USER="${DB_USER:-postgres}"

# Run the SQL file
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f update_sample_decisions_and_phase_names.sql

echo "Database updates completed!"