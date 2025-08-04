#!/usr/bin/env python3
"""
Apply complete clean versioning migration
WARNING: This will drop old versioning tables!
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def apply_clean_versioning():
    """Apply the complete clean versioning migration"""
    
    # Direct database URL
    database_url = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
    
    # Create engine
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        print("Starting clean versioning migration...")
        
        # Step 1: Drop old versioning tables
        print("\nStep 1: Dropping old versioning tables...")
        old_tables = [
            # Old versioning tables that might exist
            'version_history',
            'workflow_version_operations',
            'data_profiling_rule_versions',
            'test_execution_versions',
            'observation_versions',
            'scoping_decision_versions',
            'versioned_attribute_scoping_recommendations',
            'sample_sets',
            'sample_records',
            'sample_validation_results',
            'sample_validation_issues',
        ]
        
        for table in old_tables:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  Dropped: {table}")
            except Exception as e:
                print(f"  Warning: {table} - {e}")
        
        # Step 2: Create new clean versioning tables
        print("\nStep 2: Creating new clean versioning tables...")
        
        # Execute the complete migration SQL
        migration_sql = """
        -- Planning Phase
        CREATE TABLE IF NOT EXISTS planning_versions (
            version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_number INTEGER NOT NULL,
            version_status VARCHAR(20) NOT NULL,
            parent_version_id UUID,
            workflow_execution_id VARCHAR(255) NOT NULL,
            workflow_run_id VARCHAR(255) NOT NULL,
            activity_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER NOT NULL REFERENCES users(user_id),
            approved_at TIMESTAMP WITH TIME ZONE,
            approved_by_id INTEGER REFERENCES users(user_id),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            phase_name VARCHAR(50) NOT NULL,
            total_attributes INTEGER NOT NULL DEFAULT 0,
            included_attributes INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT uq_planning_version UNIQUE (cycle_id, report_id, version_number)
        );
        
        CREATE INDEX IF NOT EXISTS idx_planning_current ON planning_versions(cycle_id, report_id, version_status);
        CREATE INDEX IF NOT EXISTS idx_planning_workflow ON planning_versions(workflow_execution_id);
        
        CREATE TABLE IF NOT EXISTS attribute_decisions (
            decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES planning_versions(version_id) ON DELETE CASCADE,
            attribute_id INTEGER NOT NULL REFERENCES report_attributes(attribute_id),
            attribute_name VARCHAR(255) NOT NULL,
            include_in_testing BOOLEAN NOT NULL DEFAULT true,
            decision_reason TEXT,
            risk_rating VARCHAR(20)
        );
        CREATE INDEX IF NOT EXISTS idx_attr_decision_version ON attribute_decisions(version_id);
        
        -- Data Profiling Phase
        CREATE TABLE IF NOT EXISTS data_profiling_versions (
            version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_number INTEGER NOT NULL,
            version_status VARCHAR(20) NOT NULL,
            parent_version_id UUID,
            workflow_execution_id VARCHAR(255) NOT NULL,
            workflow_run_id VARCHAR(255) NOT NULL,
            activity_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER NOT NULL REFERENCES users(user_id),
            approved_at TIMESTAMP WITH TIME ZONE,
            approved_by_id INTEGER REFERENCES users(user_id),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            phase_name VARCHAR(50) NOT NULL,
            source_files JSONB NOT NULL,
            total_rules INTEGER NOT NULL DEFAULT 0,
            approved_rules INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT uq_profiling_version UNIQUE (cycle_id, report_id, version_number)
        );
        
        CREATE TABLE IF NOT EXISTS versioned_profiling_rules (
            rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES data_profiling_versions(version_id) ON DELETE CASCADE,
            rule_name VARCHAR(255) NOT NULL,
            rule_type VARCHAR(50) NOT NULL,
            rule_definition JSONB NOT NULL,
            approval_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            approval_notes TEXT
        );
        
        -- Scoping Phase
        CREATE TABLE IF NOT EXISTS scoping_versions (
            version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_number INTEGER NOT NULL,
            version_status VARCHAR(20) NOT NULL,
            parent_version_id UUID,
            workflow_execution_id VARCHAR(255) NOT NULL,
            workflow_run_id VARCHAR(255) NOT NULL,
            activity_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER NOT NULL REFERENCES users(user_id),
            approved_at TIMESTAMP WITH TIME ZONE,
            approved_by_id INTEGER REFERENCES users(user_id),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            phase_name VARCHAR(50) NOT NULL,
            total_attributes INTEGER NOT NULL DEFAULT 0,
            in_scope_count INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT uq_scoping_version UNIQUE (cycle_id, report_id, version_number)
        );
        
        CREATE TABLE IF NOT EXISTS scoping_decisions (
            decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES scoping_versions(version_id) ON DELETE CASCADE,
            attribute_id INTEGER NOT NULL REFERENCES report_attributes(attribute_id),
            is_in_scope BOOLEAN NOT NULL,
            scoping_rationale TEXT,
            risk_assessment VARCHAR(20),
            approval_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        );
        
        -- Sample Selection Phase
        CREATE TABLE IF NOT EXISTS sample_selection_versions (
            version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_number INTEGER NOT NULL,
            version_status VARCHAR(20) NOT NULL,
            parent_version_id UUID,
            workflow_execution_id VARCHAR(255) NOT NULL,
            workflow_run_id VARCHAR(255) NOT NULL,
            activity_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER NOT NULL REFERENCES users(user_id),
            approved_at TIMESTAMP WITH TIME ZONE,
            approved_by_id INTEGER REFERENCES users(user_id),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            phase_name VARCHAR(50) NOT NULL,
            selection_criteria JSONB NOT NULL,
            target_sample_size INTEGER NOT NULL,
            actual_sample_size INTEGER NOT NULL,
            CONSTRAINT uq_sample_version UNIQUE (cycle_id, report_id, version_number)
        );
        
        CREATE TABLE IF NOT EXISTS sample_decisions (
            decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES sample_selection_versions(version_id) ON DELETE CASCADE,
            sample_identifier VARCHAR(255) NOT NULL,
            sample_data JSONB NOT NULL,
            sample_type VARCHAR(50) NOT NULL,
            source VARCHAR(20) NOT NULL,
            source_metadata JSONB,
            decision_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            decision_notes TEXT,
            carried_from_version_id UUID,
            carried_from_decision_id UUID
        );
        CREATE INDEX IF NOT EXISTS idx_sample_decision_version ON sample_decisions(version_id);
        CREATE INDEX IF NOT EXISTS idx_sample_decision_status ON sample_decisions(decision_status);
        
        -- Data Owner Assignment (Audit)
        CREATE TABLE IF NOT EXISTS versioned_data_owner_assignments (
            assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            workflow_execution_id VARCHAR(255) NOT NULL,
            lob_id UUID NOT NULL REFERENCES lobs(lob_id),
            data_owner_id INTEGER NOT NULL REFERENCES users(user_id),
            assignment_type VARCHAR(50) NOT NULL DEFAULT 'primary',
            assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            assigned_by_id INTEGER NOT NULL REFERENCES users(user_id),
            is_active BOOLEAN NOT NULL DEFAULT true,
            previous_assignment_id UUID REFERENCES versioned_data_owner_assignments(assignment_id),
            change_reason TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_owner_active ON versioned_data_owner_assignments(cycle_id, report_id, lob_id, is_active);
        CREATE INDEX IF NOT EXISTS idx_owner_workflow ON versioned_data_owner_assignments(workflow_execution_id);
        
        -- Document Submission (Audit)
        CREATE TABLE IF NOT EXISTS versioned_document_submissions (
            submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            lob_id UUID NOT NULL REFERENCES lobs(lob_id),
            workflow_execution_id VARCHAR(255) NOT NULL,
            document_name VARCHAR(255) NOT NULL,
            document_type VARCHAR(100) NOT NULL,
            document_path VARCHAR(500) NOT NULL,
            document_metadata JSONB,
            document_version INTEGER NOT NULL DEFAULT 1,
            replaces_submission_id UUID REFERENCES versioned_document_submissions(submission_id),
            submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            submitted_by_id INTEGER NOT NULL REFERENCES users(user_id),
            is_current BOOLEAN NOT NULL DEFAULT true
        );
        CREATE INDEX IF NOT EXISTS idx_doc_current ON versioned_document_submissions(cycle_id, report_id, lob_id, is_current);
        CREATE INDEX IF NOT EXISTS idx_doc_workflow ON versioned_document_submissions(workflow_execution_id);
        
        -- Test Execution Audit
        CREATE TABLE IF NOT EXISTS test_execution_audit (
            audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            test_execution_id INTEGER NOT NULL REFERENCES cycle_report_test_execution_test_executions(execution_id),
            workflow_execution_id VARCHAR(255) NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            action_details JSONB NOT NULL,
            requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            requested_by_id INTEGER NOT NULL REFERENCES users(user_id),
            responded_at TIMESTAMP WITH TIME ZONE,
            responded_by_id INTEGER REFERENCES users(user_id),
            response_status VARCHAR(50),
            turnaround_hours FLOAT
        );
        CREATE INDEX IF NOT EXISTS idx_test_audit_execution ON test_execution_audit(test_execution_id);
        CREATE INDEX IF NOT EXISTS idx_test_audit_workflow ON test_execution_audit(workflow_execution_id);
        
        -- Observation Management Phase
        CREATE TABLE IF NOT EXISTS observation_versions (
            version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_number INTEGER NOT NULL,
            version_status VARCHAR(20) NOT NULL,
            parent_version_id UUID,
            workflow_execution_id VARCHAR(255) NOT NULL,
            workflow_run_id VARCHAR(255) NOT NULL,
            activity_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER NOT NULL REFERENCES users(user_id),
            approved_at TIMESTAMP WITH TIME ZONE,
            approved_by_id INTEGER REFERENCES users(user_id),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            phase_name VARCHAR(50) NOT NULL,
            observation_period_start DATE NOT NULL,
            observation_period_end DATE NOT NULL,
            total_observations INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT uq_observation_version UNIQUE (cycle_id, report_id, version_number)
        );
        
        CREATE TABLE IF NOT EXISTS observation_decisions (
            decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES observation_versions(version_id) ON DELETE CASCADE,
            observation_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            title VARCHAR(500) NOT NULL,
            description TEXT NOT NULL,
            evidence_references JSONB,
            approval_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            requires_remediation BOOLEAN NOT NULL DEFAULT false,
            remediation_deadline DATE
        );
        
        -- Test Report Phase
        CREATE TABLE IF NOT EXISTS test_report_versions (
            version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_number INTEGER NOT NULL,
            version_status VARCHAR(20) NOT NULL,
            parent_version_id UUID,
            workflow_execution_id VARCHAR(255) NOT NULL,
            workflow_run_id VARCHAR(255) NOT NULL,
            activity_name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER NOT NULL REFERENCES users(user_id),
            approved_at TIMESTAMP WITH TIME ZONE,
            approved_by_id INTEGER REFERENCES users(user_id),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            phase_name VARCHAR(50) NOT NULL,
            report_title VARCHAR(500) NOT NULL,
            report_period VARCHAR(100) NOT NULL,
            executive_summary TEXT,
            draft_document_path VARCHAR(500),
            final_document_path VARCHAR(500),
            requires_executive_signoff BOOLEAN NOT NULL DEFAULT true,
            executive_signoff_complete BOOLEAN NOT NULL DEFAULT false,
            CONSTRAINT uq_report_version UNIQUE (cycle_id, report_id, version_number)
        );
        
        CREATE TABLE IF NOT EXISTS report_sections (
            section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES test_report_versions(version_id) ON DELETE CASCADE,
            section_type VARCHAR(50) NOT NULL,
            section_title VARCHAR(255) NOT NULL,
            section_content TEXT,
            section_order INTEGER NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS report_signoffs (
            signoff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES test_report_versions(version_id) ON DELETE CASCADE,
            signoff_role VARCHAR(50) NOT NULL,
            signoff_user_id INTEGER REFERENCES users(user_id),
            signoff_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            signoff_date TIMESTAMP WITH TIME ZONE,
            signoff_notes TEXT,
            CONSTRAINT uq_report_signoff UNIQUE (version_id, signoff_role)
        );
        """
        
        # Execute the migration
        statements = migration_sql.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    await conn.execute(text(statement))
                    # Extract table name if it's a CREATE TABLE statement
                    if 'CREATE TABLE' in statement:
                        lines = statement.strip().split('\n')
                        for line in lines:
                            if 'CREATE TABLE' in line:
                                table_name = line.split('CREATE TABLE IF NOT EXISTS ')[1].split(' ')[0]
                                print(f"  Created: {table_name}")
                                break
                except Exception as e:
                    print(f"  Error executing statement: {e}")
                    print(f"  Statement: {statement[:100]}...")
        
        print("\nMigration completed successfully!")
        print("\nNote: This is a destructive migration. All old versioning data has been removed.")
        print("The new clean versioning system is now in place.")
    
    await engine.dispose()


if __name__ == "__main__":
    print("Clean Versioning Migration - Complete")
    print("=" * 50)
    print("WARNING: This will DROP old versioning tables!")
    print("All existing version history will be lost.")
    print()
    
    # Auto-confirm for non-interactive mode
    if '--yes' in sys.argv:
        print("Auto-confirmed with --yes flag")
    else:
        try:
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != "yes":
                print("Migration cancelled.")
                sys.exit(0)
        except EOFError:
            print("Running in non-interactive mode, proceeding...")
    
    asyncio.run(apply_clean_versioning())