#!/usr/bin/env python3
"""
Improved script to refactor Alembic migration file to handle circular dependencies.

This script:
1. Parses the migration file 
2. Extracts ALL ForeignKeyConstraint lines from table creation statements
3. Creates all tables without these foreign key constraints  
4. Adds ALL foreign keys at the end using op.create_foreign_key()

This pattern eliminates circular dependency issues completely.
"""

import re
import sys
from typing import List, Tuple, Dict
from pathlib import Path


def clean_whitespace_after_removal(content: str) -> str:
    """Clean up extra whitespace and formatting issues after removing foreign keys."""
    
    # Fix cases where removing ForeignKeyConstraint leaves extra commas or whitespace
    # Pattern: comma followed by only whitespace and closing parenthesis  
    content = re.sub(r',\s*\n\s*\)', r'\n)', content)
    
    # Fix double newlines in table definitions
    content = re.sub(r'\n\s*\n\s*\)', r'\n)', content)
    
    # Fix cases where PrimaryKeyConstraint is on same line as column definition
    content = re.sub(r'(\w+\),)\s*(sa\.PrimaryKeyConstraint)', r'\1\n    \2', content)
    
    return content


def extract_foreign_keys_from_table_creation(content: str) -> Tuple[str, List[Dict]]:
    """
    Extract foreign key constraints from table creation statements.
    
    Returns:
        - Modified content with ForeignKeyConstraint lines removed
        - List of foreign key definitions to add at the end
    """
    
    foreign_keys = []
    lines = content.split('\n')
    modified_lines = []
    
    in_table_creation = False
    current_table_name = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if we're starting a new table creation
        table_match = re.match(r"\s*op\.create_table\('([^']+)',", line)
        if table_match:
            in_table_creation = True
            current_table_name = table_match.group(1)
            modified_lines.append(line)
            i += 1
            continue
        
        # Check if we're ending table creation
        if in_table_creation and re.match(r'\s*\)\s*$', line):
            in_table_creation = False
            current_table_name = None
            modified_lines.append(line)
            i += 1
            continue
        
        # Check for ForeignKeyConstraint within table creation (skip lobs table)
        if in_table_creation and current_table_name != 'lobs':
            fk_match = re.match(r'\s*sa\.ForeignKeyConstraint\(\[([^\]]+)\],\s*\[([^\]]+)\](?:,\s*([^)]*))?\),?\s*$', line)
            if fk_match:
                source_cols = fk_match.group(1).strip()
                target_cols = fk_match.group(2).strip()
                options = fk_match.group(3) if fk_match.group(3) else ""
                
                # Parse source columns (remove quotes)
                source_columns = [col.strip().strip("'\"") for col in source_cols.split(',')]
                
                # Parse target columns - extract table and column names
                target_parts = target_cols.strip().strip("'\"").split('.')
                if len(target_parts) == 2:
                    target_table = target_parts[0].strip("'\"")
                    target_columns = [target_parts[1].strip("'\"")]
                else:
                    # Handle edge cases
                    target_table = target_parts[0].strip("'\"") 
                    target_columns = [col.strip().strip("'\"") for col in target_cols.split(',')]
                    if '.' in target_columns[0]:
                        target_table = target_columns[0].split('.')[0]
                        target_columns = [col.split('.')[-1] for col in target_columns]
                
                # Parse additional options like ondelete
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
                
                # Skip this line (don't add to modified_lines)
                i += 1
                continue
        
        # Add all other lines unchanged
        modified_lines.append(line)
        i += 1
    
    # Join lines back together and clean up formatting
    modified_content = '\n'.join(modified_lines)
    modified_content = clean_whitespace_after_removal(modified_content)
    
    return modified_content, foreign_keys


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
        output_path = file_path.replace('.py', '_refactored_v2.py')
    
    print(f"Reading migration file: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("Extracting foreign key constraints...")
    
    # Extract foreign keys from table creation statements
    modified_content, foreign_keys = extract_foreign_keys_from_table_creation(content)
    
    print(f"Found {len(foreign_keys)} foreign key constraints to move")
    
    # Find where to insert the foreign key commands in upgrade function
    # Look for the existing foreign key additions or the end of upgrade function
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
    print(f"Moved {len(foreign_keys)} foreign key constraints to the end of upgrade function")
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
        print("Usage: python refactor_migration_v2.py <migration_file> [output_file]")
        print("\nExample:")
        print("python refactor_migration_v2.py alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models.py")
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