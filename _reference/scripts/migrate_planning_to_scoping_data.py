#!/usr/bin/env python
"""
Migrate data from planning attributes to scoping attributes
This script moves LLM-related fields that were incorrectly placed in planning to scoping
"""

import asyncio
import logging
from sqlalchemy import select, update, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_fields_to_scoping():
    """
    Migrate fields from planning to scoping where appropriate.
    
    This migration:
    1. Copies validation_rules, testing_approach from planning to scoping
    2. Maps typical_source_documents -> expected_source_documents  
    3. Maps keywords_to_look_for -> search_keywords
    4. Populates missing llm_request_payload for NULL records
    """
    
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting data migration from planning to scoping...")
            
            # Query to find planning attributes with data that needs migration
            planning_query = text("""
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
            
            result = await db.execute(planning_query)
            planning_attrs = result.fetchall()
            
            logger.info(f"Found {len(planning_attrs)} planning attributes with data to migrate")
            
            migrated_count = 0
            for p_attr in planning_attrs:
                # Find corresponding scoping attributes
                scoping_query = text("""
                    SELECT version_id, attribute_id
                    FROM cycle_report_scoping_attributes
                    WHERE attribute_id = :planning_id
                """)
                
                scoping_result = await db.execute(
                    scoping_query,
                    {"planning_id": int(p_attr.planning_id)}
                )
                scoping_attrs = scoping_result.fetchall()
                
                if scoping_attrs:
                    logger.info(f"Migrating data for attribute '{p_attr.attribute_name}' to {len(scoping_attrs)} scoping records")
                    
                    for s_attr in scoping_attrs:
                        # Build update statement for scoping attribute
                        update_values = {}
                        
                        # Only update if the scoping field is NULL
                        if p_attr.validation_rules:
                            update_values["validation_rules"] = p_attr.validation_rules
                        
                        if p_attr.testing_approach:
                            update_values["testing_approach"] = p_attr.testing_approach
                        
                        # Map typical_source_documents to expected_source_documents
                        if p_attr.typical_source_documents:
                            update_values["expected_source_documents"] = p_attr.typical_source_documents
                        
                        # Map keywords_to_look_for to search_keywords
                        if p_attr.keywords_to_look_for:
                            update_values["search_keywords"] = p_attr.keywords_to_look_for
                        
                        if update_values:
                            # Add update timestamp
                            update_values["updated_at"] = datetime.utcnow()
                            
                            # Build and execute update query
                            update_query = text("""
                                UPDATE cycle_report_scoping_attributes
                                SET validation_rules = COALESCE(:validation_rules, validation_rules),
                                    testing_approach = COALESCE(:testing_approach, testing_approach),
                                    expected_source_documents = COALESCE(:expected_source_documents, expected_source_documents),
                                    search_keywords = COALESCE(:search_keywords, search_keywords),
                                    updated_at = :updated_at
                                WHERE version_id = :version_id AND attribute_id = :attribute_id
                            """)
                            
                            await db.execute(
                                update_query,
                                {
                                    "version_id": s_attr[0],  # version_id as UUID
                                    "attribute_id": int(s_attr[1]),  # attribute_id as int
                                    "validation_rules": update_values.get("validation_rules"),
                                    "testing_approach": update_values.get("testing_approach"),
                                    "expected_source_documents": update_values.get("expected_source_documents"),
                                    "search_keywords": update_values.get("search_keywords"),
                                    "updated_at": update_values.get("updated_at")
                                }
                            )
                            migrated_count += 1
            
            # Now populate missing llm_request_payload
            logger.info("Populating missing llm_request_payload fields...")
            
            populate_query = text("""
                UPDATE cycle_report_scoping_attributes
                SET llm_request_payload = '{"model": "claude-3-5-sonnet", "temperature": 0.3, "max_tokens": 2000, "migrated": true}'::jsonb
                WHERE llm_request_payload IS NULL 
                   OR llm_request_payload::text = 'null'
                   OR llm_request_payload::text = '{}'
            """)
            
            result = await db.execute(populate_query)
            populated_count = result.rowcount
            
            logger.info(f"Populated llm_request_payload for {populated_count} records")
            
            # Commit all changes
            await db.commit()
            
            logger.info(f"✅ Migration completed successfully!")
            logger.info(f"   - Migrated fields for {migrated_count} scoping attributes")
            logger.info(f"   - Populated llm_request_payload for {populated_count} records")
            
            # Verify migration
            verify_query = text("""
                SELECT COUNT(*) as null_count
                FROM cycle_report_scoping_attributes
                WHERE llm_request_payload IS NULL
            """)
            
            verify_result = await db.execute(verify_query)
            null_count = verify_result.scalar()
            
            if null_count > 0:
                logger.warning(f"⚠️ Still have {null_count} records with NULL llm_request_payload")
            else:
                logger.info("✅ All scoping attributes have llm_request_payload populated")
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            await db.rollback()
            raise


async def verify_migration():
    """Verify that the migration was successful"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Check for any planning attributes still having the fields
            check_query = text("""
                SELECT COUNT(*) as count
                FROM cycle_report_planning_attributes
                WHERE validation_rules IS NOT NULL
                   OR testing_approach IS NOT NULL
                   OR typical_source_documents IS NOT NULL
                   OR keywords_to_look_for IS NOT NULL
                   OR llm_rationale IS NOT NULL
                   OR risk_score IS NOT NULL
            """)
            
            result = await db.execute(check_query)
            count = result.scalar()
            
            if count > 0:
                logger.info(f"Note: {count} planning attributes still have data in fields to be dropped")
                logger.info("This is expected before running the schema migration to drop these columns")
            
            # Check scoping attributes have the data
            scoping_check = text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(validation_rules) as has_validation_rules,
                    COUNT(testing_approach) as has_testing_approach,
                    COUNT(expected_source_documents) as has_expected_docs,
                    COUNT(search_keywords) as has_search_keywords,
                    COUNT(llm_request_payload) as has_request_payload
                FROM cycle_report_scoping_attributes
            """)
            
            result = await db.execute(scoping_check)
            stats = result.fetchone()
            
            logger.info("Scoping attributes statistics:")
            logger.info(f"  Total: {stats.total}")
            logger.info(f"  With validation_rules: {stats.has_validation_rules}")
            logger.info(f"  With testing_approach: {stats.has_testing_approach}")
            logger.info(f"  With expected_source_documents: {stats.has_expected_docs}")
            logger.info(f"  With search_keywords: {stats.has_search_keywords}")
            logger.info(f"  With llm_request_payload: {stats.has_request_payload}")
            
        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            raise


if __name__ == "__main__":
    logger.info("Starting planning to scoping data migration...")
    
    # Run migration
    asyncio.run(migrate_fields_to_scoping())
    
    # Verify results
    logger.info("\n=== Verifying migration results ===")
    asyncio.run(verify_migration())
    
    logger.info("\n✅ Migration script completed")
    logger.info("Note: After verifying the data migration, run the Alembic migrations to update the schema")