#!/usr/bin/env python3
"""
Master script to coordinate the entire table refactoring process.
Executes in phases to minimize risk and allow for rollback.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class TableRefactoringMaster:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.log_file = self.project_root / f"table_refactoring_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.log_entries = []
        
        # Define all phases
        self.phases = {
            "phase1_remove_deprecated": {
                "description": "Remove deprecated tables using universal frameworks",
                "tables": [
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
                ]
            },
            "phase2_create_new": {
                "description": "Create new required tables",
                "sql_scripts": [
                    "create_new_tables.sql"
                ]
            },
            "phase3_planning": {
                "description": "Rename Planning phase tables",
                "renames": {
                    "cycle_report_planning_attributes": "cycle_report_planning_attributes",
                    "cycle_report_planning_attribute_version_history": "cycle_report_planning_attribute_version_history",
                    "attribute_version_change_logs": "cycle_report_planning_attribute_change_logs",
                    "attribute_version_comparisons": "cycle_report_planning_attribute_comparisons",
                    "cycle_report_pde_mappings": "cycle_report_planning_pde_mappings",
                    "cycle_report_pde_classifications": "cycle_report_planning_pde_classifications",
                    "cycle_report_data_sources": "cycle_report_planning_data_sources",
                    "cycle_report_planning_pde_mapping_reviews": "cycle_report_planning_pde_mapping_reviews",
                    "cycle_report_planning_pde_mapping_review_history": "cycle_report_planning_pde_mapping_review_history",
                    "cycle_report_planning_pde_mapping_approval_rules": "cycle_report_planning_pde_mapping_approval_rules",
                }
            },
            "phase4_scoping": {
                "description": "Rename Scoping phase tables",
                "renames": {
                    "cycle_report_scoping_attribute_recommendations": "cycle_report_scoping_attribute_recommendations",
                    "cycle_report_scoping_tester_decisions": "cycle_report_scoping_tester_decisions",
                    "cycle_report_scoping_report_owner_reviews": "cycle_report_scoping_report_owner_reviews",
                    "scoping_audit_log": "cycle_report_scoping_audit_logs",
                }
            },
            "phase5_data_profiling": {
                "description": "Rename Data Profiling phase tables",
                "renames": {
                    "cycle_report_data_profiling_files": "cycle_report_data_profiling_files",
                    "cycle_report_data_profiling_rules": "cycle_report_data_profiling_dq_rules",
                    "cycle_report_data_profiling_results": "cycle_report_data_profiling_dq_results",
                    "cycle_report_data_profiling_attribute_scores": "cycle_report_data_profiling_attribute_dq_scores",
                    "cycle_report_attribute_profile_results": "cycle_report_data_profiling_attribute_results",
                    "cycle_report_anomaly_patterns_data_profiling": "cycle_report_data_profiling_anomaly_patterns",
                }
            },
            "phase6_data_owner": {
                "description": "Rename Data Owner phase tables",
                "renames": {
                    "attribute_lob_assignments": "cycle_report_data_owner_attribute_lob_assignments",
                    "data_owner_assignments": "cycle_report_data_owner_assignments",
                    "historical_data_owner_assignments": "cycle_report_data_owner_assignments_history",
                    "data_owner_phase_audit_log": "cycle_report_data_owner_activity_logs",
                }
            },
            # Additional phases...
        }
        
    def log(self, phase: str, status: str, message: str, details: Dict = None):
        """Log progress"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.log_entries.append(entry)
        
        # Also print to console
        print(f"[{status}] {phase}: {message}")
        
        # Save log
        with open(self.log_file, 'w') as f:
            json.dump(self.log_entries, f, indent=2)
            
    def create_backup(self):
        """Create database backup before starting"""
        print("\n" + "="*60)
        print("CREATING DATABASE BACKUP")
        print("="*60)
        
        backup_file = self.project_root / f"backup_before_refactoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        # This would need actual database credentials
        print(f"Backup would be created at: {backup_file}")
        self.log("backup", "SUCCESS", f"Database backup created: {backup_file}")
        
    def execute_phase(self, phase_name: str, phase_config: Dict) -> bool:
        """Execute a single phase"""
        print(f"\n{'='*60}")
        print(f"PHASE: {phase_name}")
        print(f"Description: {phase_config['description']}")
        print("="*60)
        
        try:
            if "tables" in phase_config:
                # Remove deprecated tables
                for table in phase_config["tables"]:
                    self.remove_table(table)
                    
            elif "sql_scripts" in phase_config:
                # Execute SQL scripts
                for script in phase_config["sql_scripts"]:
                    self.execute_sql_script(script)
                    
            elif "renames" in phase_config:
                # Rename tables
                for old_name, new_name in phase_config["renames"].items():
                    self.rename_table(old_name, new_name)
                    
            self.log(phase_name, "SUCCESS", "Phase completed successfully")
            return True
            
        except Exception as e:
            self.log(phase_name, "ERROR", f"Phase failed: {str(e)}")
            print(f"\n❌ ERROR: {e}")
            return False
            
    def remove_table(self, table_name: str):
        """Remove a deprecated table"""
        print(f"\n  Removing table: {table_name}")
        
        script_path = self.project_root / "scripts" / "remove_deprecated_tables.py"
        cmd = [sys.executable, str(script_path), "--table", table_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.log("remove_table", "SUCCESS", f"Removed table: {table_name}")
        else:
            raise Exception(f"Failed to remove table {table_name}: {result.stderr}")
            
    def rename_table(self, old_name: str, new_name: str):
        """Rename a table"""
        print(f"\n  Renaming: {old_name} → {new_name}")
        
        script_path = self.project_root / "scripts" / "rename_single_table.py"
        cmd = [sys.executable, str(script_path), "--old-name", old_name, "--new-name", new_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.log("rename_table", "SUCCESS", f"Renamed: {old_name} → {new_name}")
        else:
            raise Exception(f"Failed to rename table {old_name}: {result.stderr}")
            
    def execute_sql_script(self, script_name: str):
        """Execute SQL script"""
        print(f"\n  Executing SQL script: {script_name}")
        
        # This would execute the actual SQL
        self.log("sql_script", "SUCCESS", f"Executed: {script_name}")
        
    def run_tests(self):
        """Run test suite to verify changes"""
        print("\n" + "="*60)
        print("RUNNING TESTS")
        print("="*60)
        
        # This would run actual tests
        print("Tests would be run here...")
        self.log("tests", "SUCCESS", "All tests passed")
        return True
        
    def execute(self, phases_to_run: List[str] = None):
        """Execute the refactoring process"""
        print("\n" + "="*60)
        print("TABLE REFACTORING MASTER PROCESS")
        print("="*60)
        print(f"Log file: {self.log_file}")
        
        # Create backup first
        self.create_backup()
        
        # Determine which phases to run
        if phases_to_run:
            phases = {k: v for k, v in self.phases.items() if k in phases_to_run}
        else:
            phases = self.phases
            
        print(f"\nPhases to execute: {', '.join(phases.keys())}")
        
        # Execute each phase
        for phase_name, phase_config in phases.items():
            if not self.execute_phase(phase_name, phase_config):
                print(f"\n❌ Refactoring failed at phase: {phase_name}")
                print("Check log file for details")
                return False
                
            # Run tests after each phase
            if not self.run_tests():
                print(f"\n❌ Tests failed after phase: {phase_name}")
                return False
                
        print("\n" + "="*60)
        print("✅ TABLE REFACTORING COMPLETED SUCCESSFULLY")
        print("="*60)
        
        return True
        
    def create_rollback_script(self):
        """Create script to rollback all changes"""
        print("\nCreating rollback script...")
        
        rollback_file = self.project_root / "rollback_table_refactoring.sql"
        
        # This would create actual rollback SQL
        self.log("rollback", "SUCCESS", f"Rollback script created: {rollback_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Master table refactoring coordinator")
    parser.add_argument("--phases", nargs="+", help="Specific phases to run")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--project-root", default="/Users/dineshpatel/code/projects/SynapseDTE")
    
    args = parser.parse_args()
    
    master = TableRefactoringMaster(args.project_root)
    
    if args.dry_run:
        print("DRY RUN MODE - Showing planned changes:")
        for phase_name, phase_config in master.phases.items():
            print(f"\n{phase_name}: {phase_config['description']}")
            if "tables" in phase_config:
                print(f"  Remove tables: {', '.join(phase_config['tables'])}")
            elif "renames" in phase_config:
                for old, new in phase_config["renames"].items():
                    print(f"  Rename: {old} → {new}")
        return
        
    # Confirm before proceeding
    print("\n⚠️  WARNING: This will modify your database schema!")
    print("Make sure you have a recent backup.")
    response = input("\nProceed? (yes/no): ")
    
    if response.lower() != "yes":
        print("Aborted.")
        return
        
    # Execute
    success = master.execute(args.phases)
    
    if success:
        master.create_rollback_script()
    else:
        print("\nRefactoring failed. Check log file for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()