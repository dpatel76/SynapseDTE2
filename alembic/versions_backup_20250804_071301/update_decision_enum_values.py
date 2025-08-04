"""Update decision enum values for consistency

Revision ID: update_decision_enum_values
Revises: 
Create Date: 2024-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_decision_enum_values'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # First update the data to use new values
    op.execute("""
        UPDATE cycle_report_data_profiling_rules
        SET tester_decision = 
          CASE 
            WHEN tester_decision = 'approve' THEN 'approved'::text
            WHEN tester_decision = 'reject' THEN 'rejected'::text
            ELSE tester_decision::text
          END
        WHERE tester_decision IN ('approve', 'reject');
    """)
    
    op.execute("""
        UPDATE cycle_report_data_profiling_rules
        SET report_owner_decision = 
          CASE 
            WHEN report_owner_decision = 'approve' THEN 'approved'::text
            WHEN report_owner_decision = 'reject' THEN 'rejected'::text
            ELSE report_owner_decision::text
          END
        WHERE report_owner_decision IN ('approve', 'reject');
    """)
    
    # Drop the old enum type constraints
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN tester_decision TYPE text;")
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN report_owner_decision TYPE text;")
    
    # Drop and recreate the enum with new values
    op.execute("DROP TYPE IF EXISTS decision_enum CASCADE;")
    op.execute("CREATE TYPE decision_enum AS ENUM ('approved', 'rejected', 'request_changes');")
    
    # Re-apply the enum type to columns
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN tester_decision TYPE decision_enum USING tester_decision::decision_enum;")
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN report_owner_decision TYPE decision_enum USING report_owner_decision::decision_enum;")


def downgrade():
    # Revert data to old values
    op.execute("""
        UPDATE cycle_report_data_profiling_rules
        SET tester_decision = 
          CASE 
            WHEN tester_decision = 'approved' THEN 'approve'::text
            WHEN tester_decision = 'rejected' THEN 'reject'::text
            ELSE tester_decision::text
          END
        WHERE tester_decision IN ('approved', 'rejected');
    """)
    
    op.execute("""
        UPDATE cycle_report_data_profiling_rules
        SET report_owner_decision = 
          CASE 
            WHEN report_owner_decision = 'approved' THEN 'approve'::text
            WHEN report_owner_decision = 'rejected' THEN 'reject'::text
            ELSE report_owner_decision::text
          END
        WHERE report_owner_decision IN ('approved', 'rejected');
    """)
    
    # Drop constraints and recreate old enum
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN tester_decision TYPE text;")
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN report_owner_decision TYPE text;")
    op.execute("DROP TYPE IF EXISTS decision_enum CASCADE;")
    op.execute("CREATE TYPE decision_enum AS ENUM ('approve', 'reject', 'request_changes');")
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN tester_decision TYPE decision_enum USING tester_decision::decision_enum;")
    op.execute("ALTER TABLE cycle_report_data_profiling_rules ALTER COLUMN report_owner_decision TYPE decision_enum USING report_owner_decision::decision_enum;")