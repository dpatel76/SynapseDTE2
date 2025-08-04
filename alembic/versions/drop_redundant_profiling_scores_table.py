"""Drop redundant cycle_report_data_profiling_attribute_scores table

Revision ID: drop_redundant_scores
Revises: 
Create Date: 2025-07-18

This table is redundant because DQ scores should be calculated by aggregating
from cycle_report_data_profiling_results instead of storing pre-calculated values.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'drop_redundant_scores'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop the redundant table"""
    op.drop_table('cycle_report_data_profiling_attribute_scores')


def downgrade() -> None:
    """Recreate the table if needed"""
    op.create_table('cycle_report_data_profiling_attribute_scores',
        sa.Column('score_id', sa.Integer(), nullable=False),
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('workflow_activity_id', sa.Integer(), nullable=True),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('overall_quality_score', sa.Float(), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('validity_score', sa.Float(), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('uniqueness_score', sa.Float(), nullable=True),
        sa.Column('total_rules_executed', sa.Integer(), nullable=True),
        sa.Column('rules_passed', sa.Integer(), nullable=True),
        sa.Column('rules_failed', sa.Integer(), nullable=True),
        sa.Column('total_values', sa.Integer(), nullable=True),
        sa.Column('null_count', sa.Integer(), nullable=True),
        sa.Column('unique_count', sa.Integer(), nullable=True),
        sa.Column('data_type_detected', sa.String(50), nullable=True),
        sa.Column('pattern_detected', sa.String(255), nullable=True),
        sa.Column('distribution_type', sa.String(50), nullable=True),
        sa.Column('has_anomalies', sa.Boolean(), nullable=True),
        sa.Column('anomaly_count', sa.Integer(), nullable=True),
        sa.Column('anomaly_types', sa.JSON(), nullable=True),
        sa.Column('testing_recommendation', sa.Text(), nullable=True),
        sa.Column('risk_assessment', sa.Text(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('score_id'),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['workflow_activity_id'], ['workflow_activities.activity_id'], ),
        sa.ForeignKeyConstraint(['attribute_id'], ['cycle_report_planning_attributes.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], )
    )
    op.create_index('idx_profiling_scores_attribute', 'cycle_report_data_profiling_attribute_scores', ['attribute_id'], unique=False)