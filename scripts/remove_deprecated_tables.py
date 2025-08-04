#!/usr/bin/env python3
"""
Script to remove deprecated tables that should use universal frameworks.
This handles:
1. Removing model files or commenting out models
2. Removing all ForeignKey references
3. Removing all relationship references
4. Creating migration to drop tables
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict
import json


# Tables to be removed
DEPRECATED_TABLES = {
    # Phase status tables (use universal status)
    "data_profiling_phases": "Use universal phase status framework",
    "sample_selection_phases": "Use universal phase status framework",
    "test_execution_phases": "Use universal phase status framework", 
    "observation_management_phases": "Use universal phase status framework",
    "test_report_phases": "Use universal phase status framework",
    "cycle_report_request_info_phases": "Use universal phase status framework",
    
    # Sample sets (no longer used)
    "cycle_report_sample_sets": "Sample sets concept removed",
    
    # Data owner specific (use universal frameworks)
    "data_owner_sla_violations": "Use universal SLA framework",
    "data_owner_escalation_log": "Use universal escalation framework",
    "data_owner_notifications": "Use universal assignments framework",
}


class TableRemover:
    def __init__(self, project_root: str, table_name: str):
        self.project_root = Path(project_root)
        self.table_name = table_name
        self.reason = DEPRECATED_TABLES.get(table_name, "Deprecated")
        self.changes_made = []
        self.files_modified = set()
        
    def remove(self):
        """Execute the complete removal process"""
        print(f"\nRemoving deprecated table '{self.table_name}'")
        print(f"Reason: {self.reason}")
        print("=" * 60)
        
        # 1. Find and comment out model definition
        self.comment_out_model()
        
        # 2. Remove/comment foreign key references
        self.remove_foreign_key_references()
        
        # 3. Remove/comment relationship references
        self.remove_relationship_references()
        
        # 4. Remove from model imports
        self.remove_from_imports()
        
        # 5. Create migration script
        self.create_migration_script()
        
        # 6. Generate report
        self.generate_report()
        
    def comment_out_model(self):
        """Find and comment out the model class definition"""
        print("\n1. Commenting out model definition...")
        
        # Find files containing the table definition
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Look for __tablename__ = "table_name"
                if f'__tablename__ = "{self.table_name}"' in content:
                    print(f"  Found model in {py_file.relative_to(self.project_root)}")
                    
                    # Find the class definition
                    lines = content.split('\n')
                    new_lines = []
                    in_class = False
                    class_indent = None
                    
                    for i, line in enumerate(lines):
                        if f'__tablename__ = "{self.table_name}"' in line:
                            # Find the class definition above
                            for j in range(i, -1, -1):
                                if lines[j].strip().startswith('class '):
                                    in_class = True
                                    class_indent = len(lines[j]) - len(lines[j].lstrip())
                                    # Add deprecation comment
                                    new_lines.append(f"# DEPRECATED: {self.reason}")
                                    new_lines.append(f"# {lines[j]}")
                                    break
                        elif in_class:
                            if line.strip() and not line[class_indent:class_indent+1].isspace() and line.strip()[0] not in ['#', '"', "'"]:
                                # End of class
                                in_class = False
                                new_lines.append(line)
                            else:
                                # Comment out class content
                                new_lines.append(f"# {line}" if line.strip() else line)
                        else:
                            new_lines.append(line)
                    
                    if new_lines != lines:
                        py_file.write_text('\n'.join(new_lines))
                        self.files_modified.add(py_file)
                        self.changes_made.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "change": f"Commented out model class for {self.table_name}"
                        })
                        print(f"  ✓ Commented out model in {py_file.relative_to(self.project_root)}")
                        
            except Exception as e:
                print(f"  ✗ Error processing {py_file}: {e}")
                
    def remove_foreign_key_references(self):
        """Remove or comment out foreign key references"""
        print("\n2. Removing ForeignKey references...")
        
        pattern = re.compile(rf'(\s*)(.*)ForeignKey\s*\(\s*["\']({re.escape(self.table_name)})\.([^"\']+)["\']\s*\)(.*)')
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                lines = content.split('\n')
                new_lines = []
                modified = False
                
                for line in lines:
                    match = pattern.match(line)
                    if match:
                        indent = match.group(1)
                        new_lines.append(f"{indent}# DEPRECATED: {self.reason}")
                        new_lines.append(f"{indent}# {line.strip()}")
                        modified = True
                        print(f"  Found FK reference in {py_file.relative_to(self.project_root)}")
                    else:
                        new_lines.append(line)
                
                if modified:
                    py_file.write_text('\n'.join(new_lines))
                    self.files_modified.add(py_file)
                    self.changes_made.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "change": f"Commented out ForeignKey references to {self.table_name}"
                    })
                    
            except Exception as e:
                print(f"  ✗ Error processing {py_file}: {e}")
                
    def remove_relationship_references(self):
        """Remove or comment out relationship references"""
        print("\n3. Removing relationship references...")
        
        # Look for relationships that might reference this table
        count = 0
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Simple check for table name in relationships
                if self.table_name in content and 'relationship(' in content:
                    print(f"  ⚠️  Potential relationship reference in {py_file.relative_to(self.project_root)}")
                    count += 1
                    
            except Exception as e:
                pass
                
        if count > 0:
            print(f"  Found {count} files with potential relationship references - manual review needed")
            
    def remove_from_imports(self):
        """Remove from __init__.py imports"""
        print("\n4. Removing from model imports...")
        
        init_file = self.project_root / "app" / "models" / "__init__.py"
        if init_file.exists():
            try:
                content = init_file.read_text()
                lines = content.split('\n')
                new_lines = []
                
                for line in lines:
                    # Comment out lines that might import this table's model
                    if any(name in line for name in ['Phase', 'SampleSet', 'SLAViolation', 'EscalationLog']):
                        new_lines.append(f"# DEPRECATED: {line}")
                    else:
                        new_lines.append(line)
                
                if new_lines != lines:
                    init_file.write_text('\n'.join(new_lines))
                    self.files_modified.add(init_file)
                    self.changes_made.append({
                        "file": str(init_file.relative_to(self.project_root)),
                        "change": "Commented out model imports"
                    })
                    print(f"  ✓ Updated model imports")
                    
            except Exception as e:
                print(f"  ✗ Error updating imports: {e}")
                
    def create_migration_script(self):
        """Create migration to drop the table"""
        print("\n5. Creating migration script...")
        
        migration_content = f'''"""Drop deprecated table {self.table_name}

Revision ID: drop_{self.table_name}
Revises: 
Create Date: auto
Reason: {self.reason}
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'drop_{self.table_name}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Drop the deprecated table
    op.drop_table('{self.table_name}')
    
    # Note: {self.reason}


def downgrade():
    # Recreate table if needed for rollback
    # This would need the full table definition
    pass
'''
        
        migrations_dir = self.project_root / "alembic" / "versions"
        migrations_dir.mkdir(parents=True, exist_ok=True)
        
        migration_file = migrations_dir / f"drop_{self.table_name}.py"
        migration_file.write_text(migration_content)
        
        self.changes_made.append({
            "file": str(migration_file.relative_to(self.project_root)),
            "change": "Created migration to drop table"
        })
        print(f"  ✓ Created migration: {migration_file.name}")
        
    def generate_report(self):
        """Generate report of changes"""
        print("\n6. Generating report...")
        
        report = {
            "table_name": self.table_name,
            "reason": self.reason,
            "files_modified": len(self.files_modified),
            "changes": self.changes_made
        }
        
        report_file = self.project_root / f"remove_{self.table_name}_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n✓ Report saved to: {report_file.name}")
        print(f"\nSummary:")
        print(f"  - Files modified: {len(self.files_modified)}")
        print(f"  - Total changes: {len(self.changes_made)}")


def main():
    parser = argparse.ArgumentParser(description="Remove deprecated database tables")
    parser.add_argument("--table", help="Specific table to remove")
    parser.add_argument("--all", action="store_true", help="Remove all deprecated tables")
    parser.add_argument("--project-root", default="/Users/dineshpatel/code/projects/SynapseDTE", 
                       help="Project root directory")
    
    args = parser.parse_args()
    
    if args.all:
        print(f"Removing all {len(DEPRECATED_TABLES)} deprecated tables...")
        for table_name in DEPRECATED_TABLES:
            remover = TableRemover(args.project_root, table_name)
            remover.remove()
            print("\n" + "="*60 + "\n")
    elif args.table:
        if args.table not in DEPRECATED_TABLES:
            print(f"Error: '{args.table}' is not in the list of deprecated tables")
            print(f"Available tables: {', '.join(DEPRECATED_TABLES.keys())}")
            return
        remover = TableRemover(args.project_root, args.table)
        remover.remove()
    else:
        print("Please specify --table or --all")
        print(f"Deprecated tables: {', '.join(DEPRECATED_TABLES.keys())}")


if __name__ == "__main__":
    main()