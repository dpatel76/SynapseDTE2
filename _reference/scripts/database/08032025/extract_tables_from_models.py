#!/usr/bin/env python3
"""
Extract table definitions by parsing model files
"""

import os
import re
from pathlib import Path

def extract_tables_from_models():
    """Extract table names and structures from model files"""
    
    models_dir = Path("/Users/dineshpatel/code/projects/SynapseDTE2/app/models")
    output_file = Path(__file__).parent / "01_complete_schema.sql"
    
    # Collect all table definitions
    tables = {}
    
    # Parse each model file
    for model_file in models_dir.glob("*.py"):
        if model_file.name in ['__init__.py', 'base.py', 'audit_mixin.py']:
            continue
            
        with open(model_file, 'r') as f:
            content = f.read()
            
        # Find table name
        table_match = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', content)
        if table_match:
            table_name = table_match.group(1)
            
            # Extract column definitions
            columns = []
            column_matches = re.findall(
                r'(\w+)\s*=\s*Column\((.*?)\)',
                content,
                re.DOTALL
            )
            
            for col_name, col_def in column_matches:
                # Clean up column definition
                col_def = col_def.replace('\n', ' ').strip()
                columns.append((col_name, col_def))
            
            if columns:
                tables[table_name] = {
                    'file': model_file.name,
                    'columns': columns
                }
    
    # Generate SQL file
    with open(output_file, 'w') as out:
        out.write("-- Complete SynapseDTE Database Schema\n")
        out.write("-- Extracted from SQLAlchemy models\n")
        out.write("-- Date: 2025-08-03\n\n")
        
        # Extensions
        out.write("-- Enable required extensions\n")
        out.write("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")
        out.write("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";\n\n")
        
        # Custom types found in models
        out.write("-- Custom Types\n")
        out.write("-- User role enum\n")
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
        
        # Add other common enums
        enums = [
            ('activity_status_enum', ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'REVISION_REQUESTED', 'BLOCKED', 'SKIPPED']),
            ('activity_type_enum', ['START', 'TASK', 'REVIEW', 'APPROVAL', 'COMPLETE', 'CUSTOM']),
            ('evidence_status_enum', ['pending', 'submitted', 'approved', 'rejected', 'expired']),
            ('evidence_type_enum', ['document', 'screenshot', 'data_export', 'manual_entry', 'api_response']),
            ('test_case_status_enum', ['Pending', 'Submitted', 'Overdue']),
            ('tester_decision_enum', ['approved', 'rejected', 'requires_revision']),
            ('observation_type_enum', ['data_quality', 'process', 'control', 'compliance', 'other']),
            ('observation_status_enum', ['open', 'in_progress', 'resolved', 'closed', 'deferred']),
            ('observation_priority_enum', ['low', 'medium', 'high', 'critical']),
            ('rule_type_enum', ['not_null', 'unique', 'range', 'pattern', 'reference', 'custom']),
            ('rule_category_enum', ['Completeness', 'Accuracy', 'Consistency', 'Timeliness', 'Validity', 'Uniqueness']),
            ('rule_status_enum', ['draft', 'pending_approval', 'approved', 'rejected', 'deprecated']),
            ('profiling_status_enum', ['pending', 'running', 'completed', 'failed']),
            ('phase_status_enum', ['not_started', 'in_progress', 'completed', 'blocked']),
            ('workflow_phase_enum', ['Planning', 'Data Profiling', 'Scoping', 'Data Owner ID', 'Sample Selection', 'Request for Information', 'Test Execution', 'Observation Management', 'Test Report'])
        ]
        
        for enum_name, values in enums:
            out.write(f"DROP TYPE IF EXISTS {enum_name} CASCADE;\n")
            out.write(f"CREATE TYPE {enum_name} AS ENUM (\n")
            out.write("    '" + "',\n    '".join(values) + "'\n")
            out.write(");\n\n")
        
        # Write tables
        out.write("\n-- Tables\n")
        for table_name, table_info in sorted(tables.items()):
            out.write(f"\n-- Table: {table_name} (from {table_info['file']})\n")
            out.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
            
            # Convert column definitions to SQL
            sql_columns = []
            for col_name, col_def in table_info['columns']:
                # Skip relationship definitions
                if 'relationship' in col_def:
                    continue
                    
                # Convert SQLAlchemy types to PostgreSQL
                sql_type = col_def
                sql_type = re.sub(r'Integer', 'INTEGER', sql_type)
                sql_type = re.sub(r'String\((\d+)\)', r'VARCHAR(\1)', sql_type)
                sql_type = re.sub(r'Text', 'TEXT', sql_type)
                sql_type = re.sub(r'Boolean', 'BOOLEAN', sql_type)
                sql_type = re.sub(r'DateTime', 'TIMESTAMP WITH TIME ZONE', sql_type)
                sql_type = re.sub(r'Date', 'DATE', sql_type)
                sql_type = re.sub(r'Float', 'FLOAT', sql_type)
                sql_type = re.sub(r'JSONB', 'JSONB', sql_type)
                
                # Handle primary key
                if 'primary_key=True' in col_def:
                    if 'Integer' in col_def:
                        sql_columns.append(f"    {col_name} SERIAL PRIMARY KEY")
                    else:
                        sql_columns.append(f"    {col_name} {sql_type.split(',')[0]} PRIMARY KEY")
                else:
                    # Extract just the type
                    type_match = re.search(r'^(\w+(?:\(\d+\))?)', sql_type)
                    if type_match:
                        col_type = type_match.group(1)
                        
                        # Add constraints
                        constraints = []
                        if 'nullable=False' in col_def:
                            constraints.append('NOT NULL')
                        if 'unique=True' in col_def:
                            constraints.append('UNIQUE')
                        if 'default=' in col_def:
                            default_match = re.search(r'default=([^,\)]+)', col_def)
                            if default_match:
                                default_val = default_match.group(1)
                                if default_val == 'True':
                                    constraints.append('DEFAULT TRUE')
                                elif default_val == 'False':
                                    constraints.append('DEFAULT FALSE')
                                elif 'datetime.utcnow' in default_val or 'func.now' in default_val:
                                    constraints.append('DEFAULT CURRENT_TIMESTAMP')
                        
                        col_sql = f"    {col_name} {col_type}"
                        if constraints:
                            col_sql += ' ' + ' '.join(constraints)
                        sql_columns.append(col_sql)
            
            if sql_columns:
                out.write(',\n'.join(sql_columns))
                out.write("\n);\n")
        
        out.write(f"\n-- Total tables: {len(tables)}\n")
    
    print(f"Created schema file: {output_file}")
    print(f"Total tables extracted: {len(tables)}")
    
    # Create test user file
    test_user_file = Path(__file__).parent / "99_test_user.sql"
    with open(test_user_file, 'w') as f:
        f.write("-- Test user with bcrypt hash for password123\n")
        f.write("INSERT INTO users (email, hashed_password, first_name, last_name, role, is_active) VALUES\n")
        f.write("('tester@example.com', '$2b$12$D/8avO4TQoqLTPI5jVzooOHlgQgaVHdm4pGp303CkmjXcn/vMQpie', 'Test', 'User', 'Tester', true)\n")
        f.write("ON CONFLICT (email) DO NOTHING;\n")

if __name__ == "__main__":
    extract_tables_from_models()