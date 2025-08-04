#!/usr/bin/env python3
"""
Simple test for the unified planning system
Tests basic imports and API structure without running a full server
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, '/Users/dineshpatel/code/projects/SynapseDTE')

def test_planning_imports():
    """Test that all planning components can be imported"""
    print("Testing planning imports...")
    
    try:
        # Test model imports
        from app.models.planning import (
            PlanningVersion, PlanningDataSource, PlanningAttribute, PlanningPDEMapping,
            VersionStatus, DataSourceType, AttributeDataType, InformationSecurityClassification,
            MappingType, Decision, Status
        )
        print("✓ Planning models imported successfully")
        
        # Test schema imports
        from app.schemas.planning_unified import (
            PlanningVersionCreate, PlanningVersionResponse,
            PlanningDataSourceCreate, PlanningDataSourceResponse,
            PlanningAttributeCreate, PlanningAttributeResponse,
            PlanningPDEMappingCreate, PlanningPDEMappingResponse
        )
        print("✓ Planning schemas imported successfully")
        
        # Test service import (without database connection)
        try:
            from app.services.planning_service_unified import PlanningServiceUnified
            print("✓ Planning service imported successfully")
        except ImportError as e:
            print(f"✗ Planning service import failed: {e}")
            return False
        
        # Test API endpoint import
        try:
            from app.api.v1.endpoints.planning_unified import router
            print("✓ Planning API endpoints imported successfully")
        except ImportError as e:
            print(f"✗ Planning API import failed: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_enum_values():
    """Test that enums have correct values"""
    print("\nTesting enum values...")
    
    try:
        from app.models.planning import VersionStatus, DataSourceType, Decision, Status
        
        # Test VersionStatus enum
        expected_version_statuses = {'draft', 'pending_approval', 'approved', 'rejected', 'superseded'}
        actual_version_statuses = {status.value for status in VersionStatus}
        if expected_version_statuses == actual_version_statuses:
            print("✓ VersionStatus enum values correct")
        else:
            print(f"✗ VersionStatus enum mismatch. Expected: {expected_version_statuses}, Got: {actual_version_statuses}")
            return False
        
        # Test DataSourceType enum
        expected_data_source_types = {'database', 'file', 'api', 'sftp', 's3', 'other'}
        actual_data_source_types = {ds_type.value for ds_type in DataSourceType}
        if expected_data_source_types == actual_data_source_types:
            print("✓ DataSourceType enum values correct")
        else:
            print(f"✗ DataSourceType enum mismatch. Expected: {expected_data_source_types}, Got: {actual_data_source_types}")
            return False
        
        # Test Decision enum
        expected_decisions = {'approve', 'reject', 'request_changes'}
        actual_decisions = {decision.value for decision in Decision}
        if expected_decisions == actual_decisions:
            print("✓ Decision enum values correct")
        else:
            print(f"✗ Decision enum mismatch. Expected: {expected_decisions}, Got: {actual_decisions}")
            return False
        
        # Test Status enum
        expected_statuses = {'pending', 'approved', 'rejected'}
        actual_statuses = {status.value for status in Status}
        if expected_statuses == actual_statuses:
            print("✓ Status enum values correct")
        else:
            print(f"✗ Status enum mismatch. Expected: {expected_statuses}, Got: {actual_statuses}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Enum test failed: {e}")
        return False

def test_model_structure():
    """Test that models have required attributes"""
    print("\nTesting model structure...")
    
    try:
        from app.models.planning import PlanningVersion, PlanningDataSource, PlanningAttribute, PlanningPDEMapping
        
        # Test PlanningVersion has required fields
        version_fields = {'version_id', 'phase_id', 'version_number', 'version_status'}
        actual_version_fields = set(PlanningVersion.__table__.columns.keys())
        if version_fields.issubset(actual_version_fields):
            print("✓ PlanningVersion has required fields")
        else:
            missing = version_fields - actual_version_fields
            print(f"✗ PlanningVersion missing fields: {missing}")
            return False
        
        # Test PlanningDataSource has required fields
        data_source_fields = {'data_source_id', 'version_id', 'source_name', 'source_type'}
        actual_data_source_fields = set(PlanningDataSource.__table__.columns.keys())
        if data_source_fields.issubset(actual_data_source_fields):
            print("✓ PlanningDataSource has required fields")
        else:
            missing = data_source_fields - actual_data_source_fields
            print(f"✗ PlanningDataSource missing fields: {missing}")
            return False
        
        # Test PlanningAttribute has required fields
        attribute_fields = {'attribute_id', 'version_id', 'attribute_name', 'data_type'}
        actual_attribute_fields = set(PlanningAttribute.__table__.columns.keys())
        if attribute_fields.issubset(actual_attribute_fields):
            print("✓ PlanningAttribute has required fields")
        else:
            missing = attribute_fields - actual_attribute_fields
            print(f"✗ PlanningAttribute missing fields: {missing}")
            return False
        
        # Test PlanningPDEMapping has required fields
        pde_mapping_fields = {'pde_mapping_id', 'version_id', 'attribute_id', 'data_source_id', 'pde_code'}
        actual_pde_mapping_fields = set(PlanningPDEMapping.__table__.columns.keys())
        if pde_mapping_fields.issubset(actual_pde_mapping_fields):
            print("✓ PlanningPDEMapping has required fields")
        else:
            missing = pde_mapping_fields - actual_pde_mapping_fields
            print(f"✗ PlanningPDEMapping missing fields: {missing}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Model structure test failed: {e}")
        return False

def test_api_router_structure():
    """Test that API router has expected endpoints"""
    print("\nTesting API router structure...")
    
    try:
        from app.api.v1.endpoints.planning_unified import router
        
        # Count routes
        routes = router.routes
        route_count = len(routes)
        print(f"✓ Planning API router has {route_count} routes")
        
        # Check for key endpoint patterns
        route_paths = [route.path for route in routes]
        expected_patterns = [
            '/versions',
            '/versions/{version_id}',
            '/versions/{version_id}/data-sources',
            '/versions/{version_id}/attributes',
            '/bulk-decision',
            '/health'
        ]
        
        found_patterns = []
        for pattern in expected_patterns:
            if any(pattern in path for path in route_paths):
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 4:  # Most key patterns found
            print(f"✓ Found {len(found_patterns)} expected endpoint patterns")
        else:
            print(f"✗ Only found {len(found_patterns)} out of {len(expected_patterns)} expected patterns")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ API router test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("UNIFIED PLANNING SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        test_planning_imports,
        test_enum_values,
        test_model_structure,
        test_api_router_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The unified planning system is ready.")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)