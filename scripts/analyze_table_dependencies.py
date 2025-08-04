#!/usr/bin/env python3
"""
Analyze all table dependencies in the codebase to prepare for table renaming.
This script will find:
1. All foreign key references
2. All relationship definitions
3. All string references to table names
4. All migration files referencing tables
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Define current table names that need to be renamed
TABLES_TO_RENAME = {
    # Planning Phase
    "cycle_report_planning_attributes": "cycle_report_planning_attributes",
    "cycle_report_planning_attribute_version_history": "cycle_report_planning_attribute_version_history",
    "attribute_version_change_logs": "cycle_report_planning_attribute_change_logs",
    "attribute_version_comparisons": "cycle_report_planning_attribute_comparisons",
    
    # Scoping Phase
    "cycle_report_scoping_attribute_recommendations": "cycle_report_scoping_attribute_recommendations",
    "cycle_report_scoping_tester_decisions": "cycle_report_scoping_tester_decisions",
    "cycle_report_scoping_report_owner_reviews": "cycle_report_scoping_report_owner_reviews",
    "scoping_audit_log": "cycle_report_scoping_audit_logs",
    
    # Data Profiling Phase
    "cycle_report_data_profiling_files": "cycle_report_data_profiling_files",
    "cycle_report_data_profiling_rules": "cycle_report_data_profiling_dq_rules",
    "cycle_report_data_profiling_results": "cycle_report_data_profiling_dq_results",
    "cycle_report_data_profiling_attribute_scores": "cycle_report_data_profiling_attribute_dq_scores",
    "cycle_report_attribute_profile_results": "cycle_report_data_profiling_attribute_results",
    "cycle_report_anomaly_patterns_data_profiling": "cycle_report_data_profiling_anomaly_patterns",
    
    # Data Owner Phase
    "attribute_lob_assignments": "cycle_report_data_owner_attribute_lob_assignments",
    "data_owner_assignments": "cycle_report_data_owner_assignments",
    "historical_data_owner_assignments": "cycle_report_data_owner_assignments_history",
    "data_owner_phase_audit_log": "cycle_report_data_owner_activity_logs",
    
    # Sample Selection Phase
    "cycle_report_sample_records": "cycle_report_sample_selection_records",
    "sample_validation_results": "cycle_report_sample_selection_validation_results",
    "sample_validation_issues": "cycle_report_sample_selection_validation_issues",
    "sample_approval_history": "cycle_report_sample_selection_approval_history",
    "llm_sample_generations": "cycle_report_sample_selection_llm_generations",
    "sample_upload_history": "cycle_report_sample_selection_upload_history",
    "sample_selection_audit_log": "cycle_report_sample_selection_audit_logs",
    
    # Request Info Phase
    "cycle_report_test_cases": "cycle_report_request_info_test_cases",
    "document_submissions": "cycle_report_request_info_document_submissions",
    "request_info_audit_log": "cycle_report_request_info_audit_logs",
    
    # Test Execution Phase
    "cycle_report_test_executions": "cycle_report_test_execution_executions",
    "cycle_report_sample_selection_samples": "cycle_report_test_execution_sample_data",
    "cycle_report_test_execution_document_analyses": "cycle_report_test_execution_document_analyses",
    "cycle_report_test_execution_database_tests": "cycle_report_test_execution_database_tests",
    "test_result_reviews": "cycle_report_test_execution_result_reviews",
    "test_comparisons": "cycle_report_test_execution_comparisons",
    "bulk_test_executions": "cycle_report_test_execution_bulk_executions",
    "test_execution_audit_logs": "cycle_report_test_execution_audit_logs",
    
    # Observation Management Phase
    "cycle_report_observation_mgmt_observation_records": "cycle_report_observation_mgmt_observations",
    "observation_groups": "cycle_report_observation_mgmt_groups",
    "observation_clarifications": "cycle_report_observation_mgmt_clarifications",
    "cycle_report_observation_mgmt_impact_assessments": "cycle_report_observation_mgmt_impact_assessments",
    "cycle_report_observation_mgmt_approvals": "cycle_report_observation_mgmt_approvals",
    "cycle_report_observation_mgmt_resolutions": "cycle_report_observation_mgmt_resolutions",
    "observation_management_audit_logs": "cycle_report_observation_mgmt_audit_logs",
    "cycle_report_observations": "cycle_report_observation_mgmt_observations",
    
    # Test Report Phase
    "cycle_report_test_report_sections": "cycle_report_test_report_sections",
    "document_revisions": "cycle_report_test_report_document_revisions",
    
    # PDEs (moving to planning)
    "cycle_report_pde_mappings": "cycle_report_planning_pde_mappings",
    "cycle_report_pde_classifications": "cycle_report_planning_pde_classifications",
    "cycle_report_data_sources": "cycle_report_planning_data_sources",
    "cycle_report_planning_pde_mapping_reviews": "cycle_report_planning_pde_mapping_reviews",
    "cycle_report_planning_pde_mapping_review_history": "cycle_report_planning_pde_mapping_review_history",
    "cycle_report_planning_pde_mapping_approval_rules": "cycle_report_planning_pde_mapping_approval_rules",
}

# Tables to remove completely
TABLES_TO_REMOVE = {
    "data_profiling_phases",
    "sample_selection_phases", 
    "test_execution_phases",
    "observation_management_phases",
    "test_report_phases",
    "cycle_report_request_info_phases",
    "cycle_report_sample_sets",
    "data_owner_sla_violations",
    "data_owner_escalation_log",
    "data_owner_notifications",
}


class TableDependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies = defaultdict(lambda: {
            "foreign_keys": [],
            "relationships": [],
            "string_references": [],
            "migrations": []
        })
        
    def analyze(self):
        """Run all analysis steps"""
        print("Starting dependency analysis...")
        self.find_foreign_keys()
        self.find_relationships()
        self.find_string_references()
        self.find_migration_references()
        self.generate_report()
        
    def find_foreign_keys(self):
        """Find all ForeignKey references to tables"""
        print("\nSearching for foreign key references...")
        
        pattern = re.compile(r'ForeignKey\s*\(\s*["\']([^"\']+)\.([^"\']+)["\']')
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                for match in pattern.finditer(content):
                    table_name = match.group(1)
                    column_name = match.group(2)
                    
                    if table_name in TABLES_TO_RENAME or table_name in TABLES_TO_REMOVE:
                        line_no = content[:match.start()].count('\n') + 1
                        self.dependencies[table_name]["foreign_keys"].append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_no,
                            "column": column_name,
                            "full_reference": match.group(0)
                        })
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
                
    def find_relationships(self):
        """Find all relationship() references"""
        print("\nSearching for relationship references...")
        
        # Pattern for back_populates and backref
        patterns = [
            re.compile(r'relationship\s*\([^)]*back_populates\s*=\s*["\']([^"\']+)["\']'),
            re.compile(r'relationship\s*\([^)]*backref\s*=\s*["\']([^"\']+)["\']'),
        ]
        
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Also look for __tablename__ definitions to map relationships
                tablename_pattern = re.compile(r'__tablename__\s*=\s*["\']([^"\']+)["\']')
                tablenames = tablename_pattern.findall(content)
                
                for pattern in patterns:
                    for match in pattern.finditer(content):
                        relationship_name = match.group(1)
                        line_no = content[:match.start()].count('\n') + 1
                        
                        # Store all relationships for analysis
                        for table in tablenames:
                            if table in TABLES_TO_RENAME or table in TABLES_TO_REMOVE:
                                self.dependencies[table]["relationships"].append({
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": line_no,
                                    "relationship": relationship_name,
                                    "type": "back_populates" if "back_populates" in match.group(0) else "backref"
                                })
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
                
    def find_string_references(self):
        """Find string references to table names"""
        print("\nSearching for string references...")
        
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.sql', '.md', '.txt']:
                if "venv" in str(file_path) or "__pycache__" in str(file_path):
                    continue
                    
                try:
                    content = file_path.read_text()
                    
                    for old_name in list(TABLES_TO_RENAME.keys()) + list(TABLES_TO_REMOVE):
                        # Look for the table name as a string
                        pattern = re.compile(rf'["\']?{re.escape(old_name)}["\']?')
                        
                        for match in pattern.finditer(content):
                            line_no = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_no - 1].strip()
                            
                            # Skip if it's a __tablename__ definition
                            if "__tablename__" in line_content:
                                continue
                                
                            self.dependencies[old_name]["string_references"].append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_no,
                                "context": line_content[:100]  # First 100 chars of line
                            })
                except Exception as e:
                    if "venv" not in str(e):  # Suppress venv errors
                        print(f"Error reading {file_path}: {e}")
                        
    def find_migration_references(self):
        """Find references in migration files"""
        print("\nSearching for migration references...")
        
        migrations_dir = self.project_root / "alembic" / "versions"
        if migrations_dir.exists():
            for migration_file in migrations_dir.glob("*.py"):
                try:
                    content = migration_file.read_text()
                    
                    for old_name in list(TABLES_TO_RENAME.keys()) + list(TABLES_TO_REMOVE):
                        if old_name in content:
                            self.dependencies[old_name]["migrations"].append({
                                "file": str(migration_file.relative_to(self.project_root)),
                                "migration_id": migration_file.stem
                            })
                except Exception as e:
                    print(f"Error reading {migration_file}: {e}")
                    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\nGenerating dependency report...")
        
        report = {
            "summary": {
                "tables_to_rename": len(TABLES_TO_RENAME),
                "tables_to_remove": len(TABLES_TO_REMOVE),
                "total_foreign_keys": sum(len(d["foreign_keys"]) for d in self.dependencies.values()),
                "total_relationships": sum(len(d["relationships"]) for d in self.dependencies.values()),
                "total_string_references": sum(len(d["string_references"]) for d in self.dependencies.values()),
                "total_migrations": sum(len(d["migrations"]) for d in self.dependencies.values()),
            },
            "rename_mapping": TABLES_TO_RENAME,
            "remove_list": list(TABLES_TO_REMOVE),
            "dependencies": dict(self.dependencies)
        }
        
        # Save report
        report_path = self.project_root / "TABLE_DEPENDENCY_ANALYSIS.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nReport saved to: {report_path}")
        print(f"\nSummary:")
        print(f"- Tables to rename: {report['summary']['tables_to_rename']}")
        print(f"- Tables to remove: {report['summary']['tables_to_remove']}")
        print(f"- Foreign key references: {report['summary']['total_foreign_keys']}")
        print(f"- Relationship references: {report['summary']['total_relationships']}")
        print(f"- String references: {report['summary']['total_string_references']}")
        print(f"- Migration references: {report['summary']['total_migrations']}")
        
        # Find tables with most dependencies
        print("\nTables with most dependencies:")
        sorted_tables = sorted(
            self.dependencies.items(),
            key=lambda x: sum(len(v) for v in x[1].values()),
            reverse=True
        )[:10]
        
        for table, deps in sorted_tables:
            total_deps = sum(len(v) for v in deps.values())
            if total_deps > 0:
                print(f"  {table}: {total_deps} dependencies")


if __name__ == "__main__":
    analyzer = TableDependencyAnalyzer("/Users/dineshpatel/code/projects/SynapseDTE")
    analyzer.analyze()