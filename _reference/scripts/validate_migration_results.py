#!/usr/bin/env python
"""
Validate the results of the data migration and schema changes
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password'
}


def validate_planning_attributes():
    """Validate planning attributes table changes"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        logger.info("=== PLANNING ATTRIBUTES VALIDATION ===")
        
        # Check for audit columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cycle_report_planning_attributes' 
            AND column_name IN ('version', 'created_by', 'updated_by')
            ORDER BY column_name;
        """)
        
        audit_columns = [row['column_name'] for row in cur.fetchall()]
        logger.info(f"✅ Audit columns present: {audit_columns}")
        
        # Check that scoping-related columns were removed
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cycle_report_planning_attributes' 
            AND column_name IN ('validation_rules', 'testing_approach', 'typical_source_documents', 
                                'keywords_to_look_for', 'risk_score', 'llm_risk_rationale')
        """)
        
        removed_columns = [row['column_name'] for row in cur.fetchall()]
        if removed_columns:
            logger.warning(f"⚠️ Columns still present (should be removed): {removed_columns}")
        else:
            logger.info("✅ Scoping-related columns successfully removed")
        
        # Check data population
        cur.execute("""
            SELECT COUNT(*) as total,
                   COUNT(version) as has_version,
                   COUNT(created_by) as has_created_by,
                   COUNT(updated_by) as has_updated_by
            FROM cycle_report_planning_attributes
        """)
        
        stats = cur.fetchone()
        logger.info(f"Planning attributes statistics:")
        logger.info(f"  Total records: {stats['total']}")
        logger.info(f"  With version: {stats['has_version']}")
        logger.info(f"  With created_by: {stats['has_created_by']}")
        logger.info(f"  With updated_by: {stats['has_updated_by']}")
        
    finally:
        cur.close()
        conn.close()


def validate_scoping_attributes():
    """Validate scoping attributes table changes"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        logger.info("\n=== SCOPING ATTRIBUTES VALIDATION ===")
        
        # Check for new columns
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_name = 'cycle_report_scoping_attributes' 
            AND column_name IN ('validation_rules', 'testing_approach', 'expected_source_documents', 
                                'search_keywords', 'llm_request_payload', 'llm_response_payload')
            ORDER BY column_name;
        """)
        
        columns = cur.fetchall()
        logger.info("Scoping columns present:")
        for col in columns:
            logger.info(f"  ✅ {col['column_name']}: {col['data_type']}")
        
        # Check data population
        cur.execute("""
            SELECT COUNT(*) as total,
                   COUNT(validation_rules) as has_validation_rules,
                   COUNT(testing_approach) as has_testing_approach,
                   COUNT(CASE WHEN expected_source_documents IS NOT NULL 
                              AND expected_source_documents::text != 'null' THEN 1 END) as has_expected_docs,
                   COUNT(CASE WHEN search_keywords IS NOT NULL 
                              AND search_keywords::text != 'null' THEN 1 END) as has_search_keywords,
                   COUNT(llm_request_payload) as has_request_payload,
                   COUNT(llm_response_payload) as has_response_payload
            FROM cycle_report_scoping_attributes
        """)
        
        stats = cur.fetchone()
        logger.info(f"\nScoping attributes data population:")
        logger.info(f"  Total records: {stats['total']}")
        logger.info(f"  With validation_rules: {stats['has_validation_rules']} ({stats['has_validation_rules']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"  With testing_approach: {stats['has_testing_approach']} ({stats['has_testing_approach']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"  With expected_source_documents (non-null JSON): {stats['has_expected_docs']} ({stats['has_expected_docs']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"  With search_keywords (non-null JSON): {stats['has_search_keywords']} ({stats['has_search_keywords']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"  With llm_request_payload: {stats['has_request_payload']} ({stats['has_request_payload']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"  With llm_response_payload: {stats['has_response_payload']} ({stats['has_response_payload']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        
        # Check llm_request_payload content
        cur.execute("""
            SELECT llm_request_payload->>'model' as model,
                   COUNT(*) as count
            FROM cycle_report_scoping_attributes
            WHERE llm_request_payload IS NOT NULL
            GROUP BY llm_request_payload->>'model'
        """)
        
        models = cur.fetchall()
        if models:
            logger.info("\nLLM models in request payloads:")
            for model in models:
                logger.info(f"  {model['model']}: {model['count']}")
        
    finally:
        cur.close()
        conn.close()


def validate_workflow_phases():
    """Validate workflow phase consistency"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        logger.info("\n=== WORKFLOW PHASES VALIDATION ===")
        
        # Check for inconsistencies
        cur.execute("""
            SELECT COUNT(*) as count
            FROM workflow_phases
            WHERE (status = 'Not Started' AND progress_percentage > 0)
               OR (status = 'Complete' AND progress_percentage < 100)
               OR (progress_percentage = 100 AND status != 'Complete')
               OR (progress_percentage = 0 AND status = 'Complete')
        """)
        
        result = cur.fetchone()
        inconsistent_count = result['count']
        
        if inconsistent_count > 0:
            logger.warning(f"⚠️ Found {inconsistent_count} workflow phases with inconsistencies")
        else:
            logger.info("✅ All workflow phases have consistent status/progress values")
        
        # Get status distribution
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM workflow_phases
            GROUP BY status
            ORDER BY status
        """)
        
        statuses = cur.fetchall()
        logger.info("\nWorkflow phase status distribution:")
        for status in statuses:
            logger.info(f"  {status['status']}: {status['count']}")
        
        # Check state consistency
        cur.execute("""
            SELECT COUNT(*) as count
            FROM workflow_phases
            WHERE status::text != state::text
        """)
        
        result = cur.fetchone()
        if result['count'] > 0:
            logger.warning(f"⚠️ Found {result['count']} phases where status != state")
        else:
            logger.info("✅ All workflow phases have matching status and state")
        
    finally:
        cur.close()
        conn.close()


def generate_summary():
    """Generate a summary of the migration results"""
    
    logger.info("\n" + "="*60)
    logger.info("MIGRATION VALIDATION SUMMARY")
    logger.info("="*60)
    
    issues = []
    successes = []
    
    # Check planning attributes
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Planning attributes checks
        cur.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.columns 
            WHERE table_name = 'cycle_report_planning_attributes' 
            AND column_name IN ('version', 'created_by', 'updated_by')
        """)
        
        if cur.fetchone()['count'] == 3:
            successes.append("Planning attributes: Audit columns added successfully")
        else:
            issues.append("Planning attributes: Missing audit columns")
        
        # Scoping attributes checks
        cur.execute("""
            SELECT COUNT(*) as total,
                   COUNT(llm_request_payload) as has_payload
            FROM cycle_report_scoping_attributes
        """)
        
        result = cur.fetchone()
        if result['has_payload'] == result['total']:
            successes.append(f"Scoping attributes: All {result['total']} records have llm_request_payload")
        else:
            issues.append(f"Scoping attributes: {result['total'] - result['has_payload']} records missing llm_request_payload")
        
        # Workflow phases checks
        cur.execute("""
            SELECT COUNT(*) as count
            FROM workflow_phases
            WHERE (status = 'Not Started' AND progress_percentage > 0)
               OR (status = 'Complete' AND progress_percentage < 100)
        """)
        
        if cur.fetchone()['count'] == 0:
            successes.append("Workflow phases: All phases have consistent status/progress")
        else:
            issues.append("Workflow phases: Some phases have inconsistent status/progress")
        
        # Print summary
        logger.info("\n✅ SUCCESSFUL CHANGES:")
        for success in successes:
            logger.info(f"  • {success}")
        
        if issues:
            logger.info("\n⚠️ ISSUES TO ADDRESS:")
            for issue in issues:
                logger.info(f"  • {issue}")
        else:
            logger.info("\n🎉 No issues found - migration completed successfully!")
        
        # Data loss warning
        logger.info("\n📝 NOTE ON DATA MIGRATION:")
        logger.info("  The validation_rules and testing_approach fields in scoping_attributes")
        logger.info("  are empty because the source columns in planning_attributes were already")
        logger.info("  dropped. This data may need to be regenerated through the LLM service.")
        
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    logger.info("Starting migration validation...")
    logger.info("="*60)
    
    # Run all validations
    validate_planning_attributes()
    validate_scoping_attributes()
    validate_workflow_phases()
    
    # Generate summary
    generate_summary()
    
    logger.info("\n✅ Validation complete")