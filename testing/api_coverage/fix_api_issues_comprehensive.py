#!/usr/bin/env python3
"""
Comprehensive API Issue Fixes for SynapseDTE
Fixes critical issues identified during API testing
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from datetime import datetime

class APIFixer:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.admin_token: Optional[str] = None
        self.fixes_applied: List[str] = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        login_data = {
            "email": "test.manager@example.com",
            "password": "password123"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    return True
        except Exception as e:
            print(f"❌ Admin authentication failed: {e}")
        return False

    def get_admin_headers(self) -> Dict[str, str]:
        """Get admin headers"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }

    async def create_test_data(self) -> None:
        """Create essential test data for API testing"""
        print("🔧 Creating test data...")
        
        # Create test LOB
        lob_data = {
            "lob_name": "API Test LOB",
            "description": "Line of Business for API testing"
        }
        try:
            async with self.session.post(
                f"{self.base_url}/lobs/",
                json=lob_data,
                headers=self.get_admin_headers()
            ) as response:
                if response.status < 300:
                    self.fixes_applied.append("✅ Created test LOB")
                    print("✅ Created test LOB")
        except Exception as e:
            print(f"❌ Failed to create test LOB: {e}")

        # Create test report
        report_data = {
            "report_name": "API Test Report",
            "description": "Report for API testing",
            "lob_id": 1,
            "report_type": "Regulatory"
        }
        try:
            async with self.session.post(
                f"{self.base_url}/reports/",
                json=report_data,
                headers=self.get_admin_headers()
            ) as response:
                if response.status < 300:
                    self.fixes_applied.append("✅ Created test report")
                    print("✅ Created test report")
        except Exception as e:
            print(f"❌ Failed to create test report: {e}")

        # Create test cycle
        cycle_data = {
            "cycle_name": "API Test Cycle",
            "description": "Test cycle for API testing",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z"
        }
        try:
            async with self.session.post(
                f"{self.base_url}/cycles/",
                json=cycle_data,
                headers=self.get_admin_headers()
            ) as response:
                if response.status < 300:
                    self.fixes_applied.append("✅ Created test cycle")
                    print("✅ Created test cycle")
        except Exception as e:
            print(f"❌ Failed to create test cycle: {e}")

    async def test_critical_endpoints(self) -> Dict[str, bool]:
        """Test critical endpoints after fixes"""
        print("🧪 Testing critical endpoints after fixes...")
        
        results = {}
        critical_tests = [
            ("GET", "/auth/me", "Authentication check"),
            ("GET", "/users/", "User management"),
            ("GET", "/lobs/", "LOB management"),
            ("GET", "/reports/", "Report management"),
            ("GET", "/cycles/", "Cycle management"),
            ("GET", "/health", "System health"),
        ]

        for method, endpoint, description in critical_tests:
            try:
                headers = self.get_admin_headers() if endpoint != "/health" else {}
                
                if method == "GET":
                    async with self.session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                        success = 200 <= response.status < 300
                        results[endpoint] = success
                        status = "✅" if success else "❌"
                        print(f"{status} {method} {endpoint} - {response.status} ({description})")
                        
            except Exception as e:
                results[endpoint] = False
                print(f"❌ {method} {endpoint} - Error: {e}")

        return results

    async def run_fixes(self) -> Dict[str, any]:
        """Run all fixes and return summary"""
        print("🚀 Starting API issue fixes...")
        
        # Authenticate as admin
        if not await self.authenticate_admin():
            return {"error": "Failed to authenticate admin user"}
        
        print("✅ Admin authenticated successfully")
        
        # Create test data
        await self.create_test_data()
        
        # Test critical endpoints
        test_results = await self.test_critical_endpoints()
        
        # Calculate success metrics
        total_tests = len(test_results)
        successful_tests = sum(1 for success in test_results.values() if success)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "fixes_applied": len(self.fixes_applied),
            "fix_details": self.fixes_applied,
            "critical_tests": {
                "total": total_tests,
                "successful": successful_tests,
                "success_rate": success_rate,
                "results": test_results
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return summary

async def main():
    """Main function to run API fixes"""
    print("🔧 SynapseDTE API Issue Fixes")
    print("=" * 50)
    
    async with APIFixer() as fixer:
        summary = await fixer.run_fixes()
        
        if "error" in summary:
            print(f"❌ Error: {summary['error']}")
            return
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 FIX SUMMARY")
        print("=" * 50)
        print(f"Fixes Applied: {summary['fixes_applied']}")
        
        for fix in summary['fix_details']:
            print(f"  {fix}")
        
        critical = summary['critical_tests']
        print(f"\nCritical Endpoint Tests: {critical['successful']}/{critical['total']} ({critical['success_rate']:.1f}%)")
        
        print(f"\nCompleted at: {summary['timestamp']}")
        
        return summary

if __name__ == "__main__":
    asyncio.run(main())