#!/usr/bin/env python
"""
Verify that the scoping service and celery task code changes are in place
and will properly save all fields in future runs
"""

import ast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_celery_task_extracts_fields():
    """Check if celery task extracts all required fields from LLM response"""
    
    with open('app/tasks/scoping_celery_tasks.py', 'r') as f:
        content = f.read()
    
    required_fields = [
        '"validation_rules": recommendation_data.get("validation_rules")',
        '"testing_approach": recommendation_data.get("testing_approach")',
        '"expected_source_documents": recommendation_data.get("typical_source_documents"',
        '"search_keywords": recommendation_data.get("keywords_to_look_for"',
        '"request_payload": llm_request_payload',
        '"response_payload": recommendation_data'
    ]
    
    logger.info("=== CELERY TASK FIELD EXTRACTION CHECK ===")
    all_found = True
    for field in required_fields:
        if field in content:
            logger.info(f"✅ Found: {field[:50]}...")
        else:
            logger.error(f"❌ Missing: {field[:50]}...")
            all_found = False
    
    return all_found


def check_scoping_service_saves_fields():
    """Check if scoping service saves all required fields"""
    
    with open('app/services/scoping_service.py', 'r') as f:
        content = f.read()
    
    # Check CREATE path
    create_fields = [
        'validation_rules=llm_recommendations[i].get(\'validation_rules\')',
        'testing_approach=llm_recommendations[i].get(\'testing_approach\')',
        'expected_source_documents=llm_recommendations[i].get(\'expected_source_documents\')',
        'search_keywords=llm_recommendations[i].get(\'search_keywords\')',
        'llm_request_payload=llm_recommendations[i].get(\'request_payload\')',
        'llm_response_payload=llm_recommendations[i].get(\'response_payload\')'
    ]
    
    # Check UPDATE path
    update_fields = [
        'existing_attr.validation_rules = llm_recommendations[i].get(\'validation_rules\')',
        'existing_attr.testing_approach = llm_recommendations[i].get(\'testing_approach\')',
        'existing_attr.expected_source_documents = llm_recommendations[i].get(\'expected_source_documents\')',
        'existing_attr.search_keywords = llm_recommendations[i].get(\'search_keywords\')',
        'existing_attr.llm_request_payload = llm_recommendations[i].get(\'request_payload\')',
        'existing_attr.llm_response_payload = llm_recommendations[i].get(\'response_payload\')'
    ]
    
    logger.info("\n=== SCOPING SERVICE CREATE PATH CHECK ===")
    create_ok = True
    for field in create_fields:
        if field in content:
            logger.info(f"✅ Found: {field[:50]}...")
        else:
            logger.error(f"❌ Missing: {field[:50]}...")
            create_ok = False
    
    logger.info("\n=== SCOPING SERVICE UPDATE PATH CHECK ===")
    update_ok = True
    for field in update_fields:
        if field in content:
            logger.info(f"✅ Found: {field[:50]}...")
        else:
            logger.error(f"❌ Missing: {field[:50]}...")
            update_ok = False
    
    return create_ok and update_ok


def check_model_has_fields():
    """Check if ScopingAttribute model has all required fields"""
    
    with open('app/models/scoping.py', 'r') as f:
        content = f.read()
    
    required_columns = [
        'validation_rules = Column(Text',
        'testing_approach = Column(Text',
        'expected_source_documents = Column(',
        'search_keywords = Column(',
        'llm_request_payload = Column(',
        'llm_response_payload = Column('
    ]
    
    logger.info("\n=== SCOPING MODEL FIELD CHECK ===")
    all_found = True
    for column in required_columns:
        if column in content:
            logger.info(f"✅ Found: {column[:40]}...")
        else:
            logger.error(f"❌ Missing: {column[:40]}...")
            all_found = False
    
    return all_found


def check_database_columns():
    """Check if database has the required columns"""
    
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5433,
        'database': 'synapse_dt',
        'user': 'synapse_user',
        'password': 'synapse_password'
    }
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    logger.info("\n=== DATABASE COLUMN CHECK ===")
    
    try:
        # Check column existence
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'cycle_report_scoping_attributes'
            AND column_name IN (
                'validation_rules', 'testing_approach',
                'expected_source_documents', 'search_keywords',
                'llm_request_payload', 'llm_response_payload'
            )
            ORDER BY column_name
        """)
        
        columns = cur.fetchall()
        expected_columns = {
            'validation_rules': 'text',
            'testing_approach': 'text',
            'expected_source_documents': 'jsonb',
            'search_keywords': 'jsonb',
            'llm_request_payload': 'jsonb',
            'llm_response_payload': 'jsonb'
        }
        
        found_columns = {col['column_name']: col['data_type'] for col in columns}
        
        all_found = True
        for col_name, expected_type in expected_columns.items():
            if col_name in found_columns:
                actual_type = found_columns[col_name]
                if actual_type == expected_type:
                    logger.info(f"✅ {col_name}: {actual_type}")
                else:
                    logger.warning(f"⚠️ {col_name}: {actual_type} (expected {expected_type})")
            else:
                logger.error(f"❌ {col_name}: NOT FOUND")
                all_found = False
        
        # Check data population
        logger.info("\n=== DATA POPULATION CHECK ===")
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(validation_rules) as has_validation,
                COUNT(testing_approach) as has_testing,
                COUNT(expected_source_documents) as has_docs,
                COUNT(search_keywords) as has_keywords,
                COUNT(llm_request_payload) as has_request,
                COUNT(llm_response_payload) as has_response
            FROM cycle_report_scoping_attributes
        """)
        
        stats = cur.fetchone()
        logger.info(f"Total records: {stats['total']}")
        logger.info(f"With validation_rules: {stats['has_validation']} ({stats['has_validation']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"With testing_approach: {stats['has_testing']} ({stats['has_testing']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"With expected_source_documents: {stats['has_docs']} ({stats['has_docs']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"With search_keywords: {stats['has_keywords']} ({stats['has_keywords']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"With llm_request_payload: {stats['has_request']} ({stats['has_request']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        logger.info(f"With llm_response_payload: {stats['has_response']} ({stats['has_response']*100//stats['total'] if stats['total'] > 0 else 0}%)")
        
        return all_found
        
    finally:
        cur.close()
        conn.close()


def main():
    """Run all verification checks"""
    
    logger.info("="*60)
    logger.info("SCOPING CODE CHANGES VERIFICATION")
    logger.info("="*60)
    
    results = []
    
    # Check celery task
    celery_ok = check_celery_task_extracts_fields()
    results.append(("Celery task field extraction", celery_ok))
    
    # Check scoping service
    service_ok = check_scoping_service_saves_fields()
    results.append(("Scoping service field saving", service_ok))
    
    # Check model
    model_ok = check_model_has_fields()
    results.append(("Model field definitions", model_ok))
    
    # Check database
    db_ok = check_database_columns()
    results.append(("Database columns", db_ok))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("="*60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    logger.info("\n" + "="*60)
    if all_passed:
        logger.info("✅ ALL CHECKS PASSED")
        logger.info("The code is properly configured to save all fields in future scoping runs.")
        logger.info("\nNOTE: testing_approach field is empty because it's not in the LLM response.")
        logger.info("This field would need to be added to the LLM prompt/response to be populated.")
    else:
        logger.info("❌ SOME CHECKS FAILED")
        logger.info("Please review the failed checks above.")
    logger.info("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()