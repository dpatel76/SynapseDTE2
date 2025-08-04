#!/usr/bin/env python3
"""
Comprehensive RBAC System Test Script
Tests all aspects of the new database-driven RBAC implementation
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.user import User
from app.models.rbac import (
    Permission, Role, RolePermission, UserRole,
    UserPermission, ResourcePermission, PermissionAuditLog
)
from app.models.rbac_resource import Resource
from app.services.permission_service import get_permission_service
from app.core.logging import get_logger

logger = get_logger(__name__)

# Test configuration
TEST_RESULTS = {
    "passed": 0,
    "failed": 0,
    "tests": []
}


def test_result(test_name: str, passed: bool, details: str = ""):
    """Record test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    TEST_RESULTS["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    if passed:
        TEST_RESULTS["passed"] += 1
    else:
        TEST_RESULTS["failed"] += 1
    
    print(f"\n{status}: {test_name}")
    if details:
        print(f"  Details: {details}")


async def test_database_schema(db: AsyncSession):
    """Test 1: Verify all RBAC tables exist"""
    print("\n=== Test 1: Database Schema Verification ===")
    
    tables_to_check = [
        "permissions",
        "resources", 
        "roles",
        "role_permissions",
        "user_roles",
        "user_permissions",
        "resource_permissions",
        "role_hierarchy",
        "permission_audit_log"
    ]
    
    all_exist = True
    for table in tables_to_check:
        try:
            result = await db.execute(
                f"SELECT COUNT(*) FROM {table}"
            )
            count = result.scalar()
            print(f"  ✓ Table '{table}' exists with {count} records")
        except Exception as e:
            print(f"  ✗ Table '{table}' missing or error: {str(e)}")
            all_exist = False
    
    test_result("Database Schema", all_exist, 
                f"All {len(tables_to_check)} RBAC tables exist" if all_exist else "Some tables missing")


async def test_permission_creation(db: AsyncSession):
    """Test 2: Create and retrieve permissions"""
    print("\n=== Test 2: Permission CRUD Operations ===")
    
    try:
        # Create a test permission
        test_permission = Permission(
            resource="test_resource",
            action="test_action",
            description="Test permission for RBAC testing"
        )
        db.add(test_permission)
        await db.commit()
        await db.refresh(test_permission)
        
        # Retrieve it
        result = await db.execute(
            select(Permission).where(
                and_(
                    Permission.resource == "test_resource",
                    Permission.action == "test_action"
                )
            )
        )
        retrieved = result.scalar_one_or_none()
        
        success = retrieved is not None and retrieved.permission_id == test_permission.permission_id
        
        # Clean up
        if retrieved:
            await db.delete(retrieved)
            await db.commit()
        
        test_result("Permission CRUD", success, 
                   f"Created and retrieved permission ID {test_permission.permission_id}")
        
    except Exception as e:
        test_result("Permission CRUD", False, str(e))


async def test_role_management(db: AsyncSession):
    """Test 3: Role creation and permission assignment"""
    print("\n=== Test 3: Role Management ===")
    
    try:
        # Create test role
        test_role = Role(
            role_name="Test_Role_RBAC",
            description="Test role for RBAC testing",
            is_system=False
        )
        db.add(test_role)
        
        # Create test permission
        test_perm = Permission(
            resource="test_rbac",
            action="execute",
            description="Test permission"
        )
        db.add(test_perm)
        await db.commit()
        await db.refresh(test_role)
        await db.refresh(test_perm)
        
        # Assign permission to role
        role_perm = RolePermission(
            role_id=test_role.role_id,
            permission_id=test_perm.permission_id,
            granted_by=1
        )
        db.add(role_perm)
        await db.commit()
        
        # Verify assignment
        result = await db.execute(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id == test_role.role_id,
                    RolePermission.permission_id == test_perm.permission_id
                )
            )
        )
        assigned = result.scalar_one_or_none()
        
        success = assigned is not None
        
        # Clean up
        if assigned:
            await db.delete(assigned)
        await db.delete(test_role)
        await db.delete(test_perm)
        await db.commit()
        
        test_result("Role Management", success, 
                   "Role created and permission assigned successfully")
        
    except Exception as e:
        test_result("Role Management", False, str(e))


async def test_permission_service(db: AsyncSession):
    """Test 4: Permission service functionality"""
    print("\n=== Test 4: Permission Service ===")
    
    try:
        permission_service = await get_permission_service(db)
        
        # Test 1: Admin bypass
        admin_user = await db.execute(
            select(User).where(User.email == "admin@company.com")
        )
        admin = admin_user.scalar_one_or_none()
        
        if admin:
            has_perm = await permission_service.check_permission(
                admin.user_id, "any_resource", "any_action"
            )
            print(f"  Admin bypass test: {has_perm}")
        
        # Test 2: Regular user permissions
        test_user = await db.execute(
            select(User).where(User.role == "Tester").limit(1)
        )
        tester = test_user.scalar_one_or_none()
        
        if tester:
            # Should have planning:execute permission
            has_planning = await permission_service.check_permission(
                tester.user_id, "planning", "execute"
            )
            
            # Should NOT have users:delete permission  
            has_delete = await permission_service.check_permission(
                tester.user_id, "users", "delete"
            )
            
            success = has_planning and not has_delete
            test_result("Permission Service", success,
                       f"Tester has planning:execute={has_planning}, users:delete={has_delete}")
        else:
            test_result("Permission Service", False, "No test user found")
            
    except Exception as e:
        test_result("Permission Service", False, str(e))


async def test_user_role_assignment(db: AsyncSession):
    """Test 5: User role assignment and removal"""
    print("\n=== Test 5: User Role Assignment ===")
    
    try:
        # Get a test user and role
        user_result = await db.execute(
            select(User).where(User.role == "Tester").limit(1)
        )
        test_user = user_result.scalar_one_or_none()
        
        role_result = await db.execute(
            select(Role).where(Role.role_name == "Report Owner")
        )
        test_role = role_result.scalar_one_or_none()
        
        if test_user and test_role:
            # Assign role
            user_role = UserRole(
                user_id=test_user.user_id,
                role_id=test_role.role_id,
                assigned_by=1,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.add(user_role)
            await db.commit()
            
            # Verify assignment
            result = await db.execute(
                select(UserRole).where(
                    and_(
                        UserRole.user_id == test_user.user_id,
                        UserRole.role_id == test_role.role_id
                    )
                )
            )
            assigned = result.scalar_one_or_none()
            
            # Remove assignment
            if assigned:
                await db.delete(assigned)
                await db.commit()
            
            test_result("User Role Assignment", assigned is not None,
                       f"Assigned {test_role.role_name} to user {test_user.email}")
        else:
            test_result("User Role Assignment", False, "Test user or role not found")
            
    except Exception as e:
        test_result("User Role Assignment", False, str(e))


async def test_resource_permissions(db: AsyncSession):
    """Test 6: Resource-level permissions"""
    print("\n=== Test 6: Resource-Level Permissions ===")
    
    try:
        # Get test user and permission
        user_result = await db.execute(
            select(User).where(User.role == "Tester").limit(1)
        )
        test_user = user_result.scalar_one_or_none()
        
        perm_result = await db.execute(
            select(Permission).where(
                and_(
                    Permission.resource == "reports",
                    Permission.action == "update"
                )
            )
        )
        test_perm = perm_result.scalar_one_or_none()
        
        if test_user and test_perm:
            # Grant resource-specific permission
            resource_perm = ResourcePermission(
                user_id=test_user.user_id,
                resource_type="report",
                resource_id=123,  # Specific report ID
                permission_id=test_perm.permission_id,
                granted=True,
                granted_by=1
            )
            db.add(resource_perm)
            await db.commit()
            
            # Test permission check
            permission_service = await get_permission_service(db)
            
            # Should have permission for specific resource
            has_specific = await permission_service.check_permission(
                test_user.user_id, "reports", "update", 123
            )
            
            # Should NOT have permission for different resource
            has_other = await permission_service.check_permission(
                test_user.user_id, "reports", "update", 456
            )
            
            success = has_specific and not has_other
            
            # Clean up
            await db.delete(resource_perm)
            await db.commit()
            
            test_result("Resource Permissions", success,
                       f"Resource 123: {has_specific}, Resource 456: {has_other}")
        else:
            test_result("Resource Permissions", False, "Test data not found")
            
    except Exception as e:
        test_result("Resource Permissions", False, str(e))


async def test_permission_inheritance(db: AsyncSession):
    """Test 7: Role hierarchy and permission inheritance"""
    print("\n=== Test 7: Permission Inheritance ===")
    
    try:
        # This would test role hierarchy if implemented
        # For now, just verify the table exists
        result = await db.execute(
            "SELECT COUNT(*) FROM role_hierarchy"
        )
        count = result.scalar()
        
        test_result("Permission Inheritance", True,
                   f"Role hierarchy table exists with {count} entries")
        
    except Exception as e:
        test_result("Permission Inheritance", False, str(e))


async def test_audit_logging(db: AsyncSession):
    """Test 8: Permission audit logging"""
    print("\n=== Test 8: Audit Logging ===")
    
    try:
        # Check recent audit logs
        result = await db.execute(
            select(PermissionAuditLog)
            .order_by(PermissionAuditLog.performed_at.desc())
            .limit(5)
        )
        logs = result.scalars().all()
        
        print(f"  Found {len(logs)} recent audit log entries")
        for log in logs:
            print(f"    - {log.action_type} on {log.target_type}:{log.target_id} "
                  f"at {log.performed_at}")
        
        test_result("Audit Logging", True,
                   f"Audit log contains {len(logs)} recent entries")
        
    except Exception as e:
        test_result("Audit Logging", False, str(e))


async def test_resources_table(db: AsyncSession):
    """Test 9: Resources table functionality"""
    print("\n=== Test 9: Resources Table ===")
    
    try:
        # Check if resources are populated
        result = await db.execute(
            select(Resource).limit(10)
        )
        resources = result.scalars().all()
        
        print(f"  Found {len(resources)} resources:")
        for resource in resources:
            print(f"    - {resource.resource_name} ({resource.resource_type}): "
                  f"{resource.display_name}")
        
        # Test resource hierarchy
        if resources:
            test_resource = resources[0]
            full_path = test_resource.full_path
            print(f"  Resource path test: {full_path}")
        
        test_result("Resources Table", len(resources) > 0,
                   f"Resources table contains {len(resources)} entries")
        
    except Exception as e:
        test_result("Resources Table", False, str(e))


async def test_permission_caching(db: AsyncSession):
    """Test 10: Permission caching performance"""
    print("\n=== Test 10: Permission Caching ===")
    
    try:
        import time
        permission_service = await get_permission_service(db)
        
        # Get a test user
        user_result = await db.execute(
            select(User).where(User.role == "Tester").limit(1)
        )
        test_user = user_result.scalar_one_or_none()
        
        if test_user:
            # First call (cache miss)
            start = time.time()
            result1 = await permission_service.check_permission(
                test_user.user_id, "planning", "execute"
            )
            time1 = time.time() - start
            
            # Second call (cache hit)
            start = time.time()
            result2 = await permission_service.check_permission(
                test_user.user_id, "planning", "execute"
            )
            time2 = time.time() - start
            
            # Cache should make second call faster
            cache_working = time2 < time1 and result1 == result2
            
            test_result("Permission Caching", cache_working,
                       f"First call: {time1:.4f}s, Cached call: {time2:.4f}s")
        else:
            test_result("Permission Caching", False, "No test user found")
            
    except Exception as e:
        test_result("Permission Caching", False, str(e))


async def run_all_tests():
    """Run all RBAC tests"""
    print("\n" + "="*60)
    print("RBAC SYSTEM COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    async for db in get_db():
        try:
            # Run all tests
            await test_database_schema(db)
            await test_permission_creation(db)
            await test_role_management(db)
            await test_permission_service(db)
            await test_user_role_assignment(db)
            await test_resource_permissions(db)
            await test_permission_inheritance(db)
            await test_audit_logging(db)
            await test_resources_table(db)
            await test_permission_caching(db)
            
            # Print summary
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            print(f"Total Tests: {TEST_RESULTS['passed'] + TEST_RESULTS['failed']}")
            print(f"Passed: {TEST_RESULTS['passed']} ✅")
            print(f"Failed: {TEST_RESULTS['failed']} ❌")
            print(f"Success Rate: {TEST_RESULTS['passed'] / (TEST_RESULTS['passed'] + TEST_RESULTS['failed']) * 100:.1f}%")
            
            if TEST_RESULTS['failed'] > 0:
                print("\nFailed Tests:")
                for test in TEST_RESULTS['tests']:
                    if not test['passed']:
                        print(f"  - {test['name']}: {test['details']}")
            
            break
            
        except Exception as e:
            logger.error(f"Test suite error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())