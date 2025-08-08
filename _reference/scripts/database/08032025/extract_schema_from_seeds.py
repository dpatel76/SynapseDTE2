#!/usr/bin/env python3
"""
Extract table structure from SQL seed files
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def extract_tables_from_seeds():
    """Extract table names and columns from INSERT statements in seed files"""
    
    seed_dir = Path(__file__).parent / "sql_seeds"
    output_file = Path(__file__).parent / "01_schema.sql"
    
    # Dictionary to store table info
    tables = defaultdict(lambda: {
        'columns': set(),
        'files': []
    })
    
    # Parse each seed file
    for seed_file in seed_dir.glob("*.sql"):
        with open(seed_file, 'r') as f:
            content = f.read()
            
        # Find INSERT statements
        # Pattern: INSERT INTO table_name (columns) VALUES
        insert_pattern = r'INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES'
        
        for match in re.finditer(insert_pattern, content, re.IGNORECASE | re.DOTALL):
            table_name = match.group(1).lower()
            columns_str = match.group(2)
            
            # Parse columns
            columns = [col.strip() for col in columns_str.split(',')]
            
            tables[table_name]['columns'].update(columns)
            if seed_file.name not in tables[table_name]['files']:
                tables[table_name]['files'].append(seed_file.name)
    
    # Generate schema file
    with open(output_file, 'w') as out:
        out.write("-- SynapseDTE Complete Database Schema\n")
        out.write("-- Extracted from SQL seed files\n")
        out.write("-- Date: 2025-08-03\n\n")
        
        # Extensions
        out.write("-- Enable required extensions\n")
        out.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
        out.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
        
        # Write custom types based on known enums
        out.write("-- Custom Types\n")
        
        # User role enum
        out.write("DROP TYPE IF EXISTS user_role_enum CASCADE;\n")
        out.write("CREATE TYPE user_role_enum AS ENUM (\n")
        out.write("    'Tester',\n")
        out.write("    'Test Executive',\n")
        out.write("    'Report Owner',\n")
        out.write("    'Report Executive',\n")
        out.write("    'Data Owner',\n")
        out.write("    'Data Executive',\n")
        out.write("    'Admin'\n")
        out.write(");\n\n")
        
        # Activity status enum
        out.write("DROP TYPE IF EXISTS activity_status_enum CASCADE;\n")
        out.write("CREATE TYPE activity_status_enum AS ENUM (\n")
        out.write("    'NOT_STARTED',\n")
        out.write("    'IN_PROGRESS',\n")
        out.write("    'COMPLETED',\n")
        out.write("    'REVISION_REQUESTED',\n")
        out.write("    'BLOCKED',\n")
        out.write("    'SKIPPED'\n")
        out.write(");\n\n")
        
        # Activity type enum
        out.write("DROP TYPE IF EXISTS activity_type_enum CASCADE;\n")
        out.write("CREATE TYPE activity_type_enum AS ENUM (\n")
        out.write("    'START',\n")
        out.write("    'TASK',\n")
        out.write("    'REVIEW',\n")
        out.write("    'APPROVAL',\n")
        out.write("    'COMPLETE',\n")
        out.write("    'CUSTOM'\n")
        out.write(");\n\n")
        
        # Evidence status enum
        out.write("DROP TYPE IF EXISTS evidence_status_enum CASCADE;\n")
        out.write("CREATE TYPE evidence_status_enum AS ENUM (\n")
        out.write("    'pending',\n")
        out.write("    'submitted',\n")
        out.write("    'approved',\n")
        out.write("    'rejected',\n")
        out.write("    'expired'\n")
        out.write(");\n\n")
        
        # Evidence type enum
        out.write("DROP TYPE IF EXISTS evidence_type_enum CASCADE;\n")
        out.write("CREATE TYPE evidence_type_enum AS ENUM (\n")
        out.write("    'document',\n")
        out.write("    'screenshot',\n")
        out.write("    'data_export',\n")
        out.write("    'manual_entry',\n")
        out.write("    'api_response'\n")
        out.write(");\n\n")
        
        # Test case status enum
        out.write("DROP TYPE IF EXISTS test_case_status_enum CASCADE;\n")
        out.write("CREATE TYPE test_case_status_enum AS ENUM (\n")
        out.write("    'Pending',\n")
        out.write("    'Submitted',\n")
        out.write("    'Overdue'\n")
        out.write(");\n\n")
        
        # Tester decision enum
        out.write("DROP TYPE IF EXISTS tester_decision_enum CASCADE;\n")
        out.write("CREATE TYPE tester_decision_enum AS ENUM (\n")
        out.write("    'approved',\n")
        out.write("    'rejected',\n")
        out.write("    'requires_revision'\n")
        out.write(");\n\n")
        
        # Observation type enum
        out.write("DROP TYPE IF EXISTS observation_type_enum CASCADE;\n")
        out.write("CREATE TYPE observation_type_enum AS ENUM (\n")
        out.write("    'data_quality',\n")
        out.write("    'process',\n")
        out.write("    'control',\n")
        out.write("    'compliance',\n")
        out.write("    'other'\n")
        out.write(");\n\n")
        
        # Observation status enum
        out.write("DROP TYPE IF EXISTS observation_status_enum CASCADE;\n")
        out.write("CREATE TYPE observation_status_enum AS ENUM (\n")
        out.write("    'open',\n")
        out.write("    'in_progress',\n")
        out.write("    'resolved',\n")
        out.write("    'closed',\n")
        out.write("    'deferred'\n")
        out.write(");\n\n")
        
        # Observation priority enum
        out.write("DROP TYPE IF EXISTS observation_priority_enum CASCADE;\n")
        out.write("CREATE TYPE observation_priority_enum AS ENUM (\n")
        out.write("    'low',\n")
        out.write("    'medium',\n")
        out.write("    'high',\n")
        out.write("    'critical'\n")
        out.write(");\n\n")
        
        # Rule type enum
        out.write("DROP TYPE IF EXISTS rule_type_enum CASCADE;\n")
        out.write("CREATE TYPE rule_type_enum AS ENUM (\n")
        out.write("    'not_null',\n")
        out.write("    'unique',\n")
        out.write("    'range',\n")
        out.write("    'pattern',\n")
        out.write("    'reference',\n")
        out.write("    'custom'\n")
        out.write(");\n\n")
        
        # Rule category enum
        out.write("DROP TYPE IF EXISTS rule_category_enum CASCADE;\n")
        out.write("CREATE TYPE rule_category_enum AS ENUM (\n")
        out.write("    'Completeness',\n")
        out.write("    'Accuracy',\n")
        out.write("    'Consistency',\n")
        out.write("    'Timeliness',\n")
        out.write("    'Validity',\n")
        out.write("    'Uniqueness'\n")
        out.write(");\n\n")
        
        # Rule status enum
        out.write("DROP TYPE IF EXISTS rule_status_enum CASCADE;\n")
        out.write("CREATE TYPE rule_status_enum AS ENUM (\n")
        out.write("    'draft',\n")
        out.write("    'pending_approval',\n")
        out.write("    'approved',\n")
        out.write("    'rejected',\n")
        out.write("    'deprecated'\n")
        out.write(");\n\n")
        
        # Profiling status enum
        out.write("DROP TYPE IF EXISTS profiling_status_enum CASCADE;\n")
        out.write("CREATE TYPE profiling_status_enum AS ENUM (\n")
        out.write("    'pending',\n")
        out.write("    'running',\n")
        out.write("    'completed',\n")
        out.write("    'failed'\n")
        out.write(");\n\n")
        
        # Phase status enum
        out.write("DROP TYPE IF EXISTS phase_status_enum CASCADE;\n")
        out.write("CREATE TYPE phase_status_enum AS ENUM (\n")
        out.write("    'not_started',\n")
        out.write("    'in_progress',\n")
        out.write("    'completed',\n")
        out.write("    'blocked'\n")
        out.write(");\n\n")
        
        # Workflow phase enum
        out.write("DROP TYPE IF EXISTS workflow_phase_enum CASCADE;\n")
        out.write("CREATE TYPE workflow_phase_enum AS ENUM (\n")
        out.write("    'Planning',\n")
        out.write("    'Data Profiling',\n")
        out.write("    'Scoping',\n")
        out.write("    'Data Owner ID',\n")
        out.write("    'Sample Selection',\n")
        out.write("    'Request for Information',\n")
        out.write("    'Test Execution',\n")
        out.write("    'Observation Management',\n")
        out.write("    'Test Report'\n")
        out.write(");\n\n")
        
        # Sample status enum
        out.write("DROP TYPE IF EXISTS sample_status_enum CASCADE;\n")
        out.write("CREATE TYPE sample_status_enum AS ENUM (\n")
        out.write("    'pending',\n")
        out.write("    'selected',\n")
        out.write("    'approved',\n")
        out.write("    'rejected',\n")
        out.write("    'in_testing',\n")
        out.write("    'completed'\n")
        out.write(");\n\n")
        
        # Request status enum
        out.write("DROP TYPE IF EXISTS request_status_enum CASCADE;\n")
        out.write("CREATE TYPE request_status_enum AS ENUM (\n")
        out.write("    'open',\n")
        out.write("    'in_progress',\n")
        out.write("    'pending_response',\n")
        out.write("    'completed',\n")
        out.write("    'cancelled'\n")
        out.write(");\n\n")
        
        # Test execution status enum
        out.write("DROP TYPE IF EXISTS test_execution_status_enum CASCADE;\n")
        out.write("CREATE TYPE test_execution_status_enum AS ENUM (\n")
        out.write("    'not_started',\n")
        out.write("    'in_progress',\n")
        out.write("    'passed',\n")
        out.write("    'failed',\n")
        out.write("    'blocked',\n")
        out.write("    'skipped'\n")
        out.write(");\n\n")
        
        # Report status enum
        out.write("DROP TYPE IF EXISTS report_status_enum CASCADE;\n")
        out.write("CREATE TYPE report_status_enum AS ENUM (\n")
        out.write("    'draft',\n")
        out.write("    'in_review',\n")
        out.write("    'approved',\n")
        out.write("    'published',\n")
        out.write("    'archived'\n")
        out.write(");\n\n")
        
        # Write tables
        out.write("\n-- Tables\n")
        for table_name in sorted(tables.keys()):
            table_info = tables[table_name]
            out.write(f"\n-- Table: {table_name} (from {', '.join(sorted(table_info['files'])[:3])})\n")
            out.write(f"-- Columns found: {', '.join(sorted(table_info['columns'])[:10])}")
            if len(table_info['columns']) > 10:
                out.write(f" and {len(table_info['columns']) - 10} more")
            out.write("\n")
        
        out.write(f"\n-- Total tables found: {len(tables)}\n")
        out.write("-- Note: This file lists tables found in seed data.\n")
        out.write("-- The actual schema with column types is needed from the application models.\n")
    
    print(f"Found {len(tables)} tables in seed files")
    print(f"Output written to: {output_file}")
    
    # Also print table list
    print("\nTables found:")
    for table_name in sorted(tables.keys()):
        print(f"  - {table_name} ({len(tables[table_name]['columns'])} columns)")

if __name__ == "__main__":
    extract_tables_from_seeds()