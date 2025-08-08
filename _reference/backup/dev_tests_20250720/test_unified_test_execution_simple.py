#!/usr/bin/env python3
"""
Simple test script for the unified test execution implementation.
Tests file structure and basic syntax without requiring dependencies.
"""

import os
import sys
import ast
from typing import Dict, Any, List

def test_file_structure():
    """Test that all required files exist."""
    print("Testing file structure...")
    
    required_files = [
        # Database models
        "app/models/test_execution.py",
        "app/models/test_execution_legacy.py",
        
        # Schemas
        "app/schemas/test_execution.py",
        
        # Services
        "app/services/test_execution_service.py",
        
        # API endpoints
        "app/api/v1/endpoints/test_execution.py",
        
        # Frontend components
        "frontend/src/components/test-execution/UnifiedTestExecutionManager.tsx",
        "frontend/src/pages/phases/TestExecutionPage.tsx",
        
        # Migration files
        "alembic/versions/2025_07_18_unified_test_execution_architecture.py",
        "alembic/versions/2025_07_18_cleanup_legacy_test_execution.py",
        
        # Configuration files
        "app/models/__init__.py",
        "app/api/v1/api.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ Found: {file_path}")
        else:
            print(f"✗ Missing: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n✗ Missing {len(missing_files)} files")
        return False
    else:
        print(f"\n✓ All {len(required_files)} files found")
        return True


def test_python_syntax():
    """Test that all Python files have valid syntax."""
    print("\nTesting Python syntax...")
    
    python_files = [
        "app/models/test_execution.py",
        "app/models/test_execution_legacy.py",
        "app/schemas/test_execution.py",
        "app/services/test_execution_service.py",
        "app/api/v1/endpoints/test_execution.py",
        "alembic/versions/2025_07_18_unified_test_execution_architecture.py",
        "alembic/versions/2025_07_18_cleanup_legacy_test_execution.py",
    ]
    
    syntax_errors = []
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                ast.parse(content)
                print(f"✓ Valid syntax: {file_path}")
            except SyntaxError as e:
                print(f"✗ Syntax error in {file_path}: {e}")
                syntax_errors.append(file_path)
        else:
            print(f"✗ File not found: {file_path}")
            syntax_errors.append(file_path)
    
    if syntax_errors:
        print(f"\n✗ Syntax errors in {len(syntax_errors)} files")
        return False
    else:
        print(f"\n✓ All {len(python_files)} Python files have valid syntax")
        return True


def test_model_definitions():
    """Test that model files contain required class definitions."""
    print("\nTesting model definitions...")
    
    model_file = "app/models/test_execution_unified.py"
    if not os.path.exists(model_file):
        print(f"✗ Model file not found: {model_file}")
        return False
    
    with open(model_file, 'r') as f:
        content = f.read()
    
    required_classes = [
        "TestExecutionResult",
        "TestExecutionReview", 
        "TestExecutionAudit"
    ]
    
    missing_classes = []
    for class_name in required_classes:
        if f"class {class_name}" in content:
            print(f"✓ Found class: {class_name}")
        else:
            print(f"✗ Missing class: {class_name}")
            missing_classes.append(class_name)
    
    if missing_classes:
        print(f"\n✗ Missing {len(missing_classes)} classes")
        return False
    else:
        print(f"\n✓ All {len(required_classes)} classes found")
        return True


def test_schema_definitions():
    """Test that schema files contain required schema definitions."""
    print("\nTesting schema definitions...")
    
    schema_file = "app/schemas/test_execution_unified.py"
    if not os.path.exists(schema_file):
        print(f"✗ Schema file not found: {schema_file}")
        return False
    
    with open(schema_file, 'r') as f:
        content = f.read()
    
    required_schemas = [
        "TestExecutionCreateRequest",
        "TestExecutionResponse",
        "TestExecutionReviewRequest",
        "BulkTestExecutionRequest",
        "TestExecutionDashboardResponse"
    ]
    
    missing_schemas = []
    for schema_name in required_schemas:
        if f"class {schema_name}" in content:
            print(f"✓ Found schema: {schema_name}")
        else:
            print(f"✗ Missing schema: {schema_name}")
            missing_schemas.append(schema_name)
    
    if missing_schemas:
        print(f"\n✗ Missing {len(missing_schemas)} schemas")
        return False
    else:
        print(f"\n✓ All {len(required_schemas)} schemas found")
        return True


def test_service_definitions():
    """Test that service files contain required service definitions."""
    print("\nTesting service definitions...")
    
    service_file = "app/services/test_execution_service_unified.py"
    if not os.path.exists(service_file):
        print(f"✗ Service file not found: {service_file}")
        return False
    
    with open(service_file, 'r') as f:
        content = f.read()
    
    required_methods = [
        "create_test_execution",
        "create_test_execution_review",
        "get_test_execution_dashboard",
        "check_phase_completion"
    ]
    
    missing_methods = []
    for method_name in required_methods:
        if f"def {method_name}" in content:
            print(f"✓ Found method: {method_name}")
        else:
            print(f"✗ Missing method: {method_name}")
            missing_methods.append(method_name)
    
    if missing_methods:
        print(f"\n✗ Missing {len(missing_methods)} methods")
        return False
    else:
        print(f"\n✓ All {len(required_methods)} methods found")
        return True


def test_api_endpoints():
    """Test that API endpoint files contain required endpoints."""
    print("\nTesting API endpoints...")
    
    api_file = "app/api/v1/endpoints/test_execution_unified.py"
    if not os.path.exists(api_file):
        print(f"✗ API file not found: {api_file}")
        return False
    
    with open(api_file, 'r') as f:
        content = f.read()
    
    required_endpoints = [
        "/test-execution/{cycle_id}/reports/{report_id}/execute",
        "/test-execution/test-cases/{test_case_id}/execute",
        "/test-execution/{cycle_id}/reports/{report_id}/pending-review",
        "/test-execution/executions/{execution_id}/review",
        "/test-execution/{cycle_id}/reports/{report_id}/dashboard",
        "/test-execution/configuration"
    ]
    
    missing_endpoints = []
    for endpoint in required_endpoints:
        if endpoint in content:
            print(f"✓ Found endpoint: {endpoint}")
        else:
            print(f"✗ Missing endpoint: {endpoint}")
            missing_endpoints.append(endpoint)
    
    if missing_endpoints:
        print(f"\n✗ Missing {len(missing_endpoints)} endpoints")
        return False
    else:
        print(f"\n✓ All {len(required_endpoints)} endpoints found")
        return True


def test_frontend_components():
    """Test that frontend components exist and have basic structure."""
    print("\nTesting frontend components...")
    
    # Test main component
    main_component = "frontend/src/components/test-execution/UnifiedTestExecutionManager.tsx"
    if not os.path.exists(main_component):
        print(f"✗ Main component not found: {main_component}")
        return False
    
    with open(main_component, 'r') as f:
        content = f.read()
    
    required_elements = [
        "UnifiedTestExecutionManager",
        "apiClient",
        "useQuery",
        "useMutation",
        "TestExecutionDashboard"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element in content:
            print(f"✓ Found element: {element}")
        else:
            print(f"✗ Missing element: {element}")
            missing_elements.append(element)
    
    # Test page integration
    page_component = "frontend/src/pages/phases/TestExecutionPage.tsx"
    if os.path.exists(page_component):
        with open(page_component, 'r') as f:
            page_content = f.read()
        
        if "UnifiedTestExecutionManager" in page_content:
            print("✓ Page integration found")
        else:
            print("✗ Page integration missing")
            missing_elements.append("Page integration")
    else:
        print("✗ Page component not found")
        missing_elements.append("Page component")
    
    if missing_elements:
        print(f"\n✗ Missing {len(missing_elements)} frontend elements")
        return False
    else:
        print(f"\n✓ All {len(required_elements)} frontend elements found")
        return True


def test_migration_structure():
    """Test that migration files have proper structure."""
    print("\nTesting migration structure...")
    
    migration_files = [
        "alembic/versions/2025_07_18_unified_test_execution_architecture.py",
        "alembic/versions/2025_07_18_cleanup_legacy_test_execution.py"
    ]
    
    errors = []
    for migration_file in migration_files:
        if not os.path.exists(migration_file):
            print(f"✗ Migration file not found: {migration_file}")
            errors.append(migration_file)
            continue
        
        with open(migration_file, 'r') as f:
            content = f.read()
        
        required_elements = [
            "def upgrade():",
            "def downgrade():",
            "revision =",
            "down_revision ="
        ]
        
        file_errors = []
        for element in required_elements:
            if element in content:
                print(f"✓ Found in {migration_file}: {element}")
            else:
                print(f"✗ Missing in {migration_file}: {element}")
                file_errors.append(element)
        
        if file_errors:
            errors.extend(file_errors)
    
    if errors:
        print(f"\n✗ Migration structure errors: {len(errors)}")
        return False
    else:
        print(f"\n✓ All migration files have proper structure")
        return True


def test_configuration_updates():
    """Test that configuration files have been updated."""
    print("\nTesting configuration updates...")
    
    # Test models __init__.py
    models_init = "app/models/__init__.py"
    if os.path.exists(models_init):
        with open(models_init, 'r') as f:
            content = f.read()
        
        if "test_execution" in content and "TestExecutionResult" in content:
            print("✓ Models __init__.py updated")
        else:
            print("✗ Models __init__.py not updated")
            return False
    else:
        print("✗ Models __init__.py not found")
        return False
    
    # Test API router
    api_router = "app/api/v1/api.py"
    if os.path.exists(api_router):
        with open(api_router, 'r') as f:
            content = f.read()
        
        if "test_execution" in content:
            print("✓ API router updated")
        else:
            print("✗ API router not updated")
            return False
    else:
        print("✗ API router not found")
        return False
    
    print("\n✓ All configuration files updated")
    return True


def main():
    """Run all tests."""
    print("🧪 Running Unified Test Execution Implementation Tests")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Syntax", test_python_syntax),
        ("Model Definitions", test_model_definitions),
        ("Schema Definitions", test_schema_definitions),
        ("Service Definitions", test_service_definitions),
        ("API Endpoints", test_api_endpoints),
        ("Frontend Components", test_frontend_components),
        ("Migration Structure", test_migration_structure),
        ("Configuration Updates", test_configuration_updates),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("""
🎉 ALL TESTS PASSED! 🎉

The unified test execution implementation is structurally complete and ready.

✅ Database models and migrations created
✅ Pydantic schemas defined
✅ Service layer implemented
✅ API endpoints created
✅ Frontend components built
✅ Legacy models cleaned up
✅ Configuration files updated

Next steps:
1. Run database migrations
2. Test API endpoints
3. Verify frontend functionality
4. End-to-end testing
""")
        return 0
    else:
        print(f"""
⚠️  {total - passed} test(s) failed.
Please review the failed tests and fix the issues.
""")
        return 1


if __name__ == "__main__":
    sys.exit(main())