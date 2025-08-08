#!/usr/bin/env python3
"""
Comprehensive RBAC Permission Testing Script

This script tests all RBAC permissions for each role to ensure the system is working correctly.
It includes both positive tests (permissions that should be granted) and negative tests 
(permissions that should be denied).
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models import User, Role, Permission, UserRole, RolePermission
from app.core.rbac_config import RESOURCES, DEFAULT_ROLE_PERMISSIONS
from app.services.permission_service import PermissionService
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    user_email: str
    user_role: str
    resource: str
    action: str
    expected: bool
    actual: bool
    passed: bool
    error: str = None

class RBACTester:
    """Comprehensive RBAC permission tester"""
    
    def __init__(self):
        self.session = None
        self.permission_service = None
        self.test_results: List[TestResult] = []
        
    async def get_session(self):
        """Get async database session"""
        if not self.session:
            self.session = AsyncSessionLocal()
        return self.session
    
    async def close_session(self):
        """Close database session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_permission_service(self):
        """Get permission service instance"""
        if not self.permission_service:
            session = await self.get_session()
            self.permission_service = PermissionService(session)
        return self.permission_service
    
    async def get_all_users(self) -> List[User]:
        """Get all users from database"""
        session = await self.get_session()
        from sqlalchemy import select
        result = await session.execute(select(User))
        return result.scalars().all()
    
    async def get_all_permissions(self) -> List[Permission]:
        """Get all permissions from database"""
        session = await self.get_session()
        from sqlalchemy import select
        result = await session.execute(select(Permission))
        return result.scalars().all()
    
    def get_expected_permissions_for_role(self, role_name: str) -> List[str]:
        """Get expected permissions for a role based on configuration"""
        if role_name not in DEFAULT_ROLE_PERMISSIONS:
            return []
        
        permissions = []
        role_perms = DEFAULT_ROLE_PERMISSIONS[role_name]
        
        for perm_string in role_perms:
            if perm_string == "*:*":
                # Admin gets all permissions
                for resource, config in RESOURCES.items():
                    for action in config["actions"]:
                        permissions.append(f"{resource}:{action.value}")
            else:
                permissions.append(perm_string)
        
        return permissions
    
    async def test_user_permission(self, user: User, resource: str, action: str, expected: bool) -> TestResult:
        """Test a specific permission for a user"""
        try:
            permission_service = await self.get_permission_service()
            
            # Test the permission using the correct method name
            actual = await permission_service.check_permission(
                user_id=user.user_id,
                resource=resource,
                action=action
            )
            
            passed = (actual == expected)
            
            result = TestResult(
                user_email=user.email,
                user_role=user.role,
                resource=resource,
                action=action,
                expected=expected,
                actual=actual,
                passed=passed
            )
            
            if passed:
                logger.debug(f"✅ {user.email} ({user.role}) - {resource}:{action} = {actual} (expected {expected})")
            else:
                logger.warning(f"❌ {user.email} ({user.role}) - {resource}:{action} = {actual} (expected {expected})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing {user.email} - {resource}:{action}: {e}")
            return TestResult(
                user_email=user.email,
                user_role=user.role,
                resource=resource,
                action=action,
                expected=expected,
                actual=False,
                passed=False,
                error=str(e)
            )
    
    async def test_all_permissions_for_user(self, user: User) -> List[TestResult]:
        """Test all permissions for a specific user"""
        logger.info(f"Testing permissions for {user.email} ({user.role})")
        
        results = []
        expected_permissions = self.get_expected_permissions_for_role(user.role)
        all_permissions = await self.get_all_permissions()
        
        for permission in all_permissions:
            perm_string = f"{permission.resource}:{permission.action}"
            expected = perm_string in expected_permissions
            
            result = await self.test_user_permission(
                user=user,
                resource=permission.resource,
                action=permission.action,
                expected=expected
            )
            results.append(result)
        
        return results
    
    async def test_all_users_and_permissions(self) -> List[TestResult]:
        """Test all permissions for all users"""
        logger.info("Starting comprehensive RBAC permission testing...")
        
        users = await self.get_all_users()
        all_results = []
        
        for user in users:
            user_results = await self.test_all_permissions_for_user(user)
            all_results.extend(user_results)
        
        self.test_results = all_results
        return all_results
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # Group by user
        user_stats = {}
        for result in self.test_results:
            if result.user_email not in user_stats:
                user_stats[result.user_email] = {
                    "role": result.user_role,
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "failures": []
                }
            
            user_stats[result.user_email]["total"] += 1
            if result.passed:
                user_stats[result.user_email]["passed"] += 1
            else:
                user_stats[result.user_email]["failed"] += 1
                user_stats[result.user_email]["failures"].append({
                    "resource": result.resource,
                    "action": result.action,
                    "expected": result.expected,
                    "actual": result.actual,
                    "error": result.error
                })
        
        # Group by role
        role_stats = {}
        for result in self.test_results:
            if result.user_role not in role_stats:
                role_stats[result.user_role] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "users": set()
                }
            
            role_stats[result.user_role]["total"] += 1
            role_stats[result.user_role]["users"].add(result.user_email)
            if result.passed:
                role_stats[result.user_role]["passed"] += 1
            else:
                role_stats[result.user_role]["failed"] += 1
        
        # Convert sets to lists for JSON serialization
        for role in role_stats:
            role_stats[role]["users"] = list(role_stats[role]["users"])
        
        # Find critical failures (permissions that should work but don't)
        critical_failures = [
            r for r in self.test_results 
            if not r.passed and r.expected and not r.error
        ]
        
        # Find unexpected permissions (permissions that work but shouldn't)
        unexpected_permissions = [
            r for r in self.test_results 
            if not r.passed and not r.expected and r.actual
        ]
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
            },
            "user_statistics": user_stats,
            "role_statistics": role_stats,
            "critical_failures": [
                {
                    "user": r.user_email,
                    "role": r.user_role,
                    "permission": f"{r.resource}:{r.action}",
                    "error": r.error
                }
                for r in critical_failures
            ],
            "unexpected_permissions": [
                {
                    "user": r.user_email,
                    "role": r.user_role,
                    "permission": f"{r.resource}:{r.action}"
                }
                for r in unexpected_permissions
            ]
        }
        
        return report
    
    def print_summary_report(self, report: Dict[str, Any]):
        """Print a human-readable summary report"""
        print("\n" + "=" * 80)
        print("RBAC PERMISSION TEST SUMMARY")
        print("=" * 80)
        
        summary = report["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']}%")
        
        print("\n" + "-" * 40)
        print("ROLE STATISTICS")
        print("-" * 40)
        
        for role, stats in report["role_statistics"].items():
            success_rate = round((stats['passed'] / stats['total']) * 100, 2) if stats['total'] > 0 else 0
            print(f"{role}:")
            print(f"  Users: {len(stats['users'])}")
            print(f"  Tests: {stats['total']} (Passed: {stats['passed']}, Failed: {stats['failed']})")
            print(f"  Success Rate: {success_rate}%")
        
        if report["critical_failures"]:
            print("\n" + "-" * 40)
            print("CRITICAL FAILURES (Expected permissions not working)")
            print("-" * 40)
            for failure in report["critical_failures"]:
                print(f"❌ {failure['user']} ({failure['role']}) - {failure['permission']}")
                if failure['error']:
                    print(f"   Error: {failure['error']}")
        
        if report["unexpected_permissions"]:
            print("\n" + "-" * 40)
            print("UNEXPECTED PERMISSIONS (Permissions working when they shouldn't)")
            print("-" * 40)
            for perm in report["unexpected_permissions"]:
                print(f"⚠️  {perm['user']} ({perm['role']}) - {perm['permission']}")
        
        print("\n" + "=" * 80)
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive RBAC testing and return report"""
        try:
            logger.info("Starting comprehensive RBAC permission testing...")
            
            # Run all tests
            await self.test_all_users_and_permissions()
            
            # Generate report
            report = self.generate_test_report()
            
            # Print summary
            self.print_summary_report(report)
            
            logger.info("RBAC testing completed successfully!")
            return report
            
        except Exception as e:
            logger.error(f"RBAC testing failed: {e}")
            raise
        finally:
            await self.close_session()


async def main():
    """Main entry point"""
    print("=" * 80)
    print("COMPREHENSIVE RBAC PERMISSION TESTING")
    print("=" * 80)
    
    try:
        tester = RBACTester()
        report = await tester.run_comprehensive_test()
        
        # Save detailed report to file
        report_file = f"rbac_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Return success/failure based on results
        if report["summary"]["failed_tests"] == 0:
            print("\n✅ All RBAC permission tests passed!")
            return 0
        else:
            print(f"\n❌ {report['summary']['failed_tests']} RBAC permission tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 RBAC testing failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 