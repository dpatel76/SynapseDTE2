"""Drop Legacy Planning Tables

Revision ID: 2025_07_18_drop_legacy_planning
Revises: 2025_07_18_planning_phase
Create Date: 2025-07-18 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers
revision = '2025_07_18_drop_legacy_planning'
down_revision = '2025_07_18_planning_phase'
branch_labels = None
depends_on = None

def upgrade():
    """Drop legacy planning tables"""
    
    # IMPORTANT: DO NOT DROP THE NEW UNIFIED PLANNING TABLES!
    # The new unified architecture uses these tables:
    # - cycle_report_planning_versions (NEW - DO NOT DROP)
    # - cycle_report_planning_data_sources (NEW - DO NOT DROP) 
    # - cycle_report_planning_attributes (NEW - DO NOT DROP)
    # - cycle_report_planning_pde_mappings (NEW - DO NOT DROP)
    
    # Only drop the OLD review and approval workflow tables
    # These are being replaced by the new PDE mapping review system
    op.execute("DROP TABLE IF EXISTS cycle_report_planning_pde_mapping_review_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS cycle_report_planning_pde_mapping_reviews CASCADE;")
    op.execute("DROP TABLE IF EXISTS cycle_report_planning_pde_mapping_approval_rules CASCADE;")
    
    # Drop old classification table if it exists separately (may not exist)
    op.execute("DROP TABLE IF EXISTS cycle_report_planning_pde_classifications_old CASCADE;")
    
    # Drop old attribute version history table (replaced by new versioning system)
    op.execute("DROP TABLE IF EXISTS cycle_report_planning_attribute_version_history CASCADE;")
    
    # NOTE: We are NOT dropping the main tables because they are part of the NEW architecture:
    # - cycle_report_planning_pde_mappings (KEEP - part of new unified system)
    # - cycle_report_planning_data_sources (KEEP - part of new unified system)
    # - cycle_report_planning_attributes (KEEP - part of new unified system)
    
    # Drop only old/unused sequences and enums - NOT the ones used by new tables
    # NOTE: The new planning tables use UUIDs with gen_random_uuid(), not sequences
    
    # Drop only legacy enums that are not part of the new system
    op.execute("DROP TYPE IF EXISTS planning_review_decision CASCADE;")
    op.execute("DROP TYPE IF EXISTS planning_approval_status CASCADE;")
    
    # NOTE: We are NOT dropping these because they are used by the NEW unified system:
    # - planning_version_status (used by cycle_report_planning_versions)
    # - planning_data_source_type (used by cycle_report_planning_data_sources)  
    # - planning_attribute_data_type (used by cycle_report_planning_attributes)
    # - planning_info_security_classification (used by cycle_report_planning_attributes)
    # - planning_mapping_type (used by cycle_report_planning_pde_mappings)
    # - planning_decision (used by cycle_report_planning_attributes)
    # - planning_status (used by cycle_report_planning_attributes)


def downgrade():
    """This migration is not reversible as it drops legacy tables"""
    
    # Note: This migration is not reversible because we're dropping legacy tables
    # that are being replaced by the new unified architecture.
    # If you need to rollback, you would need to restore from a backup.
    
    raise Exception(
        "Cannot rollback this migration. Legacy planning tables have been dropped "
        "and replaced by the new unified architecture. To rollback, restore from backup."
    )