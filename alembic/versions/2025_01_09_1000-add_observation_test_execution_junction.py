"""add_observation_test_execution_junction

Revision ID: add_obs_test_exec_junction
Revises: add_calculated_status
Create Date: 2025-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_obs_test_exec_junction'
down_revision = 'add_calculated_status'
branch_labels = None
depends_on = None


def upgrade():
    # Create the junction table for observation to test execution mapping
    op.create_table(
        'cycle_report_observation_mgmt_test_executions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('observation_id', sa.Integer(), sa.ForeignKey('cycle_report_observation_mgmt_observation_records.observation_id', ondelete='CASCADE'), nullable=False),
        sa.Column('test_execution_id', sa.Integer(), sa.ForeignKey('cycle_report_test_execution_results.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), default=False, nullable=False),
        sa.Column('linked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('linked_by_id', sa.Integer(), sa.ForeignKey('users.user_id'), nullable=True),
        sa.UniqueConstraint('observation_id', 'test_execution_id', name='uq_obs_test_exec'),
        sa.Index('idx_obs_test_exec_observation', 'observation_id'),
        sa.Index('idx_obs_test_exec_test_execution', 'test_execution_id')
    )
    
    # Migrate existing data from source_test_execution_id and supporting_data JSON
    op.execute("""
        -- First, insert primary test executions
        INSERT INTO cycle_report_observation_mgmt_test_executions (observation_id, test_execution_id, is_primary, linked_by_id)
        SELECT 
            observation_id,
            source_test_execution_id,
            true as is_primary,
            created_by_id as linked_by_id
        FROM cycle_report_observation_mgmt_observation_records
        WHERE source_test_execution_id IS NOT NULL;
        
        -- Then, insert linked test executions from supporting_data JSON
        INSERT INTO cycle_report_observation_mgmt_test_executions (observation_id, test_execution_id, is_primary, linked_by_id)
        SELECT DISTINCT
            o.observation_id,
            CAST(jsonb_array_elements_text(o.supporting_data->'linked_test_executions') AS INTEGER) as test_execution_id,
            false as is_primary,
            o.created_by_id as linked_by_id
        FROM cycle_report_observation_mgmt_observation_records o
        WHERE o.supporting_data IS NOT NULL 
        AND o.supporting_data->'linked_test_executions' IS NOT NULL
        AND jsonb_typeof(o.supporting_data->'linked_test_executions') = 'array'
        ON CONFLICT (observation_id, test_execution_id) DO NOTHING;
    """)
    
    # Drop the source_sample_record_id column as it should be derived from test cases
    op.drop_column('cycle_report_observation_mgmt_observation_records', 'source_sample_record_id')
    
    # Optionally keep source_test_execution_id for backward compatibility but mark it as deprecated
    # We'll keep it for now but can remove it in a future migration
    op.alter_column('cycle_report_observation_mgmt_observation_records', 'source_test_execution_id',
                    comment='DEPRECATED: Use cycle_report_observation_mgmt_test_executions table instead')


def downgrade():
    # Re-add the source_sample_record_id column
    op.add_column('cycle_report_observation_mgmt_observation_records',
                  sa.Column('source_sample_record_id', sa.String(), nullable=True))
    
    # Remove deprecation comment
    op.alter_column('cycle_report_observation_mgmt_observation_records', 'source_test_execution_id',
                    comment=None)
    
    # Drop the junction table
    op.drop_table('cycle_report_observation_mgmt_test_executions')