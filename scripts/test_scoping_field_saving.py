#!/usr/bin/env python
"""
Test script to verify that scoping service properly saves all fields
when processing LLM recommendations
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mock_llm_recommendation():
    """Create a mock LLM recommendation with all fields populated"""
    return {
        "attribute_name": "test_attribute",
        "risk_score": 75,
        "enhanced_rationale": {
            "regulatory_usage": "Used for regulatory reporting"
        },
        "risk_factors": ["high_risk", "critical_data"],
        "typical_source_documents": "Bank statements, Credit reports, Loan applications",
        "keywords_to_look_for": "credit limit, balance, APR, interest rate",
        "validation_rules": "Must be numeric, Range: 0-100000, Format: decimal(10,2)",
        "testing_approach": "Verify against source documents, Check calculations, Validate ranges",
        "is_cde": True,
        "is_primary_key": False,
        "has_historical_issues": True,
        "data_quality_score": 85.5,
        "data_quality_issues": ["missing_values", "outliers"],
        "processing_time_ms": 1250
    }


async def test_scoping_service():
    """Test that the scoping service properly saves all fields"""
    
    from app.core.database import AsyncSessionLocal
    from app.services.scoping_service import ScopingService
    from sqlalchemy import select
    from app.models.scoping import ScopingAttribute, ScopingVersion
    from app.models.workflow import WorkflowPhase
    
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting scoping service field saving test...")
            
            # Initialize service
            scoping_service = ScopingService(db)
            
            # Find or create a test version to work with (must be draft to edit)
            version_query = select(ScopingVersion).where(
                ScopingVersion.version_status == 'draft'
            ).limit(1)
            version_result = await db.execute(version_query)
            version = version_result.scalar_one_or_none()
            
            if not version:
                logger.info("No draft version found, creating a test version...")
                # Find a phase to create version for
                phase_query = select(WorkflowPhase).where(
                    WorkflowPhase.phase_name == 'Scoping'
                ).limit(1)
                phase_result = await db.execute(phase_query)
                phase = phase_result.scalar_one_or_none()
                
                if not phase:
                    logger.error("No scoping phase found")
                    return False
                
                # Create a draft version for testing
                version = await scoping_service.create_version(
                    phase_id=phase.phase_id,
                    version_notes="Test version for field saving validation",
                    user_id=1
                )
                logger.info(f"Created test version {version.version_id}")
            
            logger.info(f"Using version {version.version_id} for testing")
            
            # Create mock LLM recommendation
            mock_recommendation = create_mock_llm_recommendation()
            
            # Create mock request payload
            mock_request_payload = {
                "model": "claude-3-5-sonnet",
                "temperature": 0.3,
                "max_tokens": 2000,
                "timestamp": datetime.utcnow().isoformat(),
                "test_run": True
            }
            
            # Prepare recommendation for service
            service_recommendation = {
                "recommended_action": "Test",
                "confidence_score": mock_recommendation["risk_score"] / 100.0,
                "rationale": mock_recommendation["enhanced_rationale"]["regulatory_usage"],
                "risk_factors": mock_recommendation["risk_factors"],
                "expected_source_documents": mock_recommendation["typical_source_documents"].split(", "),
                "search_keywords": mock_recommendation["keywords_to_look_for"].split(", "),
                "validation_rules": mock_recommendation["validation_rules"],
                "testing_approach": mock_recommendation["testing_approach"],
                "is_cde": mock_recommendation["is_cde"],
                "is_primary_key": mock_recommendation["is_primary_key"],
                "has_historical_issues": mock_recommendation["has_historical_issues"],
                "data_quality_score": mock_recommendation["data_quality_score"],
                "data_quality_issues": mock_recommendation["data_quality_issues"],
                "provider": "claude",
                "processing_time_ms": mock_recommendation["processing_time_ms"],
                "request_payload": mock_request_payload,
                "response_payload": mock_recommendation
            }
            
            # Find a test attribute to use (pick one that exists)
            # We'll use attribute_id 29 which we know exists
            test_attribute_id = 29
            
            logger.info(f"Testing with attribute_id {test_attribute_id}")
            
            # Call the service method
            result = await scoping_service.add_attributes_to_version(
                version_id=version.version_id,
                attribute_ids=[test_attribute_id],
                llm_recommendations=[service_recommendation],
                user_id=1  # Test user
            )
            
            if result and len(result) > 0:
                created_attr = result[0]
                logger.info(f"✅ Successfully created/updated scoping attribute")
                
                # Verify all fields were saved
                verification_results = []
                
                # Check text fields
                if created_attr.validation_rules:
                    verification_results.append("✅ validation_rules saved")
                else:
                    verification_results.append("❌ validation_rules NOT saved")
                
                if created_attr.testing_approach:
                    verification_results.append("✅ testing_approach saved")
                else:
                    verification_results.append("❌ testing_approach NOT saved")
                
                # Check JSONB fields
                if created_attr.expected_source_documents:
                    verification_results.append(f"✅ expected_source_documents saved ({len(created_attr.expected_source_documents)} items)")
                else:
                    verification_results.append("❌ expected_source_documents NOT saved")
                
                if created_attr.search_keywords:
                    verification_results.append(f"✅ search_keywords saved ({len(created_attr.search_keywords)} items)")
                else:
                    verification_results.append("❌ search_keywords NOT saved")
                
                if created_attr.llm_request_payload:
                    verification_results.append("✅ llm_request_payload saved")
                else:
                    verification_results.append("❌ llm_request_payload NOT saved")
                
                if created_attr.llm_response_payload:
                    verification_results.append("✅ llm_response_payload saved")
                else:
                    verification_results.append("❌ llm_response_payload NOT saved")
                
                # Print results
                logger.info("\n=== FIELD VERIFICATION RESULTS ===")
                for result in verification_results:
                    logger.info(f"  {result}")
                
                # Check specific field values
                logger.info("\n=== FIELD VALUES ===")
                logger.info(f"  validation_rules: {created_attr.validation_rules[:50] if created_attr.validation_rules else 'None'}...")
                logger.info(f"  testing_approach: {created_attr.testing_approach[:50] if created_attr.testing_approach else 'None'}...")
                logger.info(f"  expected_source_documents: {created_attr.expected_source_documents}")
                logger.info(f"  search_keywords: {created_attr.search_keywords}")
                
                # Overall success check
                all_passed = all("✅" in r for r in verification_results)
                if all_passed:
                    logger.info("\n🎉 ALL FIELDS PROPERLY SAVED! The fix is working correctly.")
                    return True
                else:
                    logger.warning("\n⚠️ Some fields were not saved properly. Check the implementation.")
                    return False
            else:
                logger.error("❌ Failed to create/update scoping attribute")
                return False
                
        except Exception as e:
            logger.error(f"Test failed with error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # Don't commit the test data
            await db.rollback()
            logger.info("Rolled back test transaction")


async def verify_existing_data():
    """Verify that existing scoping attributes have the correct fields populated"""
    
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select, func
    from app.models.scoping import ScopingAttribute
    
    async with AsyncSessionLocal() as db:
        try:
            logger.info("\n=== VERIFYING EXISTING DATA ===")
            
            # Count records with each field populated
            total_query = select(func.count(ScopingAttribute.attribute_id))
            total_result = await db.execute(total_query)
            total_count = total_result.scalar()
            
            # Count validation_rules
            validation_query = select(func.count(ScopingAttribute.attribute_id)).where(
                ScopingAttribute.validation_rules.isnot(None)
            )
            validation_result = await db.execute(validation_query)
            validation_count = validation_result.scalar()
            
            # Count testing_approach
            testing_query = select(func.count(ScopingAttribute.attribute_id)).where(
                ScopingAttribute.testing_approach.isnot(None)
            )
            testing_result = await db.execute(testing_query)
            testing_count = testing_result.scalar()
            
            # Count expected_source_documents
            docs_query = select(func.count(ScopingAttribute.attribute_id)).where(
                ScopingAttribute.expected_source_documents.isnot(None)
            )
            docs_result = await db.execute(docs_query)
            docs_count = docs_result.scalar()
            
            # Count search_keywords
            keywords_query = select(func.count(ScopingAttribute.attribute_id)).where(
                ScopingAttribute.search_keywords.isnot(None)
            )
            keywords_result = await db.execute(keywords_query)
            keywords_count = keywords_result.scalar()
            
            logger.info(f"Total scoping attributes: {total_count}")
            logger.info(f"With validation_rules: {validation_count} ({validation_count*100//total_count if total_count > 0 else 0}%)")
            logger.info(f"With testing_approach: {testing_count} ({testing_count*100//total_count if total_count > 0 else 0}%)")
            logger.info(f"With expected_source_documents: {docs_count} ({docs_count*100//total_count if total_count > 0 else 0}%)")
            logger.info(f"With search_keywords: {keywords_count} ({keywords_count*100//total_count if total_count > 0 else 0}%)")
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")


async def main():
    """Main function to run all tests"""
    logger.info("="*60)
    logger.info("SCOPING FIELD SAVING TEST")
    logger.info("="*60)
    
    # Run the test
    test_passed = await test_scoping_service()
    
    # Verify existing data
    await verify_existing_data()
    
    logger.info("\n" + "="*60)
    if test_passed:
        logger.info("✅ TEST PASSED: Scoping service properly saves all fields")
    else:
        logger.info("❌ TEST FAILED: Issues found with field saving")
    logger.info("="*60)
    
    return test_passed


if __name__ == "__main__":
    asyncio.run(main())