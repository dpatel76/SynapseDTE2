"""Update user role enum to new values

Revision ID: update_user_roles_enum
Revises: 
Create Date: 2025-01-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_user_roles_enum'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create new enum type
    op.execute("""
        CREATE TYPE user_role_enum_new AS ENUM (
            'Tester',
            'Test Executive',
            'Report Owner',
            'Report Executive',
            'Data Owner',
            'Data Executive',
            'Admin'
        )
    """)
    
    # Update users table to use new enum, converting old values
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN role TYPE user_role_enum_new 
        USING CASE 
            WHEN role = 'Test Manager' THEN 'Test Executive'::user_role_enum_new
            WHEN role = 'CDO' THEN 'Data Executive'::user_role_enum_new
            WHEN role = 'Report Owner Executive' THEN 'Report Executive'::user_role_enum_new
            WHEN role = 'Data Provider' THEN 'Data Owner'::user_role_enum_new
            ELSE role::text::user_role_enum_new
        END
    """)
    
    # Drop old enum and rename new one
    op.execute("DROP TYPE user_role_enum")
    op.execute("ALTER TYPE user_role_enum_new RENAME TO user_role_enum")
    
    # Update roles table
    op.execute("UPDATE rbac_roles SET role_name = 'Test Executive' WHERE role_name = 'Test Manager'")
    op.execute("UPDATE rbac_roles SET role_name = 'Data Executive' WHERE role_name = 'CDO'")
    op.execute("UPDATE rbac_roles SET role_name = 'Report Executive' WHERE role_name = 'Report Owner Executive'")
    op.execute("UPDATE rbac_roles SET role_name = 'Data Owner' WHERE role_name = 'Data Provider'")
    
    # Update workflow activity templates
    op.execute("UPDATE workflow_activity_templates SET required_role = 'Test Executive' WHERE required_role = 'Test Manager'")
    op.execute("UPDATE workflow_activity_templates SET required_role = 'Data Executive' WHERE required_role = 'CDO'")


def downgrade():
    # Create old enum type
    op.execute("""
        CREATE TYPE user_role_enum_old AS ENUM (
            'Tester',
            'Test Manager',
            'Report Owner',
            'Report Owner Executive',
            'Data Provider',
            'CDO',
            'Admin',
            'Data Executive',
            'Test Executive',
            'Data Owner'
        )
    """)
    
    # Revert users table
    op.execute("""
        ALTER TABLE users 
        ALTER COLUMN role TYPE user_role_enum_old 
        USING CASE 
            WHEN role = 'Test Executive' THEN 'Test Manager'::user_role_enum_old
            WHEN role = 'Data Executive' THEN 'CDO'::user_role_enum_old
            WHEN role = 'Report Executive' THEN 'Report Owner Executive'::user_role_enum_old
            WHEN role = 'Data Owner' THEN 'Data Provider'::user_role_enum_old
            ELSE role::text::user_role_enum_old
        END
    """)
    
    # Drop new enum and restore old one
    op.execute("DROP TYPE user_role_enum")
    op.execute("ALTER TYPE user_role_enum_old RENAME TO user_role_enum")
    
    # Revert roles table
    op.execute("UPDATE rbac_roles SET role_name = 'Test Manager' WHERE role_name = 'Test Executive'")
    op.execute("UPDATE rbac_roles SET role_name = 'CDO' WHERE role_name = 'Data Executive'")
    op.execute("UPDATE rbac_roles SET role_name = 'Report Owner Executive' WHERE role_name = 'Report Executive'")
    op.execute("UPDATE rbac_roles SET role_name = 'Data Provider' WHERE role_name = 'Data Owner'")
    
    # Revert workflow activity templates
    op.execute("UPDATE workflow_activity_templates SET required_role = 'Test Manager' WHERE required_role = 'Test Executive'")
    op.execute("UPDATE workflow_activity_templates SET required_role = 'CDO' WHERE required_role = 'Data Executive'")