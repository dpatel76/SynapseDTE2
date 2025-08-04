"""Add data source and PDE mapping tables

Revision ID: add_data_source_pde_tables
Revises: 
Create Date: 2024-07-12 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_data_source_pde_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for data source types
    op.execute("""
        CREATE TYPE datasourcetype AS ENUM (
            'postgresql', 'mysql', 'oracle', 'sqlserver', 'mongodb',
            'csv', 'excel', 'api', 'sftp', 's3'
        )
    """)
    
    # Create cycle_report_data_sources table
    op.create_table('cycle_report_data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_type', postgresql.ENUM('postgresql', 'mysql', 'oracle', 'sqlserver', 'mongodb', 
                                                  'csv', 'excel', 'api', 'sftp', 's3', 
                                                  name='datasourcetype'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('connection_config', sa.JSON(), nullable=True),
        sa.Column('auth_type', sa.String(length=50), nullable=True),
        sa.Column('auth_config', sa.JSON(), nullable=True),
        sa.Column('refresh_schedule', sa.String(length=100), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_message', sa.Text(), nullable=True),
        sa.Column('validation_rules', sa.JSON(), nullable=True),
        
        # Audit columns
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create cycle_report_pde_mappings table
    op.create_table('cycle_report_pde_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('data_source_id', sa.Integer(), nullable=True),
        
        # PDE information
        sa.Column('pde_name', sa.String(length=255), nullable=False),
        sa.Column('pde_code', sa.String(length=100), nullable=False),
        sa.Column('pde_description', sa.Text(), nullable=True),
        
        # Mapping details
        sa.Column('source_field', sa.String(length=255), nullable=True),
        sa.Column('transformation_rule', sa.JSON(), nullable=True),
        sa.Column('mapping_type', sa.String(length=50), nullable=True),
        
        # LLM-assisted mapping
        sa.Column('llm_suggested_mapping', sa.JSON(), nullable=True),
        sa.Column('llm_confidence_score', sa.Integer(), nullable=True),
        sa.Column('llm_mapping_rationale', sa.Text(), nullable=True),
        sa.Column('llm_alternative_mappings', sa.JSON(), nullable=True),
        sa.Column('mapping_confirmed_by_user', sa.Boolean(), nullable=True, default=False),
        
        # Business metadata
        sa.Column('business_process', sa.String(length=255), nullable=True),
        sa.Column('business_owner', sa.String(length=255), nullable=True),
        sa.Column('data_steward', sa.String(length=255), nullable=True),
        
        # Classification
        sa.Column('criticality', sa.String(length=50), nullable=True),
        sa.Column('risk_level', sa.String(length=50), nullable=True),
        sa.Column('regulatory_flag', sa.Boolean(), nullable=True, default=False),
        sa.Column('pii_flag', sa.Boolean(), nullable=True, default=False),
        
        # LLM-assisted classification
        sa.Column('llm_suggested_criticality', sa.String(length=50), nullable=True),
        sa.Column('llm_suggested_risk_level', sa.String(length=50), nullable=True),
        sa.Column('llm_classification_rationale', sa.Text(), nullable=True),
        sa.Column('llm_regulatory_references', sa.JSON(), nullable=True),
        
        # Validation
        sa.Column('is_validated', sa.Boolean(), nullable=True, default=False),
        sa.Column('validation_message', sa.Text(), nullable=True),
        
        # Audit columns
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['attribute_id'], ['cycle_report_attributes_planning.attribute_id'], ),
        sa.ForeignKeyConstraint(['cycle_id'], ['test_cycles.cycle_id'], ),
        sa.ForeignKeyConstraint(['data_source_id'], ['cycle_report_data_sources.id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pde_code')
    )
    
    # Create cycle_report_pde_classifications table
    op.create_table('cycle_report_pde_classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pde_mapping_id', sa.Integer(), nullable=False),
        
        # Classification details
        sa.Column('classification_type', sa.String(length=100), nullable=False),
        sa.Column('classification_value', sa.String(length=100), nullable=False),
        sa.Column('classification_reason', sa.Text(), nullable=True),
        
        # Supporting evidence
        sa.Column('evidence_type', sa.String(length=100), nullable=True),
        sa.Column('evidence_reference', sa.String(length=500), nullable=True),
        sa.Column('evidence_details', sa.JSON(), nullable=True),
        
        # Review and approval
        sa.Column('classified_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('review_status', sa.String(length=50), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        
        # Audit columns
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['approved_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['classified_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['pde_mapping_id'], ['cycle_report_pde_mappings.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_data_sources_cycle_report', 'cycle_report_data_sources', ['cycle_id', 'report_id'])
    op.create_index('idx_pde_mappings_cycle_report', 'cycle_report_pde_mappings', ['cycle_id', 'report_id'])
    op.create_index('idx_pde_mappings_attribute', 'cycle_report_pde_mappings', ['attribute_id'])
    op.create_index('idx_pde_classifications_mapping', 'cycle_report_pde_classifications', ['pde_mapping_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_pde_classifications_mapping', table_name='cycle_report_pde_classifications')
    op.drop_index('idx_pde_mappings_attribute', table_name='cycle_report_pde_mappings')
    op.drop_index('idx_pde_mappings_cycle_report', table_name='cycle_report_pde_mappings')
    op.drop_index('idx_data_sources_cycle_report', table_name='cycle_report_data_sources')
    
    # Drop tables
    op.drop_table('cycle_report_pde_classifications')
    op.drop_table('cycle_report_pde_mappings')
    op.drop_table('cycle_report_data_sources')
    
    # Drop enum type
    op.execute('DROP TYPE datasourcetype')