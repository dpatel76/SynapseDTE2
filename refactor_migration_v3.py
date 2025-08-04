#!/usr/bin/env python3
"""
Enhanced script to refactor Alembic migration file to handle circular dependencies
and reorganize columns in proper order.

This script:
1. Parses the migration file 
2. Extracts ALL ForeignKeyConstraint lines from table creation statements
3. Reorganizes columns in order: PK -> FK columns -> Business columns -> Audit/timestamp columns
4. Creates all tables without foreign key constraints  
5. Adds ALL foreign keys at the end using op.create_foreign_key()

Column Order:
1. Primary Key columns (id, table_id, etc.)
2. Foreign Key columns (*_id columns)  
3. Business/domain columns (name, email, status, etc.)
4. Audit/timestamp columns (created_at, updated_at, created_by_id, updated_by_id)
"""

import re
import sys
from typing import List, Tuple, Dict, Optional
from pathlib import Path


class ColumnInfo:
    def __init__(self, line: str, column_name: str, is_primary_key: bool = False, 
                 is_foreign_key: bool = False, is_audit: bool = False):
        self.line = line.strip()
        self.column_name = column_name
        self.is_primary_key = is_primary_key
        self.is_foreign_key = is_foreign_key
        self.is_audit = is_audit
        self.sort_order = self.get_sort_order()
    
    def get_sort_order(self) -> int:
        """Determine sort order: PK(0) -> FK(1) -> Business(2) -> Audit(3)"""
        if self.is_primary_key:
            return 0
        elif self.is_foreign_key:
            return 1
        elif self.is_audit:
            return 3
        else:
            return 2  # Business columns
    
    def __lt__(self, other):
        # First sort by category
        if self.sort_order != other.sort_order:
            return self.sort_order < other.sort_order
        # Within same category, sort alphabetically
        return self.column_name < other.column_name


def identify_column_type(column_line: str, column_name: str, foreign_key_columns: set) -> ColumnInfo:
    """Identify what type of column this is and return ColumnInfo object."""
    
    # Check if it's a primary key column
    is_primary_key = (
        column_name in ['id', 'user_id', 'lob_id', 'role_id', 'resource_id', 'permission_id', 
                       'cycle_id', 'report_id', 'phase_id', 'execution_id', 'step_id', 
                       'activity_id', 'assignment_id', 'sla_config_id', 'escalation_rule_id',
                       'violation_id', 'version_id', 'observation_id', 'evidence_id',
                       'document_id', 'sample_id', 'test_case_id', 'result_id', 'job_id',
                       'mapping_id', 'attribute_id', 'data_source_id', 'configuration_id',
                       'rule_id', 'validation_id', 'history_id', 'log_id', 'notification_id'] or
        column_name.endswith('_id') and not column_name.endswith('_by_id') and 
        ('PRIMARY KEY' in column_line.upper() or 'SERIAL' in column_line.upper() or 
         'AUTO_INCREMENT' in column_line.upper())
    )
    
    # Check if it's a foreign key column (ends with _id but not audit columns)
    is_foreign_key = (
        column_name in foreign_key_columns or
        (column_name.endswith('_id') and not is_primary_key and 
         column_name not in ['created_by_id', 'updated_by_id'])
    )
    
    # Check if it's an audit/timestamp column
    is_audit = (
        column_name in ['created_at', 'updated_at', 'created_by_id', 'updated_by_id',
                       'deleted_at', 'deleted_by_id', 'archived_at', 'archived_by_id',
                       'approved_at', 'approved_by_id', 'reviewed_at', 'reviewed_by_id',
                       'submitted_at', 'submitted_by_id', 'validated_at', 'validated_by_id',
                       'executed_at', 'executed_by_id', 'completed_at', 'completed_by_id',
                       'started_at', 'started_by_id', 'finished_at', 'finished_by_id',
                       'last_accessed_at', 'last_modified_at', 'last_viewed_at', 
                       'last_downloaded_at', 'last_viewed_by', 'last_downloaded_by',
                       'version_created_at', 'version_created_by']
    )
    
    return ColumnInfo(column_line, column_name, is_primary_key, is_foreign_key, is_audit)


def reorganize_table_columns(table_content: str, table_name: str, foreign_key_columns: set) -> str:
    """Reorganize columns within a table definition in the proper order."""
    
    lines = table_content.split('\n')
    columns = []
    constraints = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a column definition
        col_match = re.match(r"sa\.Column\('([^']+)'", line)
        if col_match:
            column_name = col_match.group(1)
            col_info = identify_column_type(line, column_name, foreign_key_columns)
            columns.append(col_info)
        elif line.startswith('sa.'):
            # It's a constraint (PrimaryKeyConstraint, UniqueConstraint, etc.)
            constraints.append(line)
    
    # Sort columns by the defined order
    columns.sort()
    
    # Rebuild the table content
    result_lines = []
    
    # Add columns first
    for i, col in enumerate(columns):
        # Clean the column line to ensure it doesn't already have a comma at the end
        clean_line = col.line.rstrip(',')
        
        if i < len(columns) - 1 or constraints:
            # Add comma if not the last item overall
            result_lines.append(f"    {clean_line},")
        else:
            # Last item overall - no comma
            result_lines.append(f"    {clean_line}")
    
    # Add constraints
    for i, constraint in enumerate(constraints):
        clean_constraint = constraint.rstrip(',')
        if i < len(constraints) - 1:
            result_lines.append(f"    {clean_constraint}")
        else:
            result_lines.append(f"    {clean_constraint}")
    
    return '\n'.join(result_lines)


def extract_foreign_keys_and_reorganize(content: str) -> Tuple[str, List[Dict]]:
    """
    Extract foreign key constraints and reorganize columns in table creation statements.
    
    Returns:
        - Modified content with ForeignKeyConstraint lines removed and columns reorganized
        - List of foreign key definitions to add at the end
    """
    
    foreign_keys = []
    lines = content.split('\n')
    modified_lines = []
    
    in_table_creation = False
    current_table_name = None
    current_table_lines = []
    current_foreign_key_columns = set()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if we're starting a new table creation
        table_match = re.match(r"\s*op\.create_table\('([^']+)',", line)
        if table_match:
            in_table_creation = True
            current_table_name = table_match.group(1)
            current_table_lines = [line]
            current_foreign_key_columns = set()
            i += 1
            continue
    
        # Check if we're ending table creation
        if in_table_creation and re.match(r'\s*\)\s*$', line):
            # Process the complete table
            if current_table_name != 'lobs':  # Skip lobs table - already handled correctly
                # Extract table content (everything between create_table and closing paren)
                table_content = '\n'.join(current_table_lines[1:])  # Skip the create_table line
                
                # First pass: collect foreign key column names
                for table_line in current_table_lines[1:]:
                    fk_match = re.match(r'\s*sa\.ForeignKeyConstraint\(\[([^\]]+)\]', table_line)
                    if fk_match:
                        source_cols = fk_match.group(1).strip()
                        source_columns = [col.strip().strip("'\"") for col in source_cols.split(',')]
                        current_foreign_key_columns.update(source_columns)
                
                # Second pass: extract foreign keys and reorganize
                table_content_clean = []
                for table_line in current_table_lines[1:]:
                    fk_match = re.match(r'\s*sa\.ForeignKeyConstraint\(\[([^\]]+)\],\s*\[([^\]]+)\](?:,\s*([^)]*))?\),?\s*$', table_line)
                    if fk_match:
                        source_cols = fk_match.group(1).strip()
                        target_cols = fk_match.group(2).strip()
                        options = fk_match.group(3) if fk_match.group(3) else ""
                        
                        # Parse source columns
                        source_columns = [col.strip().strip("'\"") for col in source_cols.split(',')]
                        
                        # Parse target columns
                        target_parts = target_cols.strip().strip("'\"").split('.')
                        if len(target_parts) == 2:
                            target_table = target_parts[0].strip("'\"")
                            target_columns = [target_parts[1].strip("'\"")]
                        else:
                            target_table = target_parts[0].strip("'\"") 
                            target_columns = [col.strip().strip("'\"") for col in target_cols.split(',')]
                            if '.' in target_columns[0]:
                                target_table = target_columns[0].split('.')[0]
                                target_columns = [col.split('.')[-1] for col in target_columns]
                        
                        # Parse ondelete option
                        ondelete = None
                        if options and 'ondelete=' in options:
                            ondelete_match = re.search(r"ondelete=(['\"]?)([^'\",\s)]+)\1", options)
                            if ondelete_match:
                                ondelete = ondelete_match.group(2)
                        
                        # Create foreign key definition
                        fk_name = f"fk_{current_table_name}_{'_'.join(source_columns)}"
                        
                        fk_def = {
                            'name': fk_name,
                            'source_table': current_table_name,
                            'target_table': target_table,
                            'source_columns': source_columns,
                            'target_columns': target_columns,
                            'ondelete': ondelete
                        }
                        
                        foreign_keys.append(fk_def)
                        # Skip this line (don't add to table_content_clean)
                    else:
                        table_content_clean.append(table_line)
                
                # Reorganize the table columns
                clean_table_content = '\n'.join(table_content_clean)
                reorganized_content = reorganize_table_columns(clean_table_content, current_table_name, current_foreign_key_columns)
                
                # Add the reorganized table to modified_lines
                modified_lines.append(current_table_lines[0])  # create_table line
                if reorganized_content.strip():
                    modified_lines.extend(reorganized_content.split('\n'))
                modified_lines.append(line)  # closing parenthesis
            else:
                # For lobs table, add as-is
                modified_lines.extend(current_table_lines)
                modified_lines.append(line)
            
            in_table_creation = False
            current_table_name = None
            current_table_lines = []
            current_foreign_key_columns = set()
            i += 1
            continue
        
        # Collect lines while in table creation
        if in_table_creation:
            current_table_lines.append(line)
            i += 1
            continue
        
        # Add all other lines unchanged
        modified_lines.append(line)
        i += 1
    
    # Join lines back together
    modified_content = '\n'.join(modified_lines)
    
    # Clean up any formatting issues
    modified_content = clean_whitespace_after_removal(modified_content)
    
    return modified_content, foreign_keys


def clean_whitespace_after_removal(content: str) -> str:
    """Clean up extra whitespace and formatting issues."""
    
    # Fix double commas
    content = re.sub(r',,+', ',', content)
    
    # Fix cases where removing ForeignKeyConstraint leaves extra commas or whitespace
    content = re.sub(r',\s*\n\s*\)', r'\n)', content)
    
    # Fix double newlines in table definitions
    content = re.sub(r'\n\s*\n\s*\)', r'\n)', content)
    
    # Fix cases where PrimaryKeyConstraint is on same line as column definition
    content = re.sub(r'(\w+\),)\s*(sa\.PrimaryKeyConstraint)', r'\1\n    \2', content)
    
    # Remove trailing commas before constraints
    content = re.sub(r',(\s*\n\s*sa\.(PrimaryKeyConstraint|UniqueConstraint|CheckConstraint))', r'\1', content)
    
    # Fix any trailing comma on the last column before closing parenthesis
    content = re.sub(r',(\s*\n\s*\))', r'\1', content)
    
    return content


def generate_foreign_key_commands(foreign_keys: List[Dict]) -> str:
    """Generate op.create_foreign_key commands for all extracted foreign keys."""
    
    commands = []
    commands.append("    # Add all foreign key constraints after all tables are created")
    
    for fk in foreign_keys:
        cmd = f"    op.create_foreign_key("
        cmd += f"'{fk['name']}', "
        cmd += f"'{fk['source_table']}', "
        cmd += f"'{fk['target_table']}', "
        cmd += f"{fk['source_columns']}, "
        cmd += f"{fk['target_columns']}"
        
        if fk['ondelete']:
            cmd += f", ondelete='{fk['ondelete']}'"
            
        cmd += ")"
        
        commands.append(cmd)
    
    return "\n".join(commands)


def generate_drop_foreign_key_commands(foreign_keys: List[Dict]) -> str:
    """Generate op.drop_constraint commands for downgrade function."""
    
    commands = []
    commands.append("    # Drop all foreign key constraints first")
    
    # Reverse order for dropping
    for fk in reversed(foreign_keys):
        cmd = f"    op.drop_constraint('{fk['name']}', '{fk['source_table']}', type_='foreignkey')"
        commands.append(cmd)
    
    return "\n".join(commands)


def refactor_migration_file(file_path: str, output_path: str = None):
    """
    Main function to refactor the migration file.
    """
    
    if output_path is None:
        output_path = file_path.replace('.py', '_refactored_v3.py')
    
    print(f"Reading migration file: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("Extracting foreign key constraints and reorganizing columns...")
    
    # Extract foreign keys and reorganize columns
    modified_content, foreign_keys = extract_foreign_keys_and_reorganize(content)
    
    print(f"Found {len(foreign_keys)} foreign key constraints to move")
    
    # Find where to insert the foreign key commands in upgrade function
    existing_fk_pattern = r"(\s+# Add (?:foreign key constraints|all foreign key constraints).*?(?:\n\s+op\.create_foreign_key.*?)*)"
    existing_match = re.search(existing_fk_pattern, modified_content, re.DOTALL)
    
    if existing_match:
        # Replace existing foreign key section
        new_fk_section = "\n" + generate_foreign_key_commands(foreign_keys) + "\n"
        modified_content = modified_content.replace(existing_match.group(1), new_fk_section)
    else:
        # Add before the end of upgrade function
        upgrade_end_pattern = r"(\s+# ### end Alembic commands ###)"
        upgrade_end_match = re.search(upgrade_end_pattern, modified_content)
        
        if upgrade_end_match:
            new_fk_section = "\n" + generate_foreign_key_commands(foreign_keys) + "\n\n"
            modified_content = modified_content.replace(
                upgrade_end_match.group(1), 
                new_fk_section + upgrade_end_match.group(1)
            )
    
    # Update downgrade function to drop the foreign keys first
    downgrade_pattern = r"(def downgrade\(\) -> None:.*?\n\s+\"\"\".*?\"\"\"\s*\n\s+# ### commands auto generated by Alembic - please adjust! ###\s*\n)"
    downgrade_match = re.search(downgrade_pattern, modified_content, re.DOTALL)
    
    if downgrade_match:
        # Check if there's already a foreign key drop section
        existing_drop_pattern = r"(\s+# Drop (?:foreign key constraints|all foreign key constraints).*?(?:\n\s+op\.drop_constraint.*?)*)"
        existing_drop_match = re.search(existing_drop_pattern, modified_content)
        
        if existing_drop_match:
            # Replace existing drop section
            new_drop_section = "\n" + generate_drop_foreign_key_commands(foreign_keys) + "\n"
            modified_content = modified_content.replace(existing_drop_match.group(1), new_drop_section)
        else:
            # Add drop commands at the beginning of downgrade
            new_drop_section = "\n" + generate_drop_foreign_key_commands(foreign_keys) + "\n"
            modified_content = modified_content.replace(
                downgrade_match.group(1),
                downgrade_match.group(1) + new_drop_section
            )
    
    print(f"Writing refactored migration to: {output_path}")
    
    with open(output_path, 'w') as f:
        f.write(modified_content)
    
    print("\nRefactoring completed!")
    print(f"✅ Moved {len(foreign_keys)} foreign key constraints to the end of upgrade function")
    print("✅ Reorganized columns in proper order: PK -> FK -> Business -> Audit/Timestamp")
    print("\nFirst 10 foreign keys moved:")
    for fk in foreign_keys[:10]:
        ondelete_info = f" (ondelete={fk['ondelete']})" if fk['ondelete'] else ""
        print(f"  - {fk['source_table']}.{fk['source_columns']} -> {fk['target_table']}.{fk['target_columns']}{ondelete_info}")
    
    if len(foreign_keys) > 10:
        print(f"  ... and {len(foreign_keys) - 10} more")
    
    print(f"\nReview the refactored file: {output_path}")
    print("If it looks correct, you can replace the original file.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python refactor_migration_v3.py <migration_file> [output_file]")
        print("\nThis script will:")
        print("1. Extract all foreign key constraints from table definitions")
        print("2. Reorganize columns in proper order: PK -> FK -> Business -> Audit/Timestamp") 
        print("3. Add all foreign keys at the end to avoid circular dependencies")
        print("\nExample:")
        print("python refactor_migration_v3.py alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models.py")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(migration_file).exists():
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    try:
        refactor_migration_file(migration_file, output_file)
    except Exception as e:
        print(f"Error refactoring migration file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()