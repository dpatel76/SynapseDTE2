#!/usr/bin/env python3
"""
Fix column ordering in the migration file to follow the pattern:
1. Primary key columns first
2. Foreign key columns second  
3. Business columns third
4. Audit/timestamp columns last (created_at, updated_at, created_by_id, updated_by_id)
"""

import re
from typing import List, Tuple, Dict


def parse_column_line(line: str, table_name: str = None) -> Dict:
    """Parse a column definition line and extract its properties."""
    # Extract column name
    col_match = re.match(r"sa\.Column\('([^']+)'", line.strip())
    if not col_match:
        return None
        
    column_name = col_match.group(1)
    
    # Common primary key patterns
    primary_key_patterns = [
        'id', '_id', 'user_id', 'lob_id', 'role_id', 'permission_id',
        'cycle_id', 'report_id', 'phase_id', 'audit_id', 'template_id',
        'assignment_id', 'resource_id', 'sla_config_id', 'activity_id',
        'execution_id', 'validation_id', 'metric_id', 'log_id', 'violation_id',
        'escalation_rule_id', 'history_id', 'dependency_id', 'step_id',
        'transition_id', 'alert_id', 'notification_id', 'data_source_id',
        'result_id', 'file_id', 'version_id', 'rule_id', 'sample_id',
        'evidence_id', 'document_id', 'observation_id', 'review_id',
        'mapping_id', 'configuration_id', 'job_id', 'profile_id',
        'dict_id', 'test_case_id', 'comparison_id', 'assessment_id',
        'resolution_id', 'generation_id', 'extraction_id', 'revision_id'
    ]
    
    # Check if it's likely a primary key
    is_primary = False
    if 'primary_key=True' in line:
        is_primary = True
    elif column_name in primary_key_patterns:
        # Check if this column name matches the table's expected primary key
        # For example, users table should have user_id as primary key
        is_primary = True
    elif column_name == 'id' and not any(pk in column_name for pk in ['_id', 'by_id']):
        is_primary = True
        
    # Determine if it's a foreign key (but not audit columns)
    is_foreign = ('ForeignKey' in line or 
                  (column_name.endswith('_id') and not is_primary and 
                   column_name not in ['created_by_id', 'updated_by_id']))
    
    is_audit = column_name in ['created_at', 'updated_at', 'created_by_id', 'updated_by_id']
    
    # Assign sort order
    if is_primary:
        sort_order = 1
    elif is_foreign and not is_audit:
        sort_order = 2
    elif is_audit:
        sort_order = 4
    else:
        sort_order = 3
        
    return {
        'line': line,
        'name': column_name,
        'sort_order': sort_order,
        'is_primary': is_primary
    }


def reorder_table_columns(table_content: str, table_name: str = None) -> str:
    """Reorder columns in a table definition."""
    lines = table_content.strip().split('\n')
    
    columns = []
    constraints = []
    
    # First pass - identify primary key from PrimaryKeyConstraint
    primary_key_cols = set()
    for line in lines:
        if 'PrimaryKeyConstraint' in line:
            # Extract column names from PrimaryKeyConstraint
            pk_match = re.search(r"PrimaryKeyConstraint\(([^)]+)\)", line)
            if pk_match:
                pk_content = pk_match.group(1)
                # Extract quoted column names
                pk_cols = re.findall(r"'([^']+)'", pk_content)
                primary_key_cols.update(pk_cols)
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('sa.Column'):
            col_info = parse_column_line(line, table_name)
            if col_info:
                # Override primary key detection if found in constraint
                col_name = col_info['name']
                if col_name in primary_key_cols:
                    col_info['is_primary'] = True
                    col_info['sort_order'] = 1
                columns.append(col_info)
        elif line.startswith('sa.'):
            # It's a constraint
            constraints.append(line)
    
    # Sort columns by order, then by name for consistency
    columns.sort(key=lambda x: (x['sort_order'], x['name']))
    
    # Rebuild table content
    result_lines = []
    
    # Add columns
    for i, col in enumerate(columns):
        clean_line = col['line'].rstrip(',')
        if i < len(columns) - 1 or constraints:
            result_lines.append(f"    {clean_line},")
        else:
            result_lines.append(f"    {clean_line}")
    
    # Add constraints (no comma on the last one)
    for i, constraint in enumerate(constraints):
        clean_constraint = constraint.rstrip(',')
        if i < len(constraints) - 1:
            result_lines.append(f"    {clean_constraint},")
        else:
            result_lines.append(f"    {clean_constraint}")
    
    return '\n'.join(result_lines)


def process_migration_file(input_file: str, output_file: str):
    """Process the migration file to fix column ordering."""
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Find all table creation statements
    table_pattern = r'(op\.create_table\(\'([^\']+)\',\s*\n)(.*?)(\n\s*\))'
    
    def replace_table(match):
        prefix = match.group(1)
        table_name = match.group(2)
        table_content = match.group(3)
        suffix = match.group(4)
        
        # Reorder columns in this table
        reordered = reorder_table_columns(table_content, table_name)
        
        return prefix + reordered + suffix
    
    # Replace all table definitions with reordered columns
    new_content = re.sub(table_pattern, replace_table, content, flags=re.DOTALL)
    
    # Write the output
    with open(output_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Column ordering fixed in {output_file}")


if __name__ == "__main__":
    # Process the refactored migration file
    input_file = "/Users/dineshpatel/code/projects/SynapseDTE2/alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models_final.py"
    output_file = "/Users/dineshpatel/code/projects/SynapseDTE2/alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models_ordered.py"
    
    process_migration_file(input_file, output_file)