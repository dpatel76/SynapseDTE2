#!/usr/bin/env python
"""
Extract validation_rules and testing_approach from llm_response_payload
and populate the corresponding text columns in scoping attributes
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
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


def extract_llm_payload_data():
    """Extract data from llm_response_payload and populate text columns"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        logger.info("Starting extraction of llm_response_payload data...")
        
        # Get all records with llm_response_payload
        cur.execute("""
            SELECT version_id, attribute_id, llm_response_payload
            FROM cycle_report_scoping_attributes
            WHERE llm_response_payload IS NOT NULL
        """)
        
        records = cur.fetchall()
        logger.info(f"Found {len(records)} records with llm_response_payload")
        
        updated_count = 0
        for record in records:
            try:
                payload = record['llm_response_payload']
                
                # Extract fields from payload
                validation_rules = payload.get('validation_rules')
                testing_approach = payload.get('testing_approach')
                typical_source_docs = payload.get('typical_source_documents')
                keywords = payload.get('keywords_to_look_for')
                
                # Update the record
                cur.execute("""
                    UPDATE cycle_report_scoping_attributes
                    SET validation_rules = %s,
                        testing_approach = %s,
                        expected_source_documents = CASE 
                            WHEN expected_source_documents IS NULL OR expected_source_documents::text = 'null' 
                            THEN %s::jsonb 
                            ELSE expected_source_documents 
                        END,
                        search_keywords = CASE 
                            WHEN search_keywords IS NULL OR search_keywords::text = 'null' 
                            THEN %s::jsonb 
                            ELSE search_keywords 
                        END
                    WHERE version_id = %s AND attribute_id = %s
                """, (
                    validation_rules,
                    testing_approach,
                    json.dumps(typical_source_docs) if typical_source_docs else None,
                    json.dumps(keywords) if keywords else None,
                    record['version_id'],
                    record['attribute_id']
                ))
                
                if cur.rowcount > 0:
                    updated_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing record {record['attribute_id']}: {str(e)}")
                continue
        
        # Commit all changes
        conn.commit()
        
        logger.info(f"✅ Successfully updated {updated_count} records")
        
        # Verify the update
        cur.execute("""
            SELECT COUNT(*) as total,
                   COUNT(validation_rules) as has_validation,
                   COUNT(testing_approach) as has_testing,
                   COUNT(CASE WHEN expected_source_documents IS NOT NULL 
                              AND expected_source_documents::text != 'null' THEN 1 END) as has_docs,
                   COUNT(CASE WHEN search_keywords IS NOT NULL 
                              AND search_keywords::text != 'null' THEN 1 END) as has_keywords
            FROM cycle_report_scoping_attributes
        """)
        
        stats = cur.fetchone()
        logger.info("\nFinal statistics:")
        logger.info(f"  Total records: {stats['total']}")
        logger.info(f"  With validation_rules: {stats['has_validation']} ({stats['has_validation']*100//stats['total']}%)")
        logger.info(f"  With testing_approach: {stats['has_testing']} ({stats['has_testing']*100//stats['total']}%)")
        logger.info(f"  With expected_source_documents: {stats['has_docs']} ({stats['has_docs']*100//stats['total']}%)")
        logger.info(f"  With search_keywords: {stats['has_keywords']} ({stats['has_keywords']*100//stats['total']}%)")
        
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def show_sample_data():
    """Show sample data to verify extraction"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        logger.info("\n=== SAMPLE DATA ===")
        
        cur.execute("""
            SELECT attribute_id,
                   LEFT(validation_rules, 80) as validation_sample,
                   LEFT(testing_approach, 80) as testing_sample
            FROM cycle_report_scoping_attributes
            WHERE validation_rules IS NOT NULL
            LIMIT 3
        """)
        
        samples = cur.fetchall()
        for sample in samples:
            logger.info(f"\nAttribute {sample['attribute_id']}:")
            logger.info(f"  Validation: {sample['validation_sample']}...")
            logger.info(f"  Testing: {sample['testing_sample']}...")
        
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    logger.info("Extracting data from llm_response_payload to text columns...")
    logger.info("="*60)
    
    # Extract and populate data
    extract_llm_payload_data()
    
    # Show sample data
    show_sample_data()
    
    logger.info("\n✅ Extraction complete")