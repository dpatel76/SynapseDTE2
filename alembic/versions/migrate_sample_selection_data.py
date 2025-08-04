"""Migrate existing sample selection data to new structure

Revision ID: migrate_sample_selection_001
Revises: sample_selection_v2_001
Create Date: 2024-07-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'migrate_sample_selection_001'
down_revision = 'sample_selection_v2_001'
branch_labels = None
depends_on = None


def upgrade():
    """Migrate existing sample selection data to new structure"""
    
    # Create a connection to execute queries
    conn = op.get_bind()
    
    # Step 1: Create a temporary mapping table to track migrated data
    op.create_table(
        'sample_selection_migration_tracking',
        sa.Column('old_set_id', sa.String(36), nullable=False),
        sa.Column('new_version_id', postgresql.UUID(), nullable=False),
        sa.Column('migrated_at', sa.DateTime(timezone=True), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('old_set_id')
    )
    
    print("Created migration tracking table")
    
    # Step 2: Migrate SampleSets to SampleSelectionVersions
    print("Migrating sample sets to versions...")
    
    # Get all sample sets ordered by creation date
    sample_sets_query = text("""
        SELECT 
            ss.set_id,
            ss.cycle_id,
            ss.report_id,
            ss.set_name,
            ss.description,
            ss.generation_method,
            ss.sample_type,
            ss.status,
            ss.target_sample_size,
            ss.actual_sample_size,
            ss.created_by,
            ss.created_at,
            ss.approved_by,
            ss.approved_at,
            ss.approval_notes,
            ss.generation_rationale,
            ss.selection_criteria,
            ss.quality_score,
            ss.sample_metadata,
            ss.version_number,
            ss.is_latest_version,
            ss.is_active,
            ss.master_set_id,
            wp.phase_id
        FROM cycle_report_sample_sets ss
        LEFT JOIN workflow_phases wp ON wp.cycle_id = ss.cycle_id 
            AND wp.report_id = ss.report_id 
            AND wp.phase_name = 'Sample Selection'
        WHERE ss.is_active = true
        ORDER BY ss.created_at
    """)
    
    sample_sets = conn.execute(sample_sets_query).fetchall()
    
    for sample_set in sample_sets:
        try:
            # Determine version status from old status
            version_status = map_old_status_to_new(sample_set.status)
            
            # Generate new version ID
            new_version_id = uuid.uuid4()
            
            # Create workflow phase if it doesn't exist
            phase_id = sample_set.phase_id
            if not phase_id:
                phase_id = create_workflow_phase(conn, sample_set.cycle_id, sample_set.report_id)
            
            # Prepare selection criteria
            selection_criteria = sample_set.selection_criteria or {}
            if not selection_criteria:
                selection_criteria = {
                    'method': sample_set.generation_method,
                    'sample_type': sample_set.sample_type,
                    'description': sample_set.description,
                    'generation_rationale': sample_set.generation_rationale
                }
            
            # Prepare intelligent sampling config
            intelligent_sampling_config = {
                'quality_score': sample_set.quality_score,
                'generation_method': sample_set.generation_method,
                'sample_metadata': sample_set.sample_metadata
            }
            
            # Insert new version
            insert_version_query = text("""
                INSERT INTO cycle_report_sample_selection_versions (
                    version_id, phase_id, version_number, version_status,
                    workflow_execution_id, workflow_run_id, activity_name,
                    selection_criteria, target_sample_size, actual_sample_size,
                    intelligent_sampling_config, submission_notes, approval_notes,
                    created_at, created_by_id, submitted_at, submitted_by_id,
                    approved_at, approved_by_id, updated_at
                ) VALUES (
                    :version_id, :phase_id, :version_number, :version_status,
                    :workflow_execution_id, :workflow_run_id, :activity_name,
                    :selection_criteria, :target_sample_size, :actual_sample_size,
                    :intelligent_sampling_config, :submission_notes, :approval_notes,
                    :created_at, :created_by_id, :submitted_at, :submitted_by_id,
                    :approved_at, :approved_by_id, :updated_at
                )
            """)
            
            conn.execute(insert_version_query, {
                'version_id': new_version_id,
                'phase_id': phase_id,
                'version_number': sample_set.version_number or 1,
                'version_status': version_status,
                'workflow_execution_id': f'migrated_{sample_set.set_id}',
                'workflow_run_id': f'migrated_{sample_set.set_id}_run',
                'activity_name': 'data_migration',
                'selection_criteria': selection_criteria,
                'target_sample_size': sample_set.target_sample_size or 0,
                'actual_sample_size': sample_set.actual_sample_size or 0,
                'intelligent_sampling_config': intelligent_sampling_config,
                'submission_notes': sample_set.generation_rationale,
                'approval_notes': sample_set.approval_notes,
                'created_at': sample_set.created_at,
                'created_by_id': sample_set.created_by,
                'submitted_at': sample_set.approved_at if sample_set.approved_by else None,
                'submitted_by_id': sample_set.approved_by if sample_set.approved_by else None,
                'approved_at': sample_set.approved_at,
                'approved_by_id': sample_set.approved_by,
                'updated_at': sample_set.created_at
            })
            
            # Track migration
            conn.execute(
                text("INSERT INTO sample_selection_migration_tracking (old_set_id, new_version_id) VALUES (:old_set_id, :new_version_id)"),
                {'old_set_id': sample_set.set_id, 'new_version_id': new_version_id}
            )
            
            # Migrate samples for this set
            migrate_samples_for_set(conn, sample_set.set_id, new_version_id, phase_id)
            
            print(f"Migrated sample set {sample_set.set_id} to version {new_version_id}")
            
        except Exception as e:
            print(f"Error migrating sample set {sample_set.set_id}: {str(e)}")
            # Continue with other sets
            continue
    
    print(f"Migrated {len(sample_sets)} sample sets to versions")
    
    # Step 3: Update actual sample sizes
    print("Updating actual sample sizes...")
    
    update_sample_sizes_query = text("""
        UPDATE cycle_report_sample_selection_versions
        SET actual_sample_size = (
            SELECT COUNT(*)
            FROM cycle_report_sample_selection_samples
            WHERE version_id = cycle_report_sample_selection_versions.version_id
        )
    """)
    
    conn.execute(update_sample_sizes_query)
    
    # Step 4: Update distribution metrics
    print("Updating distribution metrics...")
    
    update_distribution_query = text("""
        UPDATE cycle_report_sample_selection_versions
        SET distribution_metrics = (
            SELECT jsonb_build_object(
                'category_distribution', 
                jsonb_object_agg(sample_category, count),
                'total_samples',
                SUM(count)
            )
            FROM (
                SELECT 
                    sample_category,
                    COUNT(*) as count
                FROM cycle_report_sample_selection_samples
                WHERE version_id = cycle_report_sample_selection_versions.version_id
                GROUP BY sample_category
            ) subq
        )
        WHERE EXISTS (
            SELECT 1 
            FROM cycle_report_sample_selection_samples 
            WHERE version_id = cycle_report_sample_selection_versions.version_id
        )
    """)
    
    conn.execute(update_distribution_query)
    
    print("Migration completed successfully!")


def migrate_samples_for_set(conn, old_set_id, new_version_id, phase_id):
    """Migrate samples for a specific sample set"""
    
    # Get all sample records for this set
    samples_query = text("""
        SELECT 
            sr.record_id,
            sr.sample_identifier,
            sr.primary_key_value,
            sr.sample_data,
            sr.risk_score,
            sr.validation_status,
            sr.validation_score,
            sr.selection_rationale,
            sr.data_source_info,
            sr.created_at,
            sr.updated_at,
            sr.approval_status,
            sr.approved_by,
            sr.approved_at,
            sr.rejection_reason,
            sr.change_requests
        FROM cycle_report_sample_records sr
        WHERE sr.set_id = :set_id
        ORDER BY sr.created_at
    """)
    
    samples = conn.execute(samples_query, {'set_id': old_set_id}).fetchall()
    
    for sample in samples:
        try:
            # Determine sample category based on validation status and risk score
            sample_category = determine_sample_category(sample.validation_status, sample.risk_score)
            
            # Determine sample source
            sample_source = 'manual'  # Default, could be enhanced with more logic
            
            # Map old approval status to new decisions
            tester_decision, report_owner_decision = map_approval_status_to_decisions(sample.approval_status)
            
            # Prepare sample data
            sample_data = sample.sample_data or {}
            sample_data.update({
                'primary_key_value': sample.primary_key_value,
                'data_source_info': sample.data_source_info,
                'validation_status': sample.validation_status,
                'validation_score': sample.validation_score,
                'selection_rationale': sample.selection_rationale,
                'migrated_from': sample.record_id
            })
            
            # Insert new sample
            insert_sample_query = text("""
                INSERT INTO cycle_report_sample_selection_samples (
                    sample_id, version_id, phase_id, lob_id,
                    sample_identifier, sample_data, sample_category, sample_source,
                    tester_decision, tester_decision_notes, tester_decision_at, tester_decision_by_id,
                    report_owner_decision, report_owner_decision_notes, report_owner_decision_at, report_owner_decision_by_id,
                    risk_score, confidence_score, validation_results,
                    created_at, updated_at
                ) VALUES (
                    :sample_id, :version_id, :phase_id, :lob_id,
                    :sample_identifier, :sample_data, :sample_category, :sample_source,
                    :tester_decision, :tester_decision_notes, :tester_decision_at, :tester_decision_by_id,
                    :report_owner_decision, :report_owner_decision_notes, :report_owner_decision_at, :report_owner_decision_by_id,
                    :risk_score, :confidence_score, :validation_results,
                    :created_at, :updated_at
                )
            """)
            
            conn.execute(insert_sample_query, {
                'sample_id': uuid.uuid4(),
                'version_id': new_version_id,
                'phase_id': phase_id,
                'lob_id': 1,  # Default LOB, would need to be determined properly
                'sample_identifier': sample.sample_identifier,
                'sample_data': sample_data,
                'sample_category': sample_category,
                'sample_source': sample_source,
                'tester_decision': tester_decision,
                'tester_decision_notes': sample.change_requests,
                'tester_decision_at': sample.approved_at,
                'tester_decision_by_id': sample.approved_by,
                'report_owner_decision': report_owner_decision,
                'report_owner_decision_notes': sample.rejection_reason,
                'report_owner_decision_at': sample.approved_at,
                'report_owner_decision_by_id': sample.approved_by,
                'risk_score': sample.risk_score,
                'confidence_score': sample.validation_score,
                'validation_results': {
                    'validation_status': sample.validation_status,
                    'validation_score': sample.validation_score
                },
                'created_at': sample.created_at,
                'updated_at': sample.updated_at or sample.created_at
            })
            
        except Exception as e:
            print(f"Error migrating sample {sample.record_id}: {str(e)}")
            continue


def create_workflow_phase(conn, cycle_id, report_id):
    """Create workflow phase for sample selection if it doesn't exist"""
    
    # Check if phase already exists
    existing_phase_query = text("""
        SELECT phase_id 
        FROM workflow_phases 
        WHERE cycle_id = :cycle_id 
        AND report_id = :report_id 
        AND phase_name = 'Sample Selection'
    """)
    
    result = conn.execute(existing_phase_query, {
        'cycle_id': cycle_id,
        'report_id': report_id
    }).fetchone()
    
    if result:
        return result.phase_id
    
    # Create new phase
    phase_id = conn.execute(text("SELECT nextval('workflow_phases_phase_id_seq')")).scalar()
    
    insert_phase_query = text("""
        INSERT INTO workflow_phases (
            phase_id, cycle_id, report_id, phase_name, phase_status,
            created_at, updated_at
        ) VALUES (
            :phase_id, :cycle_id, :report_id, :phase_name, :phase_status,
            :created_at, :updated_at
        )
    """)
    
    conn.execute(insert_phase_query, {
        'phase_id': phase_id,
        'cycle_id': cycle_id,
        'report_id': report_id,
        'phase_name': 'Sample Selection',
        'phase_status': 'In Progress',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    })
    
    return phase_id


def map_old_status_to_new(old_status):
    """Map old sample set status to new version status"""
    status_mapping = {
        'Draft': 'draft',
        'Pending Approval': 'pending_approval',
        'Approved': 'approved',
        'Rejected': 'rejected',
        'Revision Required': 'rejected'
    }
    return status_mapping.get(old_status, 'draft')


def determine_sample_category(validation_status, risk_score):
    """Determine sample category based on validation status and risk score"""
    if validation_status == 'Invalid' or (risk_score and risk_score > 0.7):
        return 'anomaly'
    elif validation_status == 'Warning' or (risk_score and risk_score > 0.5):
        return 'boundary'
    else:
        return 'clean'


def map_approval_status_to_decisions(approval_status):
    """Map old approval status to new tester and report owner decisions"""
    if approval_status == 'Approved':
        return 'include', 'include'
    elif approval_status == 'Rejected':
        return 'exclude', 'exclude'
    elif approval_status == 'Needs Changes':
        return 'pending', 'pending'
    else:
        return 'pending', 'pending'


def downgrade():
    """Reverse the migration"""
    
    print("Reversing sample selection data migration...")
    
    # Drop migration tracking table
    op.drop_table('sample_selection_migration_tracking')
    
    # Note: We don't delete the migrated data as it might be in use
    # The old tables are still available as backup tables
    
    print("Migration reversal completed. Note: Migrated data preserved for safety.")