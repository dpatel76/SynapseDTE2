"""add audit fields to all tables

Revision ID: 012_add_audit_fields_to_all_tables
Revises: 011_add_individual_sample_tables
Create Date: 2025-01-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '012_add_audit_fields_to_all_tables'
down_revision: Union[str, None] = '011_add_individual_sample_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables to exclude from audit fields
EXCLUDED_TABLES = {
    'alembic_version',  # Alembic migration tracking
    'users',  # Users table itself
}

# Tables that already have created_by/updated_by fields
TABLES_WITH_EXISTING_FIELDS = {
    'profiling_rules',
    'sample_selection_phases',
}


def upgrade() -> None:
    """Add created_by_id and updated_by_id to all tables"""
    
    # Get connection
    conn = op.get_bind()
    
    # Get all tables in the public schema
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    result = conn.execute(sa.text(query))
    tables = [row[0] for row in result]
    
    # Process each table
    for table_name in tables:
        # Skip excluded tables
        if table_name in EXCLUDED_TABLES:
            continue
            
        # Skip tables that already have the fields
        if table_name in TABLES_WITH_EXISTING_FIELDS:
            continue
        
        # Check if columns already exist
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = :table_name 
        AND column_name IN ('created_by_id', 'updated_by_id');
        """
        
        existing_cols = conn.execute(
            sa.text(check_query), 
            {"table_name": table_name}
        ).fetchall()
        existing_col_names = {col[0] for col in existing_cols}
        
        # Add created_by_id if it doesn't exist
        if 'created_by_id' not in existing_col_names:
            op.add_column(
                table_name,
                sa.Column(
                    'created_by_id',
                    sa.Integer(),
                    sa.ForeignKey('users.user_id', ondelete='SET NULL'),
                    nullable=True,
                    comment='ID of user who created this record'
                )
            )
            
            # Create index
            op.create_index(
                f'idx_{table_name}_created_by',
                table_name,
                ['created_by_id']
            )
        
        # Add updated_by_id if it doesn't exist
        if 'updated_by_id' not in existing_col_names:
            op.add_column(
                table_name,
                sa.Column(
                    'updated_by_id',
                    sa.Integer(),
                    sa.ForeignKey('users.user_id', ondelete='SET NULL'),
                    nullable=True,
                    comment='ID of user who last updated this record'
                )
            )
            
            # Create index
            op.create_index(
                f'idx_{table_name}_updated_by',
                table_name,
                ['updated_by_id']
            )


def downgrade() -> None:
    """Remove created_by_id and updated_by_id from all tables"""
    
    # Get connection
    conn = op.get_bind()
    
    # Get all tables
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    result = conn.execute(sa.text(query))
    tables = [row[0] for row in result]
    
    # Process each table
    for table_name in tables:
        # Skip excluded tables
        if table_name in EXCLUDED_TABLES:
            continue
            
        # Skip tables that originally had the fields
        if table_name in TABLES_WITH_EXISTING_FIELDS:
            continue
        
        # Drop indexes
        op.drop_index(f'idx_{table_name}_created_by', table_name, if_exists=True)
        op.drop_index(f'idx_{table_name}_updated_by', table_name, if_exists=True)
        
        # Drop columns
        try:
            op.drop_column(table_name, 'created_by_id')
        except:
            pass
            
        try:
            op.drop_column(table_name, 'updated_by_id')
        except:
            pass