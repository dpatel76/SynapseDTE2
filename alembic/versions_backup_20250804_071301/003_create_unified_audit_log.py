"""Create unified audit log table

Revision ID: 003_create_unified_audit_log
Revises: 002_seed_rbac_data
Create Date: 2024-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_unified_audit_log'
down_revision = '002_seed_rbac_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create unified audit log table with immutability features"""
    
    # Create unified audit log table
    op.create_table('unified_audit_log',
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), 
                  server_default=sa.text('gen_random_uuid()'), 
                  nullable=False, primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'), 
                  nullable=False),
        sa.Column('user_id', sa.Integer(), 
                  sa.ForeignKey('users.user_id', ondelete='SET NULL'), 
                  nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        
        # What was affected
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('operation', sa.String(50), nullable=False),
        
        # Change details
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('changes', postgresql.JSONB(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('change_ticket', sa.String(100), nullable=True),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), nullable=True),
        
        # Security and integrity
        sa.Column('signature', sa.String(256), nullable=True),
        sa.Column('previous_audit_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Compliance fields
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('requires_review', sa.Boolean(), default=False),
        sa.Column('reviewed_by', sa.Integer(), 
                  sa.ForeignKey('users.user_id', ondelete='SET NULL'), 
                  nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        
        # Indexes
        sa.Index('idx_unified_audit_timestamp', 'timestamp'),
        sa.Index('idx_unified_audit_user', 'user_id', 'timestamp'),
        sa.Index('idx_unified_audit_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_unified_audit_operation', 'operation'),
        sa.Index('idx_unified_audit_session', 'session_id'),
        sa.Index('idx_unified_audit_review', 'requires_review', 'reviewed_by'),
        
        # GIN index for JSONB queries
        sa.Index('idx_unified_audit_changes_gin', 'changes', 
                 postgresql_using='gin'),
        sa.Index('idx_unified_audit_metadata_gin', 'metadata', 
                 postgresql_using='gin')
    )
    
    # Create immutability trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_update()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                -- Only allow updating review fields
                IF OLD.audit_id != NEW.audit_id OR
                   OLD.timestamp != NEW.timestamp OR
                   OLD.user_id IS DISTINCT FROM NEW.user_id OR
                   OLD.entity_type != NEW.entity_type OR
                   OLD.entity_id IS DISTINCT FROM NEW.entity_id OR
                   OLD.operation != NEW.operation OR
                   OLD.old_values IS DISTINCT FROM NEW.old_values OR
                   OLD.new_values IS DISTINCT FROM NEW.new_values OR
                   OLD.changes IS DISTINCT FROM NEW.changes OR
                   OLD.signature IS DISTINCT FROM NEW.signature THEN
                    RAISE EXCEPTION 'Audit log records are immutable except for review fields';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to enforce immutability
    op.execute("""
        CREATE TRIGGER enforce_audit_log_immutability
        BEFORE UPDATE ON unified_audit_log
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_update();
    """)
    
    # Create function to calculate audit signature
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_audit_signature(
            p_audit_id UUID,
            p_timestamp TIMESTAMPTZ,
            p_user_id INTEGER,
            p_entity_type VARCHAR,
            p_entity_id VARCHAR,
            p_operation VARCHAR,
            p_changes JSONB,
            p_previous_signature VARCHAR
        )
        RETURNS VARCHAR AS $$
        DECLARE
            v_data_string TEXT;
            v_signature VARCHAR;
        BEGIN
            -- Concatenate all critical fields
            v_data_string := COALESCE(p_audit_id::TEXT, '') || '|' ||
                           COALESCE(p_timestamp::TEXT, '') || '|' ||
                           COALESCE(p_user_id::TEXT, '') || '|' ||
                           COALESCE(p_entity_type, '') || '|' ||
                           COALESCE(p_entity_id, '') || '|' ||
                           COALESCE(p_operation, '') || '|' ||
                           COALESCE(p_changes::TEXT, '') || '|' ||
                           COALESCE(p_previous_signature, '');
            
            -- Calculate SHA-256 hash
            v_signature := encode(sha256(v_data_string::bytea), 'hex');
            
            RETURN v_signature;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)
    
    # Create trigger to automatically calculate signature
    op.execute("""
        CREATE OR REPLACE FUNCTION set_audit_signature()
        RETURNS TRIGGER AS $$
        DECLARE
            v_previous_signature VARCHAR;
        BEGIN
            -- Get previous audit record signature for chaining
            SELECT signature INTO v_previous_signature
            FROM unified_audit_log
            WHERE audit_id != NEW.audit_id
            ORDER BY timestamp DESC
            LIMIT 1;
            
            -- Calculate signature
            NEW.signature := calculate_audit_signature(
                NEW.audit_id,
                NEW.timestamp,
                NEW.user_id,
                NEW.entity_type,
                NEW.entity_id,
                NEW.operation,
                NEW.changes,
                v_previous_signature
            );
            
            -- Set previous audit ID for chain
            SELECT audit_id INTO NEW.previous_audit_id
            FROM unified_audit_log
            WHERE audit_id != NEW.audit_id
            ORDER BY timestamp DESC
            LIMIT 1;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for signature calculation
    op.execute("""
        CREATE TRIGGER calculate_audit_signature_trigger
        BEFORE INSERT ON unified_audit_log
        FOR EACH ROW
        EXECUTE FUNCTION set_audit_signature();
    """)
    
    # Create view for audit trail analysis
    op.execute("""
        CREATE OR REPLACE VIEW audit_trail_analysis AS
        SELECT 
            a.audit_id,
            a.timestamp,
            u.username,
            u.full_name,
            a.entity_type,
            a.entity_id,
            a.operation,
            a.change_reason,
            a.risk_score,
            a.requires_review,
            reviewer.username as reviewed_by_username,
            a.reviewed_at,
            jsonb_array_length(
                COALESCE(jsonb_agg(DISTINCT k) FILTER (WHERE k IS NOT NULL), '[]'::jsonb)
            ) as fields_changed
        FROM unified_audit_log a
        LEFT JOIN users u ON a.user_id = u.user_id
        LEFT JOIN users reviewer ON a.reviewed_by = reviewer.user_id
        LEFT JOIN LATERAL jsonb_object_keys(a.changes) k ON true
        GROUP BY 
            a.audit_id, a.timestamp, u.username, u.full_name,
            a.entity_type, a.entity_id, a.operation, a.change_reason,
            a.risk_score, a.requires_review, reviewer.username, a.reviewed_at;
    """)
    
    # Create table for audit retention policies
    op.create_table('audit_retention_policies',
        sa.Column('policy_id', sa.Integer(), primary_key=True),
        sa.Column('entity_type', sa.String(100), nullable=False, unique=True),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('archive_after_days', sa.Integer(), nullable=True),
        sa.Column('delete_after_days', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Insert default retention policies
    op.execute("""
        INSERT INTO audit_retention_policies 
        (entity_type, retention_days, archive_after_days, delete_after_days, is_active)
        VALUES 
        ('user_authentication', 2555, 365, 2555, true),  -- 7 years
        ('data_modification', 2555, 365, 2555, true),
        ('approval_decision', 2555, 365, 2555, true),
        ('llm_operation', 1095, 180, 1095, true),        -- 3 years
        ('document_access', 730, 90, 730, true),         -- 2 years
        ('system_configuration', 2555, 365, 2555, true),
        ('default', 2555, 365, 2555, true);
    """)


def downgrade() -> None:
    """Remove unified audit log and related objects"""
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS audit_trail_analysis")
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS calculate_audit_signature_trigger ON unified_audit_log")
    op.execute("DROP TRIGGER IF EXISTS enforce_audit_log_immutability ON unified_audit_log")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS set_audit_signature()")
    op.execute("DROP FUNCTION IF EXISTS calculate_audit_signature(UUID, TIMESTAMPTZ, INTEGER, VARCHAR, VARCHAR, VARCHAR, JSONB, VARCHAR)")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_update()")
    
    # Drop tables
    op.drop_table('audit_retention_policies')
    op.drop_table('unified_audit_log')