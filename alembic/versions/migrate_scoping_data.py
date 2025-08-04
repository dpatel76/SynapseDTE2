"""Migrate existing scoping data to new consolidated system

Revision ID: migrate_scoping_data_001
Revises: scoping_consolidation_001
Create Date: 2024-07-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'migrate_scoping_data_001'
down_revision = 'scoping_consolidation_001'
branch_labels = None
depends_on = None


def upgrade():
    """Migrate existing scoping data to new consolidated system"""
    
    # Create connection
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        # Create migration tracking table
        op.create_table(
            'scoping_migration_tracking',
            sa.Column('migration_id', sa.Integer, primary_key=True),
            sa.Column('phase_id', sa.Integer, nullable=False),
            sa.Column('legacy_data_count', sa.Integer, nullable=False),
            sa.Column('migrated_data_count', sa.Integer, nullable=False),
            sa.Column('migration_status', sa.String(50), nullable=False),
            sa.Column('migration_errors', postgresql.JSONB, nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
        
        # Step 1: Migrate legacy scoping data
        print("Starting migration of legacy scoping data...")
        
        # Get all workflow phases that have scoping data
        phases_with_scoping = session.execute(text("""
            SELECT DISTINCT wp.phase_id, wp.cycle_id, wp.report_id
            FROM workflow_phases wp
            WHERE wp.phase_name = 'Scoping'
            AND EXISTS (
                SELECT 1 FROM cycle_report_scoping_attribute_recommendations asr
                WHERE asr.cycle_id = wp.cycle_id AND asr.report_id = wp.report_id
            )
        """)).fetchall()
        
        migration_count = 0
        
        for phase_id, cycle_id, report_id in phases_with_scoping:
            try:
                # Create a new scoping version for this phase
                version_result = session.execute(text("""
                    INSERT INTO cycle_report_scoping_versions (
                        version_id, phase_id, version_number, version_status,
                        total_attributes, scoped_attributes, declined_attributes,
                        override_count, cde_count, recommendation_accuracy,
                        created_at, created_by_id, updated_at, updated_by_id
                    ) VALUES (
                        gen_random_uuid(), :phase_id, 1, 'approved',
                        0, 0, 0, 0, 0, 0.0,
                        CURRENT_TIMESTAMP, 1, CURRENT_TIMESTAMP, 1
                    ) RETURNING version_id
                """), {"phase_id": phase_id})
                
                version_id = version_result.fetchone()[0]
                
                # Migrate attribute recommendations and decisions
                attribute_data = session.execute(text("""
                    SELECT 
                        asr.id as recommendation_id,
                        asr.attribute_id as planning_attribute_id,
                        asr.llm_recommendation,
                        asr.llm_confidence_score,
                        asr.llm_reasoning,
                        asr.llm_provider,
                        asr.created_at as recommendation_created_at,
                        asr.created_by_id as recommendation_created_by,
                        
                        -- Tester decision data
                        tsd.id as tester_decision_id,
                        tsd.scoping_decision as tester_decision,
                        tsd.decision_rationale as tester_rationale,
                        tsd.is_override,
                        tsd.override_justification,
                        tsd.created_at as tester_decided_at,
                        tsd.created_by_id as tester_decided_by,
                        
                        -- Report owner review data
                        ror.id as report_owner_review_id,
                        ror.approval_status as report_owner_decision,
                        ror.review_notes as report_owner_notes,
                        ror.created_at as report_owner_decided_at,
                        ror.created_by_id as report_owner_decided_by,
                        
                        -- Planning attribute data for metadata
                        cra.attribute_name,
                        cra.data_type,
                        cra.mandatory_flag,
                        cra.is_primary_key,
                        cra.expected_source_documents,
                        cra.search_keywords
                        
                    FROM cycle_report_scoping_attribute_recommendations asr
                    JOIN cycle_report_planning_attributes cra ON asr.attribute_id = cra.id
                    LEFT JOIN cycle_report_tester_scoping_decisions tsd ON asr.id = tsd.recommendation_id
                    LEFT JOIN cycle_report_report_owner_scoping_reviews ror ON tsd.id = ror.tester_decision_id
                    WHERE asr.cycle_id = :cycle_id AND asr.report_id = :report_id
                """), {"cycle_id": cycle_id, "report_id": report_id})
                
                attributes_migrated = 0
                total_attributes = 0
                scoped_attributes = 0
                declined_attributes = 0
                override_count = 0
                cde_count = 0
                accurate_predictions = 0
                
                for attr_row in attribute_data:
                    total_attributes += 1
                    
                    # Build LLM recommendation JSON
                    llm_recommendation = {
                        "recommended_action": "test" if attr_row.llm_recommendation else "skip",
                        "confidence_score": float(attr_row.llm_confidence_score) if attr_row.llm_confidence_score else None,
                        "rationale": attr_row.llm_reasoning,
                        "provider": attr_row.llm_provider or "unknown",
                        "legacy_migration": True
                    }
                    
                    # Determine final scoping decision
                    final_scoping = None
                    tester_decision = None
                    if attr_row.tester_decision is not None:
                        if attr_row.tester_decision == 'include':
                            final_scoping = True
                            tester_decision = 'accept'
                            scoped_attributes += 1
                        elif attr_row.tester_decision == 'exclude':
                            final_scoping = False
                            tester_decision = 'decline'
                            declined_attributes += 1
                        elif attr_row.tester_decision == 'override':
                            # Need to check the actual scoping outcome
                            final_scoping = True  # Assume override means include
                            tester_decision = 'override'
                            scoped_attributes += 1
                            override_count += 1
                    
                    # Map report owner decision
                    report_owner_decision = None
                    if attr_row.report_owner_decision:
                        if attr_row.report_owner_decision == 'approved':
                            report_owner_decision = 'approved'
                        elif attr_row.report_owner_decision == 'rejected':
                            report_owner_decision = 'rejected'
                        elif attr_row.report_owner_decision == 'pending':
                            report_owner_decision = 'pending'
                        else:
                            report_owner_decision = 'needs_revision'
                    
                    # Determine if CDE
                    is_cde = attr_row.mandatory_flag == 'Mandatory'
                    if is_cde:
                        cde_count += 1
                    
                    # Check LLM accuracy
                    if tester_decision and llm_recommendation.get('recommended_action'):
                        llm_action = llm_recommendation['recommended_action']
                        if (llm_action == 'test' and final_scoping is True) or (llm_action == 'skip' and final_scoping is False):
                            accurate_predictions += 1
                    
                    # Determine attribute status
                    attribute_status = 'pending'
                    if tester_decision:
                        if report_owner_decision == 'approved':
                            attribute_status = 'approved'
                        elif report_owner_decision == 'rejected':
                            attribute_status = 'rejected'
                        elif report_owner_decision == 'needs_revision':
                            attribute_status = 'needs_revision'
                        else:
                            attribute_status = 'submitted'
                    
                    # Build metadata
                    expected_source_documents = attr_row.expected_source_documents
                    search_keywords = attr_row.search_keywords
                    
                    # Insert scoping attribute
                    session.execute(text("""
                        INSERT INTO cycle_report_scoping_attributes (
                            attribute_id, version_id, phase_id, planning_attribute_id,
                            llm_recommendation, llm_provider, llm_confidence_score, llm_rationale,
                            tester_decision, final_scoping, tester_rationale,
                            tester_decided_by_id, tester_decided_at,
                            report_owner_decision, report_owner_notes,
                            report_owner_decided_by_id, report_owner_decided_at,
                            is_override, override_reason, is_cde, is_primary_key,
                            expected_source_documents, search_keywords, status,
                            created_at, created_by_id, updated_at, updated_by_id
                        ) VALUES (
                            gen_random_uuid(), :version_id, :phase_id, :planning_attribute_id,
                            :llm_recommendation, :llm_provider, :llm_confidence_score, :llm_rationale,
                            :tester_decision, :final_scoping, :tester_rationale,
                            :tester_decided_by_id, :tester_decided_at,
                            :report_owner_decision, :report_owner_notes,
                            :report_owner_decided_by_id, :report_owner_decided_at,
                            :is_override, :override_reason, :is_cde, :is_primary_key,
                            :expected_source_documents, :search_keywords, :status,
                            :created_at, :created_by_id, :updated_at, :updated_by_id
                        )
                    """), {
                        "version_id": version_id,
                        "phase_id": phase_id,
                        "planning_attribute_id": attr_row.planning_attribute_id,
                        "llm_recommendation": llm_recommendation,
                        "llm_provider": attr_row.llm_provider or "unknown",
                        "llm_confidence_score": attr_row.llm_confidence_score,
                        "llm_rationale": attr_row.llm_reasoning,
                        "tester_decision": tester_decision,
                        "final_scoping": final_scoping,
                        "tester_rationale": attr_row.tester_rationale,
                        "tester_decided_by_id": attr_row.tester_decided_by,
                        "tester_decided_at": attr_row.tester_decided_at,
                        "report_owner_decision": report_owner_decision,
                        "report_owner_notes": attr_row.report_owner_notes,
                        "report_owner_decided_by_id": attr_row.report_owner_decided_by,
                        "report_owner_decided_at": attr_row.report_owner_decided_at,
                        "is_override": attr_row.is_override or False,
                        "override_reason": attr_row.override_justification,
                        "is_cde": is_cde,
                        "is_primary_key": attr_row.is_primary_key or False,
                        "expected_source_documents": expected_source_documents,
                        "search_keywords": search_keywords,
                        "status": attribute_status,
                        "created_at": attr_row.recommendation_created_at,
                        "created_by_id": attr_row.recommendation_created_by,
                        "updated_at": attr_row.tester_decided_at or attr_row.recommendation_created_at,
                        "updated_by_id": attr_row.tester_decided_by or attr_row.recommendation_created_by
                    })
                    
                    attributes_migrated += 1
                
                # Update version summary statistics
                recommendation_accuracy = (accurate_predictions / total_attributes) if total_attributes > 0 else 0.0
                
                session.execute(text("""
                    UPDATE cycle_report_scoping_versions
                    SET 
                        total_attributes = :total_attributes,
                        scoped_attributes = :scoped_attributes,
                        declined_attributes = :declined_attributes,
                        override_count = :override_count,
                        cde_count = :cde_count,
                        recommendation_accuracy = :recommendation_accuracy,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE version_id = :version_id
                """), {
                    "version_id": version_id,
                    "total_attributes": total_attributes,
                    "scoped_attributes": scoped_attributes,
                    "declined_attributes": declined_attributes,
                    "override_count": override_count,
                    "cde_count": cde_count,
                    "recommendation_accuracy": recommendation_accuracy
                })
                
                # Record migration success
                session.execute(text("""
                    INSERT INTO scoping_migration_tracking (
                        phase_id, legacy_data_count, migrated_data_count, migration_status
                    ) VALUES (
                        :phase_id, :legacy_count, :migrated_count, 'success'
                    )
                """), {
                    "phase_id": phase_id,
                    "legacy_count": total_attributes,
                    "migrated_count": attributes_migrated
                })
                
                migration_count += 1
                print(f"Migrated phase {phase_id}: {attributes_migrated} attributes")
                
            except Exception as e:
                print(f"Error migrating phase {phase_id}: {str(e)}")
                session.execute(text("""
                    INSERT INTO scoping_migration_tracking (
                        phase_id, legacy_data_count, migrated_data_count, migration_status, migration_errors
                    ) VALUES (
                        :phase_id, 0, 0, 'error', :error
                    )
                """), {
                    "phase_id": phase_id,
                    "error": {"error": str(e)}
                })
                continue
        
        session.commit()
        print(f"Migration completed: {migration_count} phases migrated")
        
    except Exception as e:
        session.rollback()
        print(f"Migration failed: {str(e)}")
        raise
    finally:
        session.close()


def downgrade():
    """Rollback the scoping data migration"""
    
    # Create connection
    bind = op.get_bind()
    session = Session(bind=bind)
    
    try:
        print("Rolling back scoping data migration...")
        
        # Get migration tracking data
        migration_data = session.execute(text("""
            SELECT phase_id, legacy_data_count, migrated_data_count, migration_status
            FROM scoping_migration_tracking
            ORDER BY phase_id
        """)).fetchall()
        
        # Clear migrated data
        session.execute(text("DELETE FROM cycle_report_scoping_attributes"))
        session.execute(text("DELETE FROM cycle_report_scoping_versions"))
        
        # Drop migration tracking table
        op.drop_table('scoping_migration_tracking')
        
        session.commit()
        print("Rollback completed successfully")
        
    except Exception as e:
        session.rollback()
        print(f"Rollback failed: {str(e)}")
        raise
    finally:
        session.close()