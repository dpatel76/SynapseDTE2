"""Unify scoping decisions into single table

Revision ID: unify_scoping_decisions
Revises: 
Create Date: 2025-07-18 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'unify_scoping_decisions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create the report owner decision enum if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE report_owner_decision_enum AS ENUM ('Approved', 'Rejected', 'Pending');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create scoping_decision_enum if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE scoping_decision_enum AS ENUM ('Accept', 'Decline', 'Test', 'Skip');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create the unified scoping decisions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS cycle_report_scoping_decisions (
            decision_id SERIAL PRIMARY KEY,
            cycle_id INTEGER NOT NULL REFERENCES test_cycles(cycle_id),
            report_id INTEGER NOT NULL REFERENCES reports(id),
            attribute_id INTEGER NOT NULL REFERENCES cycle_report_planning_attributes(id),
            phase_id INTEGER REFERENCES workflow_phases(phase_id),
            
            -- Tester decision fields
            tester_decision scoping_decision_enum,
            final_scoping BOOLEAN,
            tester_rationale TEXT,
            tester_decided_by INTEGER REFERENCES users(user_id),
            tester_decided_at TIMESTAMP WITH TIME ZONE,
            
            -- Report Owner decision fields
            report_owner_decision report_owner_decision_enum,
            report_owner_notes TEXT,
            report_owner_decided_by INTEGER REFERENCES users(user_id),
            report_owner_decided_at TIMESTAMP WITH TIME ZONE,
            
            -- Override fields
            override_reason TEXT,
            override_by_user_id INTEGER REFERENCES users(user_id),
            override_timestamp TIMESTAMP WITH TIME ZONE,
            
            -- Version tracking
            version INTEGER NOT NULL DEFAULT 1,
            
            -- Audit fields
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            created_by INTEGER REFERENCES users(user_id),
            updated_at TIMESTAMP WITH TIME ZONE,
            updated_by INTEGER REFERENCES users(user_id),
            
            -- Constraints
            CONSTRAINT uq_scoping_decisions_version UNIQUE (cycle_id, report_id, attribute_id, version)
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_scoping_decisions_cycle_report ON cycle_report_scoping_decisions(cycle_id, report_id);
        CREATE INDEX IF NOT EXISTS idx_scoping_decisions_attribute ON cycle_report_scoping_decisions(attribute_id);
        CREATE INDEX IF NOT EXISTS idx_scoping_decisions_decision_id ON cycle_report_scoping_decisions(decision_id);
    """)
    
    # Migrate data from cycle_report_scoping_tester_decisions
    # Only migrate records that have valid foreign key references
    op.execute("""
        INSERT INTO cycle_report_scoping_decisions (
            cycle_id, report_id, attribute_id, phase_id,
            tester_decision, final_scoping, tester_rationale, 
            tester_decided_by, tester_decided_at,
            override_reason,
            version, created_at, created_by, updated_at, updated_by
        )
        SELECT DISTINCT ON (td.cycle_id, td.report_id, td.attribute_id)
            td.cycle_id, td.report_id, td.attribute_id, td.phase_id,
            td.decision, td.final_scoping, td.tester_rationale,
            td.decided_by, td.created_at,
            td.override_reason,
            1, td.created_at, td.created_by_id, td.updated_at, td.updated_by_id
        FROM cycle_report_scoping_tester_decisions td
        INNER JOIN cycle_report_planning_attributes attr ON td.attribute_id = attr.id
        INNER JOIN test_cycles tc ON td.cycle_id = tc.cycle_id
        INNER JOIN reports r ON td.report_id = r.id
        WHERE td.decided_by IS NULL OR EXISTS (SELECT 1 FROM users u WHERE u.user_id = td.decided_by)
        ORDER BY td.cycle_id, td.report_id, td.attribute_id, td.created_at DESC
    """)
    
    # Update report owner decisions from cycle_report_scoping_report_owner_reviews
    # This is more complex as it's at the submission level, not attribute level
    # For now, we'll leave report_owner fields NULL and handle them separately
    
    # Create backup tables before dropping
    op.rename_table('cycle_report_scoping_tester_decisions', 'cycle_report_scoping_tester_decisions_backup')
    op.rename_table('cycle_report_scoping_report_owner_reviews', 'cycle_report_scoping_report_owner_reviews_backup')
    
    # Note: We're keeping the backup tables for safety. They can be dropped later after verification.


def downgrade():
    # Restore original tables from backups
    op.rename_table('cycle_report_scoping_tester_decisions_backup', 'cycle_report_scoping_tester_decisions')
    op.rename_table('cycle_report_scoping_report_owner_reviews_backup', 'cycle_report_scoping_report_owner_reviews')
    
    # Drop the unified table
    op.drop_table('cycle_report_scoping_decisions')
    
    # Drop the report owner decision enum
    report_owner_decision_enum = postgresql.ENUM('Approved', 'Rejected', 'Pending', name='report_owner_decision_enum')
    report_owner_decision_enum.drop(op.get_bind(), checkfirst=True)