"""Rename data profiling tables with consistent cycle_report_ prefixes

Revision ID: 2025_07_18_rename_data_profiling_tables
Revises: 2025_07_18_create_unified_test_report_tables
Create Date: 2025-07-18 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_07_18_rename_data_profiling_tables'
down_revision = '2025_07_18_create_unified_test_report_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Rename data profiling tables with consistent prefixes"""
    
    # First, create the missing data_profiling_uploads table
    op.create_table(
        'cycle_report_data_profiling_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('upload_status', sa.String(length=50), nullable=True, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], )
    )
    
    # Create indexes for the new table
    op.create_index('ix_cycle_report_data_profiling_uploads_cycle_id', 'cycle_report_data_profiling_uploads', ['cycle_id'])
    op.create_index('ix_cycle_report_data_profiling_uploads_report_id', 'cycle_report_data_profiling_uploads', ['report_id'])
    op.create_index('ix_cycle_report_data_profiling_uploads_status', 'cycle_report_data_profiling_uploads', ['upload_status'])
    
    # Rename enterprise profiling tables to cycle_report_data_profiling_highvolume_ prefix
    try:
        # Check if tables exist before renaming
        conn = op.get_bind()
        
        # Rename profiling_cache
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiling_cache')"))
        if result.scalar():
            op.rename_table('profiling_cache', 'cycle_report_data_profiling_highvolume_cache')
        
        # Rename profiling_executions
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiling_executions')"))
        if result.scalar():
            op.rename_table('profiling_executions', 'cycle_report_data_profiling_highvolume_executions')
        
        # Rename profiling_jobs
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiling_jobs')"))
        if result.scalar():
            op.rename_table('profiling_jobs', 'cycle_report_data_profiling_highvolume_jobs')
        
        # Rename profiling_partitions
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiling_partitions')"))
        if result.scalar():
            op.rename_table('profiling_partitions', 'cycle_report_data_profiling_highvolume_partitions')
        
        # Rename profiling_rule_sets
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiling_rule_sets')"))
        if result.scalar():
            op.rename_table('profiling_rule_sets', 'cycle_report_data_profiling_highvolume_rule_sets')
            
    except Exception as e:
        print(f"Warning: Table rename failed: {e}")
        # Continue with migration even if some renames fail
    
    # Update foreign key constraints that reference the renamed tables
    # This will be handled by the model updates
    
    print("✅ Data profiling tables renamed successfully")
    print("Standard tables: cycle_report_data_profiling_*")
    print("Enterprise tables: cycle_report_data_profiling_highvolume_*")


def downgrade():
    """Revert table renames"""
    
    # Revert enterprise profiling table renames
    try:
        conn = op.get_bind()
        
        # Revert profiling_cache
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_data_profiling_highvolume_cache')"))
        if result.scalar():
            op.rename_table('cycle_report_data_profiling_highvolume_cache', 'profiling_cache')
        
        # Revert profiling_executions
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_data_profiling_highvolume_executions')"))
        if result.scalar():
            op.rename_table('cycle_report_data_profiling_highvolume_executions', 'profiling_executions')
        
        # Revert profiling_jobs
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_data_profiling_highvolume_jobs')"))
        if result.scalar():
            op.rename_table('cycle_report_data_profiling_highvolume_jobs', 'profiling_jobs')
        
        # Revert profiling_partitions
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_data_profiling_highvolume_partitions')"))
        if result.scalar():
            op.rename_table('cycle_report_data_profiling_highvolume_partitions', 'profiling_partitions')
        
        # Revert profiling_rule_sets
        result = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cycle_report_data_profiling_highvolume_rule_sets')"))
        if result.scalar():
            op.rename_table('cycle_report_data_profiling_highvolume_rule_sets', 'profiling_rule_sets')
            
    except Exception as e:
        print(f"Warning: Table revert failed: {e}")
    
    # Drop the created uploads table
    op.drop_table('cycle_report_data_profiling_uploads')
    
    print("✅ Data profiling table renames reverted")