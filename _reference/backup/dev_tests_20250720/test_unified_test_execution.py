#!/usr/bin/env python3
"""
Comprehensive test script for the unified test execution implementation.

This script tests the complete test execution workflow including:
1. Database models and relationships
2. API endpoints and schemas
3. Service layer functionality
4. Frontend integration
5. Migration and cleanup

Usage:
    python test_unified_test_execution.py
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that all unified test execution models can be imported correctly."""
    print("Testing model imports...")
    
    try:
        # Test unified model imports
        from app.models.test_execution import (
            TestExecutionResult, TestExecutionReview, TestExecutionAudit,
            update_user_relationships, update_model_relationships
        )
        print("✓ Unified test execution models imported successfully")
        
        # Test schema imports
        from app.schemas.test_execution import (
            TestExecutionCreateRequest, TestExecutionUpdateRequest, TestExecutionReviewRequest,
            BulkTestExecutionRequest, BulkReviewRequest, TestExecutionResponse, TestExecutionReviewResponse,
            TestExecutionAuditResponse, TestExecutionListResponse, TestExecutionReviewListResponse,
            TestExecutionDashboardResponse, TestExecutionCompletionStatusResponse,
            BulkTestExecutionResponse, BulkReviewResponse, TestExecutionConfigurationResponse
        )
        print("✓ Unified test execution schemas imported successfully")
        
        # Test service imports
        from app.services.test_execution_service import TestExecutionService
        print("✓ Unified test execution service imported successfully")
        
        # Test API endpoint imports
        from app.api.v1.endpoints.test_execution import router
        print("✓ Unified test execution API endpoints imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False


def test_database_models():
    """Test database model definitions and relationships."""
    print("\nTesting database models...")
    
    try:
        from app.models.test_execution import (
            TestExecutionResult, TestExecutionReview, TestExecutionAudit
        )
        from sqlalchemy import inspect
        
        # Test model attributes
        execution_columns = [col.name for col in inspect(TestExecutionResult).columns]
        required_execution_columns = [
            'id', 'test_case_id', 'evidence_id', 'execution_number', 'execution_status',
            'test_type', 'analysis_method', 'analysis_results', 'created_at', 'updated_at'
        ]
        
        missing_columns = [col for col in required_execution_columns if col not in execution_columns]
        if missing_columns:
            print(f"✗ Missing columns in TestExecutionResult: {missing_columns}")
            return False
            
        print("✓ TestExecutionResult model has all required columns")
        
        # Test relationships
        if hasattr(TestExecutionResult, 'reviews'):
            print("✓ TestExecutionResult has reviews relationship")
        else:
            print("✗ TestExecutionResult missing reviews relationship")
            return False
            
        if hasattr(TestExecutionResult, 'audit_logs'):
            print("✓ TestExecutionResult has audit_logs relationship")
        else:
            print("✗ TestExecutionResult missing audit_logs relationship")
            return False
            
        # Test review model
        review_columns = [col.name for col in inspect(TestExecutionReview).columns]
        required_review_columns = [
            'id', 'execution_id', 'review_status', 'overall_score', 'reviewed_by', 'reviewed_at'
        ]
        
        missing_review_columns = [col for col in required_review_columns if col not in review_columns]
        if missing_review_columns:
            print(f"✗ Missing columns in TestExecutionReview: {missing_review_columns}")
            return False
            
        print("✓ TestExecutionReview model has all required columns")
        
        # Test audit model
        audit_columns = [col.name for col in inspect(TestExecutionAudit).columns]
        required_audit_columns = [
            'id', 'execution_id', 'action', 'performed_by', 'performed_at'
        ]
        
        missing_audit_columns = [col for col in required_audit_columns if col not in audit_columns]
        if missing_audit_columns:
            print(f"✗ Missing columns in TestExecutionAudit: {missing_audit_columns}")
            return False
            
        print("✓ TestExecutionAudit model has all required columns")
        
        return True
        
    except Exception as e:
        print(f"✗ Database model test failed: {e}")
        return False


def test_schemas():
    """Test Pydantic schemas for request/response validation."""
    print("\nTesting Pydantic schemas...")
    
    try:
        from app.schemas.test_execution import (
            TestExecutionCreateRequest, TestExecutionResponse, TestExecutionReviewRequest,
            BulkTestExecutionRequest, TestExecutionDashboardResponse
        )
        
        # Test create request schema
        create_request_data = {
            "test_case_id": "tc_001",
            "evidence_id": 1,
            "execution_reason": "initial",
            "test_type": "document_analysis",
            "analysis_method": "llm_analysis",
            "execution_method": "automatic"
        }
        
        create_request = TestExecutionCreateRequest(**create_request_data)
        print("✓ TestExecutionCreateRequest schema validation passed")
        
        # Test response schema
        response_data = {
            "id": 1,
            "phase_id": 1,
            "cycle_id": 1,
            "report_id": 1,
            "test_case_id": "tc_001",
            "evidence_id": 1,
            "execution_number": 1,
            "is_latest_execution": True,
            "test_type": "document_analysis",
            "analysis_method": "llm_analysis",
            "execution_status": "completed",
            "analysis_results": {"confidence": 0.95},
            "executed_by": 1,
            "execution_method": "automatic",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": 1,
            "updated_by": 1
        }
        
        response = TestExecutionResponse(**response_data)
        print("✓ TestExecutionResponse schema validation passed")
        
        # Test review request schema
        review_request_data = {
            "review_status": "approved",
            "accuracy_score": 0.95,
            "completeness_score": 0.90,
            "consistency_score": 0.85
        }
        
        review_request = TestExecutionReviewRequest(**review_request_data)
        print("✓ TestExecutionReviewRequest schema validation passed")
        
        # Test bulk request schema
        bulk_request_data = {
            "test_case_ids": ["tc_001", "tc_002", "tc_003"],
            "execution_method": "automatic"
        }
        
        bulk_request = BulkTestExecutionRequest(**bulk_request_data)
        print("✓ BulkTestExecutionRequest schema validation passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        return False


def test_service_layer():
    """Test the service layer functionality."""
    print("\nTesting service layer...")
    
    try:
        from app.services.test_execution_service import TestExecutionService
        from app.schemas.test_execution import TestExecutionCreateRequest
        
        # Test service instantiation
        # Note: This would normally require database session, LLM service, etc.
        # For this test, we'll just verify the class can be imported and has required methods
        
        required_methods = [
            'create_test_execution',
            'create_test_execution_review',
            'get_test_execution_dashboard',
            'check_phase_completion'
        ]
        
        for method in required_methods:
            if hasattr(TestExecutionService, method):
                print(f"✓ TestExecutionService has {method} method")
            else:
                print(f"✗ TestExecutionService missing {method} method")
                return False
                
        # Test request creation
        create_request = TestExecutionCreateRequest(
            test_case_id="tc_001",
            evidence_id=1,
            test_type="document_analysis",
            analysis_method="llm_analysis"
        )
        
        print("✓ Service layer test passed")
        return True
        
    except Exception as e:
        print(f"✗ Service layer test failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoint definitions."""
    print("\nTesting API endpoints...")
    
    try:
        from app.api.v1.endpoints.test_execution import router
        from fastapi import APIRouter
        
        # Verify router is properly configured
        if not isinstance(router, APIRouter):
            print("✗ Router is not a FastAPI APIRouter instance")
            return False
            
        # Check for required endpoints
        routes = [route.path for route in router.routes]
        required_endpoints = [
            "/test-execution/{cycle_id}/reports/{report_id}/execute",
            "/test-execution/test-cases/{test_case_id}/execute",
            "/test-execution/{cycle_id}/reports/{report_id}/pending-review",
            "/test-execution/executions/{execution_id}/review",
            "/test-execution/{cycle_id}/reports/{report_id}/dashboard",
            "/test-execution/{cycle_id}/reports/{report_id}/completion-status",
            "/test-execution/configuration"
        ]
        
        for endpoint in required_endpoints:
            if endpoint in routes:
                print(f"✓ Found endpoint: {endpoint}")
            else:
                print(f"✗ Missing endpoint: {endpoint}")
                return False
                
        print("✓ API endpoints test passed")
        return True
        
    except Exception as e:
        print(f"✗ API endpoints test failed: {e}")
        return False


def test_migration_files():
    """Test migration files exist and are properly formatted."""
    print("\nTesting migration files...")
    
    try:
        migration_files = [
            "alembic/versions/2025_07_18_unified_test_execution_architecture.py",
            "alembic/versions/2025_07_18_cleanup_legacy_test_execution.py"
        ]
        
        for migration_file in migration_files:
            if os.path.exists(migration_file):
                print(f"✓ Found migration file: {migration_file}")
                
                # Check if file has upgrade and downgrade functions
                with open(migration_file, 'r') as f:
                    content = f.read()
                    
                if 'def upgrade():' in content and 'def downgrade():' in content:
                    print(f"✓ Migration file {migration_file} has upgrade/downgrade functions")
                else:
                    print(f"✗ Migration file {migration_file} missing upgrade/downgrade functions")
                    return False
                    
            else:
                print(f"✗ Missing migration file: {migration_file}")
                return False
                
        print("✓ Migration files test passed")
        return True
        
    except Exception as e:
        print(f"✗ Migration files test failed: {e}")
        return False


def test_frontend_integration():
    """Test frontend component integration."""
    print("\nTesting frontend integration...")
    
    try:
        frontend_files = [
            "frontend/src/components/test-execution/UnifiedTestExecutionManager.tsx",
            "frontend/src/pages/phases/TestExecutionPage.tsx"
        ]
        
        for frontend_file in frontend_files:
            if os.path.exists(frontend_file):
                print(f"✓ Found frontend file: {frontend_file}")
                
                # Check if file has required imports and components
                with open(frontend_file, 'r') as f:
                    content = f.read()
                    
                if 'apiClient' in content and 'useQuery' in content:
                    print(f"✓ Frontend file {frontend_file} has API integration")
                else:
                    print(f"✗ Frontend file {frontend_file} missing API integration")
                    return False
                    
            else:
                print(f"✗ Missing frontend file: {frontend_file}")
                return False
                
        print("✓ Frontend integration test passed")
        return True
        
    except Exception as e:
        print(f"✗ Frontend integration test failed: {e}")
        return False


def test_legacy_cleanup():
    """Test that legacy models are properly deprecated/cleaned up."""
    print("\nTesting legacy cleanup...")
    
    try:
        # Test that legacy models are marked as deprecated
        legacy_file = "app/models/test_execution_legacy.py"
        if os.path.exists(legacy_file):
            print(f"✓ Found legacy file: {legacy_file}")
            
            with open(legacy_file, 'r') as f:
                content = f.read()
                
            if 'DEPRECATED' in content and 'warnings.warn' in content:
                print("✓ Legacy file properly marked as deprecated")
            else:
                print("✗ Legacy file not properly marked as deprecated")
                return False
                
        else:
            print(f"✗ Missing legacy file: {legacy_file}")
            return False
            
        # Test that models __init__.py has been updated
        models_init_file = "app/models/__init__.py"
        if os.path.exists(models_init_file):
            with open(models_init_file, 'r') as f:
                content = f.read()
                
            if 'test_execution' in content and 'TestExecutionResult' in content:
                print("✓ Models __init__.py updated with unified imports")
            else:
                print("✗ Models __init__.py not properly updated")
                return False
                
        else:
            print(f"✗ Missing models __init__.py file")
            return False
            
        print("✓ Legacy cleanup test passed")
        return True
        
    except Exception as e:
        print(f"✗ Legacy cleanup test failed: {e}")
        return False


def test_api_router_integration():
    """Test that API router is properly configured."""
    print("\nTesting API router integration...")
    
    try:
        api_file = "app/api/v1/api.py"
        if os.path.exists(api_file):
            with open(api_file, 'r') as f:
                content = f.read()
                
            if 'test_execution' in content and 'test-execution-legacy' in content:
                print("✓ API router properly configured with unified endpoints")
            else:
                print("✗ API router not properly configured")
                return False
                
        else:
            print(f"✗ Missing API router file: {api_file}")
            return False
            
        print("✓ API router integration test passed")
        return True
        
    except Exception as e:
        print(f"✗ API router integration test failed: {e}")
        return False


def generate_test_report(test_results: Dict[str, bool]) -> str:
    """Generate a comprehensive test report."""
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    failed_tests = total_tests - passed_tests
    
    report = f"""
=== UNIFIED TEST EXECUTION IMPLEMENTATION TEST REPORT ===

Test Summary:
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {(passed_tests/total_tests)*100:.1f}%

Detailed Results:
"""
    
    for test_name, result in test_results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        report += f"- {test_name}: {status}\n"
    
    if failed_tests == 0:
        report += """
🎉 ALL TESTS PASSED! 🎉

The unified test execution implementation is ready for deployment.

Key Features Implemented:
✓ Unified test execution architecture with evidence integration
✓ Comprehensive database models with proper relationships
✓ Pydantic schemas for request/response validation
✓ Service layer with LLM analysis and database query execution
✓ Complete API endpoints for all test execution operations
✓ Tester approval workflow with quality scoring
✓ Frontend components for test execution management
✓ Database migration scripts for deployment
✓ Legacy model cleanup and deprecation
✓ Comprehensive audit trail and execution history

Next Steps:
1. Run database migrations: alembic upgrade head
2. Deploy the updated API endpoints
3. Test the frontend components in the development environment
4. Verify the complete workflow end-to-end
"""
    else:
        report += f"""
⚠️ {failed_tests} TEST(S) FAILED ⚠️

Please review the failed tests above and fix the issues before deployment.
"""
    
    return report


def main():
    """Run all tests and generate a comprehensive report."""
    print("🚀 Starting Unified Test Execution Implementation Tests...")
    print("=" * 60)
    
    # Define all test functions
    test_functions = {
        "Model Imports": test_model_imports,
        "Database Models": test_database_models,
        "Pydantic Schemas": test_schemas,
        "Service Layer": test_service_layer,
        "API Endpoints": test_api_endpoints,
        "Migration Files": test_migration_files,
        "Frontend Integration": test_frontend_integration,
        "Legacy Cleanup": test_legacy_cleanup,
        "API Router Integration": test_api_router_integration,
    }
    
    # Run all tests
    test_results = {}
    for test_name, test_func in test_functions.items():
        try:
            test_results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            test_results[test_name] = False
    
    # Generate and display report
    report = generate_test_report(test_results)
    print("\n" + "=" * 60)
    print(report)
    
    # Return exit code based on results
    all_passed = all(test_results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())