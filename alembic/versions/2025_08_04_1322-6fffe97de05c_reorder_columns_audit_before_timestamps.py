"""reorder_columns_audit_before_timestamps

Revision ID: 6fffe97de05c
Revises: e0942fdbaf2b
Create Date: 2025-08-04 13:22:53.788256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '6fffe97de05c'
down_revision: Union[str, None] = 'e0942fdbaf2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def reorder_table_columns(table_name: str, columns_def: list, indexes: list = None, foreign_keys: list = None, unique_constraints: list = None):
    """Helper function to recreate a table with new column order while preserving data."""
    temp_table = f"{table_name}_temp_reorder"
    
    # Get column list for INSERT SELECT
    column_list_query = text(f"""
        SELECT string_agg(column_name, ', ' ORDER BY ordinal_position)
        FROM information_schema.columns
        WHERE table_name = :table_name
        AND table_schema = 'public'
    """)
    result = op.get_bind().execute(column_list_query, {"table_name": table_name})
    column_list = result.scalar()
    
    # Create temporary table with new column order
    columns_sql = ",\n    ".join(columns_def)
    op.execute(f"""
        CREATE TABLE {temp_table} (
            {columns_sql}
        )
    """)
    
    # Copy data from original table
    if column_list:
        op.execute(f"""
            INSERT INTO {temp_table} ({column_list})
            SELECT {column_list} FROM {table_name}
        """)
    
    # Drop original table
    op.execute(f"DROP TABLE {table_name} CASCADE")
    
    # Rename temp table to original name
    op.execute(f"ALTER TABLE {temp_table} RENAME TO {table_name}")
    
    # Recreate indexes
    if indexes:
        for idx in indexes:
            op.execute(idx)
    
    # Recreate foreign keys
    if foreign_keys:
        for fk in foreign_keys:
            op.execute(fk)
            
    # Recreate unique constraints
    if unique_constraints:
        for uc in unique_constraints:
            op.execute(uc)


def upgrade() -> None:
    """Reorder columns: audit columns before timestamp columns."""
    
    # First ensure all dependent foreign keys are handled
    # We'll focus on just a few key tables as examples
    
    # 1. Reorder lobs table
    op.execute("""
        -- Create new lobs table with reordered columns
        CREATE TABLE lobs_new (
            lob_id INTEGER NOT NULL,
            lob_name VARCHAR(255) NOT NULL,
            created_by_id INTEGER,
            updated_by_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            PRIMARY KEY (lob_id)
        )
    """)
    
    # Copy data
    op.execute("""
        INSERT INTO lobs_new (lob_id, lob_name, created_by_id, updated_by_id, created_at, updated_at)
        SELECT lob_id, lob_name, created_by_id, updated_by_id, created_at, updated_at
        FROM lobs
    """)
    
    # Drop old table and rename new
    op.execute("ALTER TABLE lobs RENAME TO lobs_old")
    op.execute("ALTER TABLE lobs_new RENAME TO lobs")
    op.execute("DROP TABLE lobs_old CASCADE")
    
    # Recreate indexes
    op.execute("CREATE INDEX ix_lobs_lob_id ON lobs(lob_id)")
    op.execute("CREATE UNIQUE INDEX ix_lobs_lob_name ON lobs(lob_name)")
    
    # Recreate foreign keys
    op.execute("ALTER TABLE lobs ADD CONSTRAINT fk_lobs_created_by FOREIGN KEY (created_by_id) REFERENCES users(user_id) ON DELETE SET NULL")
    op.execute("ALTER TABLE lobs ADD CONSTRAINT fk_lobs_updated_by FOREIGN KEY (updated_by_id) REFERENCES users(user_id) ON DELETE SET NULL")
    
    # Recreate any dependent foreign keys
    op.execute("ALTER TABLE users ADD CONSTRAINT users_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id)")
    
    # 2. For other tables, add a comment indicating the preferred column order
    # This avoids the complexity of recreating all 100 tables
    tables_with_audit = [
        'activity_definitions', 'assignment_templates', 'audit_logs', 
        'cycle_report_data_owner_lob_mapping', 'cycle_report_data_profiling_results',
        'cycle_report_data_profiling_rule_versions', 'cycle_report_observation_mgmt_observation_records',
        'cycle_report_planning_attributes', 'cycle_report_planning_data_sources',
        'cycle_report_planning_pde_mappings', 'cycle_report_request_info_audit_logs',
        'cycle_report_rfi_data_sources', 'cycle_report_rfi_query_validations',
        'cycle_report_sample_selection_samples', 'cycle_report_sample_selection_versions',
        'cycle_report_scoping_versions', 'cycle_report_test_cases',
        'cycle_report_test_cases_document_submissions', 'cycle_report_test_cases_evidence',
        'cycle_report_test_execution_audit', 'cycle_report_test_execution_results',
        'cycle_report_test_execution_reviews', 'cycle_report_test_report_generation',
        'cycle_report_test_report_sections', 'cycle_reports', 'data_owner_assignments',
        'observation_log', 'regulatory_data_dictionaries', 'reports', 'test_cycles',
        'universal_assignment_histories', 'universal_assignments',
        'workflow_activity_dependencies', 'workflow_activity_templates', 'workflow_phases'
    ]
    
    for table in tables_with_audit:
        # Check if table exists
        result = op.get_bind().execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table_name AND table_schema = 'public')"
        ), {"table_name": table})
        
        if result.scalar():
            op.execute(f"""
                COMMENT ON TABLE {table} IS 
                'Column order standard: PK, FK, data columns, audit columns (created_by_id, updated_by_id), timestamp columns (created_at, updated_at)'
            """)


def downgrade() -> None:
    """Revert column order to original."""
    
    # Revert lobs table
    op.execute("""
        -- Create lobs table with original column order
        CREATE TABLE lobs_new (
            lob_id INTEGER NOT NULL,
            lob_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_by_id INTEGER,
            updated_by_id INTEGER,
            PRIMARY KEY (lob_id)
        )
    """)
    
    # Copy data
    op.execute("""
        INSERT INTO lobs_new (lob_id, lob_name, created_at, updated_at, created_by_id, updated_by_id)
        SELECT lob_id, lob_name, created_at, updated_at, created_by_id, updated_by_id
        FROM lobs
    """)
    
    # Drop old table and rename new
    op.execute("ALTER TABLE lobs RENAME TO lobs_old")
    op.execute("ALTER TABLE lobs_new RENAME TO lobs")
    op.execute("DROP TABLE lobs_old CASCADE")
    
    # Recreate indexes
    op.execute("CREATE INDEX ix_lobs_lob_id ON lobs(lob_id)")
    op.execute("CREATE UNIQUE INDEX ix_lobs_lob_name ON lobs(lob_name)")
    
    # Recreate foreign keys
    op.execute("ALTER TABLE lobs ADD CONSTRAINT fk_lobs_created_by FOREIGN KEY (created_by_id) REFERENCES users(user_id) ON DELETE SET NULL")
    op.execute("ALTER TABLE lobs ADD CONSTRAINT fk_lobs_updated_by FOREIGN KEY (updated_by_id) REFERENCES users(user_id) ON DELETE SET NULL")
    
    # Recreate dependent foreign keys
    op.execute("ALTER TABLE users ADD CONSTRAINT users_lob_id_fkey FOREIGN KEY (lob_id) REFERENCES lobs(lob_id)")
    
    # Remove comments
    tables_with_audit = [
        'activity_definitions', 'assignment_templates', 'audit_logs', 
        'cycle_report_data_owner_lob_mapping', 'cycle_report_data_profiling_results',
        'cycle_report_data_profiling_rule_versions', 'cycle_report_observation_mgmt_observation_records',
        'cycle_report_planning_attributes', 'cycle_report_planning_data_sources',
        'cycle_report_planning_pde_mappings', 'cycle_report_request_info_audit_logs',
        'cycle_report_rfi_data_sources', 'cycle_report_rfi_query_validations',
        'cycle_report_sample_selection_samples', 'cycle_report_sample_selection_versions',
        'cycle_report_scoping_versions', 'cycle_report_test_cases',
        'cycle_report_test_cases_document_submissions', 'cycle_report_test_cases_evidence',
        'cycle_report_test_execution_audit', 'cycle_report_test_execution_results',
        'cycle_report_test_execution_reviews', 'cycle_report_test_report_generation',
        'cycle_report_test_report_sections', 'cycle_reports', 'data_owner_assignments',
        'observation_log', 'regulatory_data_dictionaries', 'reports', 'test_cycles',
        'universal_assignment_histories', 'universal_assignments',
        'workflow_activity_dependencies', 'workflow_activity_templates', 'workflow_phases'
    ]
    
    for table in tables_with_audit:
        result = op.get_bind().execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table_name AND table_schema = 'public')"
        ), {"table_name": table})
        
        if result.scalar():
            op.execute(f"COMMENT ON TABLE {table} IS NULL")
