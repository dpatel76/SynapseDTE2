#!/usr/bin/env python3
"""
Script to update SQLAlchemy models and queries after table renaming.
This handles:
1. Updating model class names if needed
2. Updating relationship definitions
3. Updating query references in services
4. Updating raw SQL queries
5. Updating API endpoint queries
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set
import json


class ModelAndQueryUpdater:
    def __init__(self, project_root: str, old_name: str, new_name: str):
        self.project_root = Path(project_root)
        self.old_name = old_name
        self.new_name = new_name
        self.changes_made = []
        self.files_modified = set()
        
        # Derive model class names from table names
        self.old_model_name = self._table_to_model_name(old_name)
        self.new_model_name = self._table_to_model_name(new_name)
        
    def _table_to_model_name(self, table_name: str) -> str:
        """Convert table_name to ModelName"""
        # Special cases mapping
        special_cases = {
            "cycle_report_planning_attributes": "ReportAttribute",
            "data_owner_assignments": "DataOwnerAssignment",
            "cycle_report_sample_selection_samples": "Sample",
            "cycle_report_data_profiling_rules": "ProfilingRule",
            # Add more mappings as needed
        }
        
        if table_name in special_cases:
            return special_cases[table_name]
            
        # General conversion: table_name -> TableName
        parts = table_name.split('_')
        return ''.join(word.capitalize() for word in parts)
        
    def update_all(self):
        """Execute all updates"""
        print(f"\nUpdating models and queries for: {self.old_name} → {self.new_name}")
        print("=" * 60)
        
        # 1. Update relationship back_populates
        self.update_relationship_back_populates()
        
        # 2. Update query references in services
        self.update_service_queries()
        
        # 3. Update API endpoint queries
        self.update_api_queries()
        
        # 4. Update raw SQL queries
        self.update_raw_sql_queries()
        
        # 5. Update imports if model name changed
        if self.old_model_name != self.new_model_name:
            self.update_model_imports()
            
        # 6. Generate report
        self.generate_report()
        
    def update_relationship_back_populates(self):
        """Update relationship back_populates references"""
        print("\n1. Updating relationship back_populates...")
        
        # Find all files with relationship definitions
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                original_content = content
                
                # Pattern to find relationships that might reference our table
                # Look for back_populates="something" where something might be derived from table name
                patterns = [
                    # Direct table name reference
                    (rf'back_populates\s*=\s*["\']({re.escape(self.old_name)})["\']',
                     f'back_populates="{self.new_name}"'),
                    
                    # Pluralized form
                    (rf'back_populates\s*=\s*["\']({re.escape(self.old_name)}s?)["\']',
                     lambda m: f'back_populates="{self.new_name}s"' if m.group(1).endswith('s') else f'back_populates="{self.new_name}"'),
                    
                    # Model-based reference (e.g., "report_attributes" from ReportAttribute)
                    # This is more complex and needs the model mapping
                ]
                
                for pattern, replacement in patterns:
                    if isinstance(replacement, str):
                        content = re.sub(pattern, replacement, content)
                    else:
                        content = re.sub(pattern, replacement, content)
                        
                if content != original_content:
                    py_file.write_text(content)
                    self.files_modified.add(py_file)
                    self.changes_made.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "change": "Updated relationship back_populates"
                    })
                    print(f"  ✓ Updated {py_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                print(f"  ✗ Error updating {py_file}: {e}")
                
    def update_service_queries(self):
        """Update query references in service files"""
        print("\n2. Updating service layer queries...")
        
        services_dir = self.project_root / "app" / "services"
        if not services_dir.exists():
            return
            
        for py_file in services_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                original_content = content
                
                # Update query references
                # Pattern 1: Direct model references (e.g., DataOwnerAssignment.query)
                if self.old_model_name != self.new_model_name:
                    content = re.sub(
                        rf'\b{re.escape(self.old_model_name)}\b',
                        self.new_model_name,
                        content
                    )
                
                # Pattern 2: String-based table references in raw SQL
                content = re.sub(
                    rf'["\']({re.escape(self.old_name)})["\']',
                    f'"{self.new_name}"',
                    content
                )
                
                # Pattern 3: f-string table references
                content = re.sub(
                    rf'FROM\s+{re.escape(self.old_name)}\b',
                    f'FROM {self.new_name}',
                    content,
                    flags=re.IGNORECASE
                )
                
                content = re.sub(
                    rf'JOIN\s+{re.escape(self.old_name)}\b',
                    f'JOIN {self.new_name}',
                    content,
                    flags=re.IGNORECASE
                )
                
                if content != original_content:
                    py_file.write_text(content)
                    self.files_modified.add(py_file)
                    self.changes_made.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "change": "Updated service queries"
                    })
                    print(f"  ✓ Updated {py_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                print(f"  ✗ Error updating {py_file}: {e}")
                
    def update_api_queries(self):
        """Update queries in API endpoints"""
        print("\n3. Updating API endpoint queries...")
        
        api_dir = self.project_root / "app" / "api"
        if not api_dir.exists():
            return
            
        for py_file in api_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                original_content = content
                
                # Update model imports
                if self.old_model_name != self.new_model_name:
                    # Update import statements
                    content = re.sub(
                        rf'from\s+app\.models\.[a-z_]+\s+import\s+.*\b{re.escape(self.old_model_name)}\b',
                        lambda m: m.group(0).replace(self.old_model_name, self.new_model_name),
                        content
                    )
                    
                    # Update model usage
                    content = re.sub(
                        rf'\b{re.escape(self.old_model_name)}\b',
                        self.new_model_name,
                        content
                    )
                
                # Update any string references to table names
                content = re.sub(
                    rf'["\']({re.escape(self.old_name)})["\']',
                    f'"{self.new_name}"',
                    content
                )
                
                if content != original_content:
                    py_file.write_text(content)
                    self.files_modified.add(py_file)
                    self.changes_made.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "change": "Updated API queries"
                    })
                    print(f"  ✓ Updated {py_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                print(f"  ✗ Error updating {py_file}: {e}")
                
    def update_raw_sql_queries(self):
        """Update raw SQL queries"""
        print("\n4. Updating raw SQL queries...")
        
        # Look for SQL files and Python files with raw SQL
        sql_patterns = [
            f"FROM {self.old_name}",
            f"JOIN {self.old_name}",
            f"INTO {self.old_name}",
            f"UPDATE {self.old_name}",
            f"DELETE FROM {self.old_name}",
            f"REFERENCES {self.old_name}",
            f"ALTER TABLE {self.old_name}",
            f"DROP TABLE {self.old_name}",
            f"CREATE TABLE {self.old_name}",
        ]
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.sql', '.py']:
                if "venv" in str(file_path) or "__pycache__" in str(file_path):
                    continue
                    
                try:
                    content = file_path.read_text()
                    original_content = content
                    
                    # Replace SQL patterns
                    for pattern in sql_patterns:
                        # Case insensitive replacement
                        content = re.sub(
                            re.escape(pattern),
                            pattern.replace(self.old_name, self.new_name),
                            content,
                            flags=re.IGNORECASE
                        )
                    
                    # Also check for quoted table names
                    content = re.sub(
                        rf'"({re.escape(self.old_name)})"',
                        f'"{self.new_name}"',
                        content
                    )
                    
                    if content != original_content:
                        file_path.write_text(content)
                        self.files_modified.add(file_path)
                        self.changes_made.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "change": "Updated raw SQL queries"
                        })
                        print(f"  ✓ Updated {file_path.relative_to(self.project_root)}")
                        
                except Exception as e:
                    if "venv" not in str(e):
                        print(f"  ✗ Error updating {file_path}: {e}")
                        
    def update_model_imports(self):
        """Update import statements if model name changed"""
        print("\n5. Updating model imports...")
        
        # Update __init__.py
        init_file = self.project_root / "app" / "models" / "__init__.py"
        if init_file.exists():
            try:
                content = init_file.read_text()
                original_content = content
                
                # Update import statements
                content = re.sub(
                    rf'\b{re.escape(self.old_model_name)}\b',
                    self.new_model_name,
                    content
                )
                
                if content != original_content:
                    init_file.write_text(content)
                    self.files_modified.add(init_file)
                    self.changes_made.append({
                        "file": str(init_file.relative_to(self.project_root)),
                        "change": "Updated model imports in __init__.py"
                    })
                    print(f"  ✓ Updated {init_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                print(f"  ✗ Error updating {init_file}: {e}")
                
    def generate_report(self):
        """Generate report of all changes"""
        print("\n6. Generating report...")
        
        report = {
            "old_table_name": self.old_name,
            "new_table_name": self.new_name,
            "old_model_name": self.old_model_name,
            "new_model_name": self.new_model_name,
            "files_modified": len(self.files_modified),
            "changes": self.changes_made
        }
        
        report_file = self.project_root / f"update_models_{self.old_name}_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n✓ Report saved to: {report_file.name}")
        print(f"\nSummary:")
        print(f"  - Files modified: {len(self.files_modified)}")
        print(f"  - Total changes: {len(self.changes_made)}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Update models and queries after table renaming")
    parser.add_argument("--old-name", required=True, help="Old table name")
    parser.add_argument("--new-name", required=True, help="New table name")
    parser.add_argument("--project-root", default="/Users/dineshpatel/code/projects/SynapseDTE")
    
    args = parser.parse_args()
    
    updater = ModelAndQueryUpdater(args.project_root, args.old_name, args.new_name)
    updater.update_all()


if __name__ == "__main__":
    main()