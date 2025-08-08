"""add_calculated_status_columns

Revision ID: add_calculated_status
Revises: 4d40548ec4af
Create Date: 2025-08-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'add_calculated_status'
down_revision = 'fix_sample_selection_001'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # 1. Add calculated status column to sample_selection_samples
    # First add the column
    op.add_column('cycle_report_sample_selection_samples', 
        sa.Column('calculated_status', sa.String(20), nullable=True)
    )
    
    # Update existing records with calculated status
    conn.execute(text("""
        UPDATE cycle_report_sample_selection_samples
        SET calculated_status = 
            CASE 
                WHEN tester_decision = 'approved' AND report_owner_decision = 'approved' THEN 'approved'
                WHEN tester_decision = 'rejected' OR report_owner_decision = 'rejected' THEN 'rejected'
                ELSE 'pending'
            END
    """))
    
    # Make column not nullable after populating
    op.alter_column('cycle_report_sample_selection_samples', 'calculated_status',
                    nullable=False,
                    server_default='pending')
    
    # Add index for efficient filtering
    op.create_index('idx_sample_selection_calculated_status', 
                    'cycle_report_sample_selection_samples', 
                    ['calculated_status'])
    
    # 2. Add calculated status to scoping attributes
    # Check if table exists first
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'cycle_report_scoping_attributes'
        )
    """))
    
    if result.scalar():
        op.add_column('cycle_report_scoping_attributes',
            sa.Column('calculated_status', sa.String(20), nullable=True)
        )
        
        # Update based on tester and report owner decisions
        # Note: tester_decision uses 'accept', 'decline', 'override'
        # report_owner_decision uses 'approved', 'rejected', 'pending', 'needs_revision'
        conn.execute(text("""
            UPDATE cycle_report_scoping_attributes
            SET calculated_status = 
                CASE 
                    WHEN tester_decision = 'accept' AND report_owner_decision = 'approved' THEN 'approved'
                    WHEN tester_decision = 'decline' OR report_owner_decision = 'rejected' THEN 'rejected'
                    ELSE 'pending'
                END
        """))
        
        # Make column not nullable
        op.alter_column('cycle_report_scoping_attributes', 'calculated_status',
                        nullable=False,
                        server_default='pending')
        
        # Add index
        op.create_index('idx_scoping_attributes_calculated_status',
                        'cycle_report_scoping_attributes',
                        ['calculated_status'])
    
    # 3. Add calculated status to data profiling rules
    # Check if table exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'cycle_report_data_profiling_rules'
        )
    """))
    
    if result.scalar():
        # Check if column already exists
        col_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'cycle_report_data_profiling_rules' 
                AND column_name = 'calculated_status'
            )
        """))
        
        if not col_exists.scalar():
            op.add_column('cycle_report_data_profiling_rules',
                sa.Column('calculated_status', sa.String(20), nullable=True)
            )
            
            # Update based on tester and report owner decisions
            # decision_enum uses 'approved', 'rejected', 'request_changes'
            conn.execute(text("""
                UPDATE cycle_report_data_profiling_rules
                SET calculated_status = 
                    CASE 
                        WHEN tester_decision = 'approved' AND report_owner_decision = 'approved' THEN 'approved'
                        WHEN tester_decision = 'rejected' OR report_owner_decision = 'rejected' THEN 'rejected'
                        ELSE 'pending'
                    END
            """))
            
            # Make column not nullable
            op.alter_column('cycle_report_data_profiling_rules', 'calculated_status',
                            nullable=False,
                            server_default='pending')
            
            # Add index
            op.create_index('idx_data_profiling_rules_calculated_status',
                            'cycle_report_data_profiling_rules',
                            ['calculated_status'])
    
    # 4. Create a trigger to automatically update calculated_status on sample updates
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION update_sample_calculated_status()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.calculated_status = 
                CASE 
                    WHEN NEW.tester_decision = 'approved' AND NEW.report_owner_decision = 'approved' THEN 'approved'
                    WHEN NEW.tester_decision = 'rejected' OR NEW.report_owner_decision = 'rejected' THEN 'rejected'
                    ELSE 'pending'
                END;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER sample_selection_status_trigger
        BEFORE INSERT OR UPDATE OF tester_decision, report_owner_decision
        ON cycle_report_sample_selection_samples
        FOR EACH ROW
        EXECUTE FUNCTION update_sample_calculated_status();
    """))
    
    # Similar triggers for scoping attributes if table exists
    if conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_scoping_attributes')")).scalar():
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_scoping_calculated_status()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.calculated_status = 
                    CASE 
                        WHEN NEW.tester_decision = 'accept' AND NEW.report_owner_decision = 'approved' THEN 'approved'
                        WHEN NEW.tester_decision = 'decline' OR NEW.report_owner_decision = 'rejected' THEN 'rejected'
                        ELSE 'pending'
                    END;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER scoping_attributes_status_trigger
            BEFORE INSERT OR UPDATE OF tester_decision, report_owner_decision
            ON cycle_report_scoping_attributes
            FOR EACH ROW
            EXECUTE FUNCTION update_scoping_calculated_status();
        """))


def downgrade():
    conn = op.get_bind()
    
    # Drop triggers
    conn.execute(text("DROP TRIGGER IF EXISTS sample_selection_status_trigger ON cycle_report_sample_selection_samples"))
    conn.execute(text("DROP FUNCTION IF EXISTS update_sample_calculated_status()"))
    
    conn.execute(text("DROP TRIGGER IF EXISTS scoping_attributes_status_trigger ON cycle_report_scoping_attributes"))
    conn.execute(text("DROP FUNCTION IF EXISTS update_scoping_calculated_status()"))
    
    # Drop indexes
    op.drop_index('idx_sample_selection_calculated_status', 'cycle_report_sample_selection_samples')
    
    if conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_scoping_attributes')")).scalar():
        op.drop_index('idx_scoping_attributes_calculated_status', 'cycle_report_scoping_attributes')
    
    if conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_data_profiling_rules')")).scalar():
        op.drop_index('idx_data_profiling_rules_calculated_status', 'cycle_report_data_profiling_rules')
    
    # Drop columns
    op.drop_column('cycle_report_sample_selection_samples', 'calculated_status')
    
    if conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_scoping_attributes')")).scalar():
        op.drop_column('cycle_report_scoping_attributes', 'calculated_status')
    
    if conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_data_profiling_rules')")).scalar():
        if conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'cycle_report_data_profiling_rules' AND column_name = 'calculated_status')")).scalar():
            op.drop_column('cycle_report_data_profiling_rules', 'calculated_status')