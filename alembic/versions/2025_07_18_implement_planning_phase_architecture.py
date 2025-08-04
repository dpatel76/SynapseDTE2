"""Implement Planning Phase Architecture - Unified System

Revision ID: 2025_07_18_planning_phase
Revises: 2025_07_11_redesign_migration
Create Date: 2025-07-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers
revision = '2025_07_18_planning_phase'
down_revision = '2025_07_11_redesign_migration'
branch_labels = None
depends_on = None

def upgrade():
    """Create the new unified planning phase architecture"""
    
    # Create the version status enum
    op.execute("""
        CREATE TYPE planning_version_status AS ENUM (
            'draft', 'pending_approval', 'approved', 'rejected', 'superseded'
        );
    """)
    
    # Create data source type enum
    op.execute("""
        CREATE TYPE planning_data_source_type AS ENUM (
            'database', 'file', 'api', 'sftp', 's3', 'other'
        );
    """)
    
    # Create attribute data type enum
    op.execute("""
        CREATE TYPE planning_attribute_data_type AS ENUM (
            'string', 'integer', 'decimal', 'boolean', 'date', 'datetime', 'text'
        );
    """)
    
    # Create information security classification enum
    op.execute("""
        CREATE TYPE planning_info_security_classification AS ENUM (
            'public', 'internal', 'confidential', 'restricted'
        );
    """)
    
    # Create mapping type enum
    op.execute("""
        CREATE TYPE planning_mapping_type AS ENUM (
            'direct', 'calculated', 'lookup', 'conditional'
        );
    """)
    
    # Create decision enum
    op.execute("""
        CREATE TYPE planning_decision AS ENUM (
            'approve', 'reject', 'request_changes'
        );
    """)
    
    # Create status enum
    op.execute("""
        CREATE TYPE planning_status AS ENUM (
            'pending', 'approved', 'rejected'
        );
    """)
    
    # Table 1: Planning Version Management
    op.create_table('cycle_report_planning_versions',
        sa.Column('version_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
        
        # Phase Integration
        sa.Column('phase_id', sa.Integer(), nullable=False),
        sa.Column('workflow_activity_id', sa.Integer(), nullable=True),
        
        # Version Management
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_status', postgresql.ENUM('draft', 'pending_approval', 'approved', 'rejected', 'superseded', name='planning_version_status'), nullable=False, default='draft'),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Temporal Workflow Context
        sa.Column('workflow_execution_id', sa.String(255), nullable=True),
        sa.Column('workflow_run_id', sa.String(255), nullable=True),
        
        # Planning Summary Statistics
        sa.Column('total_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('approved_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('pk_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('cde_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('mandatory_attributes', sa.Integer(), nullable=False, default=0),
        sa.Column('total_data_sources', sa.Integer(), nullable=False, default=0),
        sa.Column('approved_data_sources', sa.Integer(), nullable=False, default=0),
        sa.Column('total_pde_mappings', sa.Integer(), nullable=False, default=0),
        sa.Column('approved_pde_mappings', sa.Integer(), nullable=False, default=0),
        
        # LLM Generation Summary
        sa.Column('llm_generation_summary', postgresql.JSONB(), nullable=True),
        
        # Tester-Only Approval Workflow
        sa.Column('submitted_by_id', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        
        # Audit Fields
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer(), nullable=False),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['workflow_activity_id'], ['workflow_activities.activity_id'], ),
        sa.ForeignKeyConstraint(['parent_version_id'], ['cycle_report_planning_versions.version_id'], ),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        
        # Constraints
        sa.UniqueConstraint('phase_id', 'version_number', name='uq_planning_version_phase_number'),
    )
    
    # Table 2: Phase-Level Data Sources
    op.create_table('cycle_report_planning_data_sources',
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
        
        # Version Reference
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Phase Integration
        sa.Column('phase_id', sa.Integer(), nullable=False),
        
        # Data Source Definition
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('source_type', postgresql.ENUM('database', 'file', 'api', 'sftp', 's3', 'other', name='planning_data_source_type'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Connection Configuration
        sa.Column('connection_config', postgresql.JSONB(), nullable=False),
        
        # Authentication Configuration
        sa.Column('auth_config', postgresql.JSONB(), nullable=True),
        
        # Data Source Metadata
        sa.Column('refresh_schedule', sa.String(100), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(), nullable=True),
        sa.Column('estimated_record_count', sa.Integer(), nullable=True),
        sa.Column('data_freshness_hours', sa.Integer(), nullable=True),
        
        # Tester Decision
        sa.Column('tester_decision', postgresql.ENUM('approve', 'reject', 'request_changes', name='planning_decision'), nullable=True),
        sa.Column('tester_decided_by', sa.Integer(), nullable=True),
        sa.Column('tester_decided_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('tester_notes', sa.Text(), nullable=True),
        
        # Status
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='planning_status'), nullable=False, default='pending'),
        
        # Audit Fields
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer(), nullable=False),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['version_id'], ['cycle_report_planning_versions.version_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['tester_decided_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        
        # Constraints
        sa.UniqueConstraint('version_id', 'source_name', name='uq_planning_data_source_version_name'),
    )
    
    # Table 3: Individual Planning Attributes
    op.create_table('cycle_report_planning_attributes',
        sa.Column('attribute_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
        
        # Version Reference
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Phase Integration
        sa.Column('phase_id', sa.Integer(), nullable=False),
        
        # Attribute Definition
        sa.Column('attribute_name', sa.String(255), nullable=False),
        sa.Column('data_type', postgresql.ENUM('string', 'integer', 'decimal', 'boolean', 'date', 'datetime', 'text', name='planning_attribute_data_type'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('business_definition', sa.Text(), nullable=True),
        
        # Attribute Characteristics
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_cde', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_primary_key', sa.Boolean(), nullable=False, default=False),
        sa.Column('max_length', sa.Integer(), nullable=True),
        
        # Information Security Classification
        sa.Column('information_security_classification', postgresql.ENUM('public', 'internal', 'confidential', 'restricted', name='planning_info_security_classification'), nullable=False, default='internal'),
        
        # LLM Assistance Metadata
        sa.Column('llm_metadata', postgresql.JSONB(), nullable=True),
        
        # Tester Decision
        sa.Column('tester_decision', postgresql.ENUM('approve', 'reject', 'request_changes', name='planning_decision'), nullable=True),
        sa.Column('tester_decided_by', sa.Integer(), nullable=True),
        sa.Column('tester_decided_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('tester_notes', sa.Text(), nullable=True),
        
        # Status
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='planning_status'), nullable=False, default='pending'),
        
        # Audit Fields
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer(), nullable=False),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['version_id'], ['cycle_report_planning_versions.version_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['tester_decided_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        
        # Constraints
        sa.UniqueConstraint('version_id', 'attribute_name', name='uq_planning_attribute_version_name'),
    )
    
    # Table 4: PDE Mappings
    op.create_table('cycle_report_planning_pde_mappings',
        sa.Column('pde_mapping_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')),
        
        # Version and Attribute References
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attribute_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('data_source_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Phase Integration
        sa.Column('phase_id', sa.Integer(), nullable=False),
        
        # PDE Definition
        sa.Column('pde_name', sa.String(255), nullable=False),
        sa.Column('pde_code', sa.String(100), nullable=False),
        sa.Column('mapping_type', postgresql.ENUM('direct', 'calculated', 'lookup', 'conditional', name='planning_mapping_type'), nullable=False, default='direct'),
        
        # Data Source Mapping
        sa.Column('source_table', sa.String(255), nullable=False),
        sa.Column('source_column', sa.String(255), nullable=False),
        sa.Column('source_field', sa.String(500), nullable=False),
        sa.Column('column_data_type', sa.String(100), nullable=True),
        sa.Column('transformation_rule', sa.Text(), nullable=True),
        sa.Column('condition_rule', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        
        # PDE Classification
        sa.Column('classification', postgresql.JSONB(), nullable=True),
        
        # LLM Assistance
        sa.Column('llm_metadata', postgresql.JSONB(), nullable=True),
        
        # Tester Decision
        sa.Column('tester_decision', postgresql.ENUM('approve', 'reject', 'request_changes', name='planning_decision'), nullable=True),
        sa.Column('tester_decided_by', sa.Integer(), nullable=True),
        sa.Column('tester_decided_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('tester_notes', sa.Text(), nullable=True),
        sa.Column('auto_approved', sa.Boolean(), nullable=False, default=False),
        
        # Status
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='planning_status'), nullable=False, default='pending'),
        
        # Audit Fields
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_by_id', sa.Integer(), nullable=False),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['version_id'], ['cycle_report_planning_versions.version_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['cycle_report_planning_attributes.attribute_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['data_source_id'], ['cycle_report_planning_data_sources.data_source_id'], ),
        sa.ForeignKeyConstraint(['phase_id'], ['workflow_phases.phase_id'], ),
        sa.ForeignKeyConstraint(['tester_decided_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.user_id'], ),
        
        # Constraints
        sa.UniqueConstraint('version_id', 'attribute_id', 'pde_code', name='uq_planning_pde_mapping_version_attribute_code'),
    )
    
    # Create indexes for performance
    op.create_index('idx_cycle_report_planning_versions_phase', 'cycle_report_planning_versions', ['phase_id'])
    op.create_index('idx_cycle_report_planning_versions_status', 'cycle_report_planning_versions', ['version_status'])
    op.create_index('idx_cycle_report_planning_versions_parent', 'cycle_report_planning_versions', ['parent_version_id'])
    
    op.create_index('idx_cycle_report_planning_data_sources_version', 'cycle_report_planning_data_sources', ['version_id'])
    op.create_index('idx_cycle_report_planning_data_sources_phase', 'cycle_report_planning_data_sources', ['phase_id'])
    op.create_index('idx_cycle_report_planning_data_sources_status', 'cycle_report_planning_data_sources', ['status'])
    op.create_index('idx_cycle_report_planning_data_sources_type', 'cycle_report_planning_data_sources', ['source_type'])
    
    op.create_index('idx_cycle_report_planning_attributes_version', 'cycle_report_planning_attributes', ['version_id'])
    op.create_index('idx_cycle_report_planning_attributes_phase', 'cycle_report_planning_attributes', ['phase_id'])
    op.create_index('idx_cycle_report_planning_attributes_status', 'cycle_report_planning_attributes', ['status'])
    op.create_index('idx_cycle_report_planning_attributes_cde', 'cycle_report_planning_attributes', ['is_cde'])
    op.create_index('idx_cycle_report_planning_attributes_pk', 'cycle_report_planning_attributes', ['is_primary_key'])
    
    op.create_index('idx_cycle_report_planning_pde_mappings_version', 'cycle_report_planning_pde_mappings', ['version_id'])
    op.create_index('idx_cycle_report_planning_pde_mappings_attribute', 'cycle_report_planning_pde_mappings', ['attribute_id'])
    op.create_index('idx_cycle_report_planning_pde_mappings_data_source', 'cycle_report_planning_pde_mappings', ['data_source_id'])
    op.create_index('idx_cycle_report_planning_pde_mappings_phase', 'cycle_report_planning_pde_mappings', ['phase_id'])
    op.create_index('idx_cycle_report_planning_pde_mappings_status', 'cycle_report_planning_pde_mappings', ['status'])
    op.create_index('idx_cycle_report_planning_pde_mappings_code', 'cycle_report_planning_pde_mappings', ['pde_code'])


def downgrade():
    """Drop the planning phase architecture"""
    
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('cycle_report_planning_pde_mappings')
    op.drop_table('cycle_report_planning_attributes')
    op.drop_table('cycle_report_planning_data_sources')
    op.drop_table('cycle_report_planning_versions')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS planning_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS planning_decision CASCADE;")
    op.execute("DROP TYPE IF EXISTS planning_mapping_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS planning_info_security_classification CASCADE;")
    op.execute("DROP TYPE IF EXISTS planning_attribute_data_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS planning_data_source_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS planning_version_status CASCADE;")