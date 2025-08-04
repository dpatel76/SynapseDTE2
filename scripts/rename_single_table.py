#!/usr/bin/env python3
"""
Script to rename a single table and update all its references.
This handles:
1. Updating the model's __tablename__
2. Updating all ForeignKey references
3. Updating all relationship back_populates
4. Creating migration script
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
import json


class TableRenamer:
    def __init__(self, project_root: str, old_name: str, new_name: str):
        self.project_root = Path(project_root)
        self.old_name = old_name
        self.new_name = new_name
        self.changes_made = []
        self.files_modified = set()
        
    def rename(self):
        """Execute the complete rename process"""
        print(f"\nRenaming table '{self.old_name}' to '{self.new_name}'")
        print("=" * 60)
        
        # 1. Update model's __tablename__
        self.update_tablename_definition()
        
        # 2. Update all ForeignKey references
        self.update_foreign_key_references()
        
        # 3. Update relationship references if needed
        self.update_relationship_references()
        
        # 4. Update models and queries
        self.update_models_and_queries()
        
        # 5. Create migration script
        self.create_migration_script()
        
        # 6. Generate report
        self.generate_report()
        
    def update_tablename_definition(self):
        """Find and update the __tablename__ definition"""
        print("\n1. Updating __tablename__ definition...")
        
        pattern = re.compile(rf'__tablename__\s*=\s*["\']({re.escape(self.old_name)})["\']')
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                new_content = content
                
                if pattern.search(content):
                    new_content = pattern.sub(f'__tablename__ = "{self.new_name}"', content)
                    
                    if new_content != content:
                        py_file.write_text(new_content)
                        self.files_modified.add(py_file)
                        self.changes_made.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "change": f"Updated __tablename__ from '{self.old_name}' to '{self.new_name}'"
                        })
                        print(f"  ✓ Updated {py_file.relative_to(self.project_root)}")
                        
            except Exception as e:
                print(f"  ✗ Error updating {py_file}: {e}")
                
    def update_foreign_key_references(self):
        """Update all ForeignKey references to this table"""
        print("\n2. Updating ForeignKey references...")
        
        # Pattern to match ForeignKey("table.column")
        pattern = re.compile(rf'ForeignKey\s*\(\s*["\']({re.escape(self.old_name)})\.([^"\']+)["\']')
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                new_content = content
                
                matches = list(pattern.finditer(content))
                if matches:
                    for match in reversed(matches):  # Process in reverse to maintain positions
                        old_ref = match.group(0)
                        column = match.group(2)
                        new_ref = f'ForeignKey("{self.new_name}.{column}"'
                        
                        new_content = new_content[:match.start()] + new_ref + new_content[match.end():]
                    
                    if new_content != content:
                        py_file.write_text(new_content)
                        self.files_modified.add(py_file)
                        self.changes_made.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "change": f"Updated {len(matches)} ForeignKey references"
                        })
                        print(f"  ✓ Updated {len(matches)} references in {py_file.relative_to(self.project_root)}")
                        
            except Exception as e:
                print(f"  ✗ Error updating {py_file}: {e}")
                
    def update_relationship_references(self):
        """Update relationship references if table name is used in relationships"""
        print("\n3. Checking relationship references...")
        
        # This is more complex as relationships might reference the model class name
        # not the table name. Log for manual review.
        
        pattern = re.compile(rf'relationship\s*\([^)]*["\'].*{re.escape(self.old_name)}.*["\'][^)]*\)')
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                matches = list(pattern.finditer(content))
                
                if matches:
                    print(f"  ⚠️  Found {len(matches)} potential relationship references in {py_file.relative_to(self.project_root)}")
                    print("     These may need manual review")
                    
            except Exception as e:
                pass
    def update_models_and_queries(self):
        """Call the update_models_and_queries script"""
        print("\n4. Updating models and queries...")
        
        import subprocess
        script_path = Path(__file__).parent / "update_models_and_queries.py"
        cmd = [
            sys.executable, str(script_path),
            "--old-name", self.old_name,
            "--new-name", self.new_name,
            "--project-root", str(self.project_root)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✓ Models and queries updated successfully")
            self.changes_made.append({
                "file": "Multiple files",
                "change": "Updated models and queries"
            })
        else:
            print(f"  ✗ Error updating models and queries: {result.stderr}")
                
    def create_migration_script(self):
        """Create Alembic migration script"""
        print("\n5. Creating migration script...")
        
        timestamp = Path.cwd().name  # Simple timestamp
        migration_name = f"rename_{self.old_name}_to_{self.new_name}"
        
        migration_content = f'''"""Rename {self.old_name} to {self.new_name}

Revision ID: auto_generated
Revises: 
Create Date: {timestamp}
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'auto_generated'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Rename table
    op.rename_table('{self.old_name}', '{self.new_name}')
    
    # Update any views, stored procedures, etc. that reference the old name
    # Add custom SQL here if needed


def downgrade():
    # Rename back
    op.rename_table('{self.new_name}', '{self.old_name}')
'''
        
        migrations_dir = self.project_root / "alembic" / "versions"
        migrations_dir.mkdir(parents=True, exist_ok=True)
        
        migration_file = migrations_dir / f"{migration_name}.py"
        migration_file.write_text(migration_content)
        
        self.changes_made.append({
            "file": str(migration_file.relative_to(self.project_root)),
            "change": "Created migration script"
        })
        print(f"  ✓ Created migration: {migration_file.name}")
        
    def generate_report(self):
        """Generate a report of all changes made"""
        print("\n6. Generating report...")
        
        report = {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "files_modified": len(self.files_modified),
            "changes": self.changes_made
        }
        
        report_file = self.project_root / f"rename_{self.old_name}_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n✓ Report saved to: {report_file.name}")
        print(f"\nSummary:")
        print(f"  - Files modified: {len(self.files_modified)}")
        print(f"  - Total changes: {len(self.changes_made)}")
        
        # Also create a SQL script for manual execution if needed
        sql_file = self.project_root / f"rename_{self.old_name}.sql"
        sql_content = f"""-- SQL script to rename {self.old_name} to {self.new_name}

-- Rename the table
ALTER TABLE {self.old_name} RENAME TO {self.new_name};

-- Update any dependent views, functions, etc.
-- Add custom SQL here as needed

-- To rollback:
-- ALTER TABLE {self.new_name} RENAME TO {self.old_name};
"""
        sql_file.write_text(sql_content)
        print(f"  - SQL script: {sql_file.name}")


def main():
    parser = argparse.ArgumentParser(description="Rename a database table and update all references")
    parser.add_argument("--old-name", required=True, help="Current table name")
    parser.add_argument("--new-name", required=True, help="New table name")
    parser.add_argument("--project-root", default="/Users/dineshpatel/code/projects/SynapseDTE", 
                       help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        # TODO: Implement dry run logic
        return
    
    renamer = TableRenamer(args.project_root, args.old_name, args.new_name)
    renamer.rename()


if __name__ == "__main__":
    main()