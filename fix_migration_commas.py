#!/usr/bin/env python3
"""
Fix missing commas in migration file before constraints.
"""

import re


def fix_missing_commas(input_file: str, output_file: str):
    """Fix missing commas before constraint definitions."""
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Pattern to find column lines followed by constraint lines without comma
    # This will match a column definition line that doesn't end with comma,
    # followed by a constraint line (PrimaryKeyConstraint, UniqueConstraint, etc)
    pattern = r"(sa\.Column\([^)]+\))\s*\n\s*(sa\.(?:PrimaryKeyConstraint|UniqueConstraint|CheckConstraint|ForeignKeyConstraint))"
    
    # Replace with comma added
    def add_comma(match):
        column_line = match.group(1)
        constraint_line = match.group(2)
        return f"{column_line},\n    {constraint_line}"
    
    # Fix the content
    fixed_content = re.sub(pattern, add_comma, content)
    
    # Write the fixed content
    with open(output_file, 'w') as f:
        f.write(fixed_content)
    
    print(f"✅ Fixed missing commas in {output_file}")


if __name__ == "__main__":
    input_file = "/Users/dineshpatel/code/projects/SynapseDTE2/alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models.py"
    output_file = "/Users/dineshpatel/code/projects/SynapseDTE2/alembic/versions/2025_08_04_1041-9b46a58d423b_initial_migration_from_all_models_fixed.py"
    
    fix_missing_commas(input_file, output_file)