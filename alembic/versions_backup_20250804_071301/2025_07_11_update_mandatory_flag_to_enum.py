"""Update mandatory_flag from boolean to enum

Revision ID: update_mandatory_flag_enum
Revises: 2025_07_11_merge_heads
Create Date: 2025-07-11 19:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_mandatory_flag_enum'
down_revision = '2025_07_11_merge_heads'
branch_labels = None
depends_on = None


def upgrade():
    # Create the enum type if it doesn't exist
    mandatory_flag_enum = postgresql.ENUM('Mandatory', 'Conditional', 'Optional', name='mandatory_flag_enum')
    mandatory_flag_enum.create(op.get_bind(), checkfirst=True)
    
    # Add a temporary column with the enum type
    op.add_column('cycle_report_attributes_planning', 
                  sa.Column('is_mandatory_temp', postgresql.ENUM('Mandatory', 'Conditional', 'Optional', 
                                                                 name='mandatory_flag_enum', 
                                                                 create_type=False), 
                           nullable=True))
    
    # Convert boolean values to enum values
    op.execute("""
        UPDATE cycle_report_planning_attributes
        SET is_mandatory_temp = CASE 
            WHEN is_mandatory = true THEN 'Mandatory'::mandatory_flag_enum
            ELSE 'Optional'::mandatory_flag_enum
        END
    """)
    
    # Drop the old column
    op.drop_column('cycle_report_attributes_planning', 'is_mandatory')
    
    # Rename the temporary column to the original name
    op.alter_column('cycle_report_attributes_planning', 'is_mandatory_temp', 
                    new_column_name='is_mandatory',
                    nullable=False,
                    server_default='Optional')


def downgrade():
    # Add a temporary boolean column
    op.add_column('cycle_report_attributes_planning', 
                  sa.Column('is_mandatory_temp', sa.Boolean(), nullable=True))
    
    # Convert enum values back to boolean
    op.execute("""
        UPDATE cycle_report_planning_attributes
        SET is_mandatory_temp = CASE 
            WHEN is_mandatory = 'Mandatory'::mandatory_flag_enum THEN true
            ELSE false
        END
    """)
    
    # Drop the enum column
    op.drop_column('cycle_report_attributes_planning', 'is_mandatory')
    
    # Rename the temporary column to the original name
    op.alter_column('cycle_report_attributes_planning', 'is_mandatory_temp', 
                    new_column_name='is_mandatory',
                    nullable=False,
                    server_default='false')
    
    # Drop the enum type (if not used elsewhere)
    # mandatory_flag_enum = postgresql.ENUM('Mandatory', 'Conditional', 'Optional', name='mandatory_flag_enum')
    # mandatory_flag_enum.drop(op.get_bind(), checkfirst=True)