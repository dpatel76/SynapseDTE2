"""Update sample decision enum values from include/exclude to approved/rejected

Revision ID: update_sample_decision_enum
Revises: 
Create Date: 2025-01-22 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_sample_decision_enum'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create new enum type
    op.execute("CREATE TYPE sample_decision_enum_new AS ENUM ('approved', 'rejected', 'pending')")
    
    # Update tester_decision column
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN tester_decision TYPE VARCHAR(20)
    """)
    
    # Migrate tester_decision values
    op.execute("""
        UPDATE cycle_report_sample_selection_samples 
        SET tester_decision = CASE 
            WHEN tester_decision = 'include' THEN 'approved'
            WHEN tester_decision = 'exclude' THEN 'rejected'
            ELSE tester_decision
        END
    """)
    
    # Update tester_decision to new enum type
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN tester_decision TYPE sample_decision_enum_new 
        USING tester_decision::sample_decision_enum_new
    """)
    
    # Update report_owner_decision column
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN report_owner_decision TYPE VARCHAR(20)
    """)
    
    # Migrate report_owner_decision values
    op.execute("""
        UPDATE cycle_report_sample_selection_samples 
        SET report_owner_decision = CASE 
            WHEN report_owner_decision = 'include' THEN 'approved'
            WHEN report_owner_decision = 'exclude' THEN 'rejected'
            ELSE report_owner_decision
        END
    """)
    
    # Update report_owner_decision to new enum type
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN report_owner_decision TYPE sample_decision_enum_new 
        USING report_owner_decision::sample_decision_enum_new
    """)
    
    # Drop old enum type and rename new one
    op.execute("DROP TYPE IF EXISTS sample_decision_enum CASCADE")
    op.execute("ALTER TYPE sample_decision_enum_new RENAME TO sample_decision_enum")


def downgrade():
    # Create old enum type
    op.execute("CREATE TYPE sample_decision_enum_old AS ENUM ('include', 'exclude', 'pending')")
    
    # Update tester_decision column
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN tester_decision TYPE VARCHAR(20)
    """)
    
    # Migrate tester_decision values back
    op.execute("""
        UPDATE cycle_report_sample_selection_samples 
        SET tester_decision = CASE 
            WHEN tester_decision = 'approved' THEN 'include'
            WHEN tester_decision = 'rejected' THEN 'exclude'
            ELSE tester_decision
        END
    """)
    
    # Update tester_decision to old enum type
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN tester_decision TYPE sample_decision_enum_old 
        USING tester_decision::sample_decision_enum_old
    """)
    
    # Update report_owner_decision column
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN report_owner_decision TYPE VARCHAR(20)
    """)
    
    # Migrate report_owner_decision values back
    op.execute("""
        UPDATE cycle_report_sample_selection_samples 
        SET report_owner_decision = CASE 
            WHEN report_owner_decision = 'approved' THEN 'include'
            WHEN report_owner_decision = 'rejected' THEN 'exclude'
            ELSE report_owner_decision
        END
    """)
    
    # Update report_owner_decision to old enum type
    op.execute("""
        ALTER TABLE cycle_report_sample_selection_samples 
        ALTER COLUMN report_owner_decision TYPE sample_decision_enum_old 
        USING report_owner_decision::sample_decision_enum_old
    """)
    
    # Drop new enum type and rename old one back
    op.execute("DROP TYPE IF EXISTS sample_decision_enum CASCADE")
    op.execute("ALTER TYPE sample_decision_enum_old RENAME TO sample_decision_enum")