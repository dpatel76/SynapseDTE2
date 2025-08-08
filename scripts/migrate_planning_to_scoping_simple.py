#!/usr/bin/env python
"""
Simple synchronous migration script to move data from planning to scoping
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
import json

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


def migrate_fields_to_scoping():
    """Migrate fields from planning to scoping"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        logger.info("Starting data migration from planning to scoping...")
        
        # Query planning attributes with data to migrate
        cur.execute("""
            SELECT DISTINCT
                p.id as planning_id,
                p.phase_id,
                p.attribute_name,
                p.validation_rules,
                p.testing_approach,
                p.typical_source_documents,
                p.keywords_to_look_for,
                p.llm_rationale,
                p.risk_score
            FROM cycle_report_planning_attributes p
            WHERE p.validation_rules IS NOT NULL
               OR p.testing_approach IS NOT NULL
               OR p.typical_source_documents IS NOT NULL
               OR p.keywords_to_look_for IS NOT NULL
               OR p.llm_rationale IS NOT NULL
               OR p.risk_score IS NOT NULL
        """)
        
        planning_attrs = cur.fetchall()
        logger.info(f"Found {len(planning_attrs)} planning attributes with data to migrate")
        
        migrated_count = 0
        for p_attr in planning_attrs:
            # Find corresponding scoping attributes
            cur.execute("""
                SELECT version_id, attribute_id
                FROM cycle_report_scoping_attributes
                WHERE attribute_id = %s
            """, (p_attr['planning_id'],))
            
            scoping_attrs = cur.fetchall()
            
            if scoping_attrs:
                logger.info(f"Migrating data for attribute '{p_attr['attribute_name']}' to {len(scoping_attrs)} scoping records")
                
                for s_attr in scoping_attrs:
                    # Update scoping attribute
                    cur.execute("""
                        UPDATE cycle_report_scoping_attributes
                        SET validation_rules = COALESCE(%s, validation_rules),
                            testing_approach = COALESCE(%s, testing_approach),
                            expected_source_documents = COALESCE(%s, expected_source_documents),
                            search_keywords = COALESCE(%s, search_keywords),
                            updated_at = %s
                        WHERE version_id = %s AND attribute_id = %s
                    """, (
                        p_attr['validation_rules'],
                        p_attr['testing_approach'],
                        p_attr['typical_source_documents'],
                        p_attr['keywords_to_look_for'],
                        datetime.utcnow(),
                        s_attr['version_id'],
                        s_attr['attribute_id']
                    ))
                    
                    if cur.rowcount > 0:
                        migrated_count += 1
        
        logger.info(f"Migrated fields for {migrated_count} scoping attributes")
        
        # Populate missing llm_request_payload
        logger.info("Populating missing llm_request_payload fields...")
        
        default_payload = json.dumps({
            "model": "claude-3-5-sonnet",
            "temperature": 0.3,
            "max_tokens": 2000,
            "migrated": True,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        cur.execute("""
            UPDATE cycle_report_scoping_attributes
            SET llm_request_payload = %s::jsonb
            WHERE llm_request_payload IS NULL 
               OR llm_request_payload::text = 'null'
               OR llm_request_payload::text = '{}'
        """, (default_payload,))
        
        populated_count = cur.rowcount
        logger.info(f"Populated llm_request_payload for {populated_count} records")
        
        # Commit all changes
        conn.commit()
        
        logger.info("✅ Migration completed successfully!")
        logger.info(f"   - Migrated fields for {migrated_count} scoping attributes")
        logger.info(f"   - Populated llm_request_payload for {populated_count} records")
        
        # Verify migration
        cur.execute("""
            SELECT COUNT(*) as null_count
            FROM cycle_report_scoping_attributes
            WHERE llm_request_payload IS NULL
        """)
        
        result = cur.fetchone()
        null_count = result['null_count']
        
        if null_count > 0:
            logger.warning(f"⚠️ Still have {null_count} records with NULL llm_request_payload")
        else:
            logger.info("✅ All scoping attributes have llm_request_payload populated")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def verify_migration():
    """Verify that the migration was successful"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check for any planning attributes still having the fields
        cur.execute("""
            SELECT COUNT(*) as count
            FROM cycle_report_planning_attributes
            WHERE validation_rules IS NOT NULL
               OR testing_approach IS NOT NULL
               OR typical_source_documents IS NOT NULL
               OR keywords_to_look_for IS NOT NULL
               OR llm_rationale IS NOT NULL
               OR risk_score IS NOT NULL
        """)
        
        result = cur.fetchone()
        count = result['count']
        
        if count > 0:
            logger.info(f"Note: {count} planning attributes still have data in fields to be dropped")
            logger.info("This is expected before running the schema migration to drop these columns")
        
        # Check scoping attributes have the data
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(validation_rules) as has_validation_rules,
                COUNT(testing_approach) as has_testing_approach,
                COUNT(expected_source_documents) as has_expected_docs,
                COUNT(search_keywords) as has_search_keywords,
                COUNT(llm_request_payload) as has_request_payload
            FROM cycle_report_scoping_attributes
        """)
        
        stats = cur.fetchone()
        
        logger.info("Scoping attributes statistics:")
        logger.info(f"  Total: {stats['total']}")
        logger.info(f"  With validation_rules: {stats['has_validation_rules']}")
        logger.info(f"  With testing_approach: {stats['has_testing_approach']}")
        logger.info(f"  With expected_source_documents: {stats['has_expected_docs']}")
        logger.info(f"  With search_keywords: {stats['has_search_keywords']}")
        logger.info(f"  With llm_request_payload: {stats['has_request_payload']}")
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    logger.info("Starting planning to scoping data migration...")
    
    # Run migration
    migrate_fields_to_scoping()
    
    # Verify results
    logger.info("\n=== Verifying migration results ===")
    verify_migration()
    
    logger.info("\n✅ Migration script completed")
    logger.info("Note: After verifying the data migration, run the Alembic migrations to update the schema")