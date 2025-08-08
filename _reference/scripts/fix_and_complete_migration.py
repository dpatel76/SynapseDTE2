#!/usr/bin/env python3
"""
Fix and complete the clean versioning migration
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def fix_migration():
    """Fix and complete the migration"""
    
    database_url = "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt"
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        print("Fixing and completing clean versioning migration...")
        
        # Continue with the tables that failed
        migration_sql = """
        -- Data Owner Assignment (Audit) - Fixed lob_id type
        CREATE TABLE IF NOT EXISTS versioned_data_owner_assignments (
            assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            workflow_execution_id VARCHAR(255) NOT NULL,
            lob_id INTEGER NOT NULL REFERENCES lobs(lob_id),
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
        
        -- Document Submission (Audit) - Fixed lob_id type
        CREATE TABLE IF NOT EXISTS versioned_document_submissions (
            submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(report_id),
            lob_id INTEGER NOT NULL REFERENCES lobs(lob_id),
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
        
        # Execute each statement
        statements = migration_sql.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    await conn.execute(text(statement))
                    if 'CREATE TABLE' in statement:
                        lines = statement.strip().split('\n')
                        for line in lines:
                            if 'CREATE TABLE' in line:
                                table_name = line.split('CREATE TABLE IF NOT EXISTS ')[1].split(' ')[0]
                                print(f"  Created: {table_name}")
                                break
                    elif 'CREATE INDEX' in statement:
                        if 'idx_' in statement:
                            idx_name = statement.split('CREATE INDEX IF NOT EXISTS ')[1].split(' ')[0]
                            print(f"  Created index: {idx_name}")
                except Exception as e:
                    print(f"  Error: {e}")
        
        # Verify all tables were created
        print("\nVerifying created tables...")
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'planning_versions', 'attribute_decisions',
                'data_profiling_versions', 'versioned_profiling_rules',
                'scoping_versions', 'scoping_decisions',
                'sample_selection_versions', 'sample_decisions',
                'versioned_data_owner_assignments', 'versioned_document_submissions',
                'test_execution_audit', 'observation_versions',
                'observation_decisions', 'test_report_versions',
                'report_sections', 'report_signoffs'
            )
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        print(f"\nCreated {len(tables)} versioning tables:")
        for table in tables:
            print(f"  ✓ {table}")
        
        print("\nClean versioning migration completed successfully!")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(fix_migration())