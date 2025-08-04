#!/usr/bin/env python3
"""
API Security Testing Script
Tests for API-specific vulnerabilities including injection, mass assignment, etc.
"""

import asyncio
import aiohttp
import json
import time
import random
import string
from typing import Dict, List, Any
from datetime import datetime
import xml.etree.ElementTree as ET

class APISecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.results = []
        self.session = None
        self.auth_token = None
        
    async def setup(self):
        """Setup test environment and get auth token"""
        self.session = aiohttp.ClientSession()
        
        # Try to login as admin for testing
        async with self.session.post(
            f"{self.api_base}/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data.get("access_token")
                print("✅ Authenticated successfully")
            else:
                print("⚠️  Could not authenticate, some tests may fail")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self):
        """Run all API security tests"""
        print("🔌 Starting API Security Tests")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Run tests
            await self.test_sql_injection()
            await self.test_nosql_injection()
            await self.test_xss_injection()
            await self.test_xxe_injection()
            await self.test_mass_assignment()
            await self.test_api_versioning()
            await self.test_cors_configuration()
            await self.test_http_methods()
            await self.test_content_type_validation()
            await self.test_api_dos()
            
        finally:
            await self.cleanup()
        
        # Generate report
        self.generate_report()
    
    async def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        print("\n🔍 Testing SQL Injection...")
        
        sql_payloads = [
            "' OR '1'='1",
            "1' UNION SELECT NULL--",
            "1'; DROP TABLE users--",
            "admin'--",
            "' OR 1=1--",
            "1' AND SLEEP(5)--",
            "' UNION SELECT password FROM users--"
        ]
        
        vulnerable_endpoints = []
        
        # Test various endpoints with SQL payloads
        test_endpoints = [
            ("/users", "GET", {"search": "PAYLOAD"}),
            ("/reports", "GET", {"filter": "PAYLOAD"}),
            ("/cycles", "GET", {"sort": "PAYLOAD"}),
            ("/users/1", "GET", {}),  # ID in URL
        ]
        
        for endpoint, method, params in test_endpoints:
            for payload in sql_payloads:
                # Replace PAYLOAD with actual payload
                test_params = {}
                for key, value in params.items():
                    test_params[key] = value.replace("PAYLOAD", payload) if value == "PAYLOAD" else value
                
                # Test ID in URL
                test_endpoint = endpoint.replace("1", payload) if "1" in endpoint else endpoint
                
                try:
                    headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
                    
                    if method == "GET":
                        async with self.session.get(
                            f"{self.api_base}{test_endpoint}",
                            params=test_params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            # Check for SQL error messages
                            text = await response.text()
                            sql_errors = [
                                "SQL syntax",
                                "mysql_fetch",
                                "PostgreSQL",
                                "warning: pg_",
                                "valid MySQL result",
                                "mssql_query",
                                "SQLAlchemy",
                                "psycopg2"
                            ]
                            
                            for error in sql_errors:
                                if error.lower() in text.lower():
                                    vulnerable_endpoints.append({
                                        "endpoint": endpoint,
                                        "payload": payload,
                                        "error": error
                                    })
                                    break
                            
                            # Check for delays (time-based SQLi)
                            if "SLEEP" in payload and response.status == 200:
                                # Would need to measure actual delay
                                pass
                
                except asyncio.TimeoutError:
                    # Timeout might indicate time-based SQLi
                    if "SLEEP" in payload:
                        vulnerable_endpoints.append({
                            "endpoint": endpoint,
                            "payload": payload,
                            "type": "time-based"
                        })
                except Exception as e:
                    pass
        
        if vulnerable_endpoints:
            self.results.append({
                "test": "SQL Injection",
                "status": "FAIL",
                "severity": "CRITICAL",
                "details": f"Found {len(vulnerable_endpoints)} potential SQL injection points",
                "vulnerable_endpoints": vulnerable_endpoints
            })
            print(f"   ❌ Found {len(vulnerable_endpoints)} potential SQL injection vulnerabilities")
        else:
            self.results.append({
                "test": "SQL Injection",
                "status": "PASS",
                "details": "No SQL injection vulnerabilities detected"
            })
            print("   ✅ No SQL injection vulnerabilities detected")
    
    async def test_nosql_injection(self):
        """Test for NoSQL injection (if applicable)"""
        print("\n🔍 Testing NoSQL Injection...")
        
        nosql_payloads = [
            {"$gt": ""},
            {"$ne": None},
            {"$where": "this.password.length > 0"},
            {"$regex": ".*"},
            {"password": {"$ne": "1"}}
        ]
        
        vulnerable_endpoints = []
        
        # Test login endpoint with NoSQL payloads
        for payload in nosql_payloads:
            try:
                async with self.session.post(
                    f"{self.api_base}/auth/login",
                    json={"email": payload, "password": "test"}
                ) as response:
                    if response.status == 200:
                        vulnerable_endpoints.append({
                            "endpoint": "/auth/login",
                            "payload": str(payload)
                        })
            except:
                pass
        
        if vulnerable_endpoints:
            self.results.append({
                "test": "NoSQL Injection",
                "status": "FAIL",
                "severity": "HIGH",
                "details": f"Found {len(vulnerable_endpoints)} NoSQL injection vulnerabilities"
            })
            print(f"   ❌ Found {len(vulnerable_endpoints)} NoSQL injection vulnerabilities")
        else:
            self.results.append({
                "test": "NoSQL Injection",
                "status": "PASS",
                "details": "No NoSQL injection vulnerabilities detected"
            })
            print("   ✅ No NoSQL injection vulnerabilities detected")
    
    async def test_xss_injection(self):
        """Test for Cross-Site Scripting vulnerabilities"""
        print("\n🔍 Testing XSS Injection...")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>alert('XSS')</script>",
            "\"onfocus=\"alert('XSS')\"autofocus=\"",
            "<iframe src='javascript:alert()'>"
        ]
        
        vulnerable_endpoints = []
        
        # Test user creation/update endpoints
        test_data = {
            "first_name": "PAYLOAD",
            "last_name": "Test",
            "bio": "PAYLOAD"
        }
        
        for payload in xss_payloads:
            # Test user profile update
            if self.auth_token:
                test_data_with_payload = {
                    k: v.replace("PAYLOAD", payload) if v == "PAYLOAD" else v
                    for k, v in test_data.items()
                }
                
                async with self.session.patch(
                    f"{self.api_base}/users/me",
                    json=test_data_with_payload,
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                ) as response:
                    if response.status == 200:
                        # Get the data back to check if XSS is reflected
                        async with self.session.get(
                            f"{self.api_base}/users/me",
                            headers={"Authorization": f"Bearer {self.auth_token}"}
                        ) as get_response:
                            if get_response.status == 200:
                                data = await get_response.json()
                                # Check if payload is returned without encoding
                                for field, value in data.items():
                                    if isinstance(value, str) and payload in value:
                                        vulnerable_endpoints.append({
                                            "endpoint": "/users/me",
                                            "field": field,
                                            "payload": payload
                                        })
        
        if vulnerable_endpoints:
            self.results.append({
                "test": "XSS Injection",
                "status": "FAIL",
                "severity": "HIGH",
                "details": f"Found {len(vulnerable_endpoints)} XSS vulnerabilities"
            })
            print(f"   ❌ Found {len(vulnerable_endpoints)} XSS vulnerabilities")
        else:
            self.results.append({
                "test": "XSS Injection",
                "status": "PASS",
                "details": "No XSS vulnerabilities detected"
            })
            print("   ✅ No XSS vulnerabilities detected")
    
    async def test_xxe_injection(self):
        """Test for XML External Entity injection"""
        print("\n🔍 Testing XXE Injection...")
        
        xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ELEMENT foo ANY>
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>"""
        
        vulnerable = False
        
        # Test XML upload endpoints
        headers = {"Content-Type": "application/xml"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test various endpoints that might accept XML
        test_endpoints = ["/upload", "/import", "/data"]
        
        for endpoint in test_endpoints:
            try:
                async with self.session.post(
                    f"{self.api_base}{endpoint}",
                    data=xxe_payload,
                    headers=headers
                ) as response:
                    text = await response.text()
                    # Check if file contents are reflected
                    if "root:" in text or "/etc/passwd" in text:
                        vulnerable = True
                        break
            except:
                pass
        
        if vulnerable:
            self.results.append({
                "test": "XXE Injection",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "XXE vulnerability detected"
            })
            print("   ❌ XXE vulnerability detected")
        else:
            self.results.append({
                "test": "XXE Injection",
                "status": "PASS",
                "details": "No XXE vulnerabilities detected"
            })
            print("   ✅ No XXE vulnerabilities detected")
    
    async def test_mass_assignment(self):
        """Test for mass assignment vulnerabilities"""
        print("\n🔍 Testing Mass Assignment...")
        
        issues = []
        
        if self.auth_token:
            # Try to update protected fields
            protected_fields = {
                "role": "admin",
                "is_admin": True,
                "is_superuser": True,
                "permissions": ["admin"],
                "user_id": 1,
                "id": 999,
                "created_at": "2000-01-01",
                "email_verified": True
            }
            
            # Get current user data
            async with self.session.get(
                f"{self.api_base}/users/me",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            ) as response:
                if response.status == 200:
                    original_data = await response.json()
                    
                    # Try to update with protected fields
                    update_data = {
                        "first_name": "Test",
                        **protected_fields
                    }
                    
                    async with self.session.patch(
                        f"{self.api_base}/users/me",
                        json=update_data,
                        headers={"Authorization": f"Bearer {self.auth_token}"}
                    ) as update_response:
                        if update_response.status == 200:
                            # Check if protected fields were updated
                            async with self.session.get(
                                f"{self.api_base}/users/me",
                                headers={"Authorization": f"Bearer {self.auth_token}"}
                            ) as check_response:
                                if check_response.status == 200:
                                    new_data = await check_response.json()
                                    
                                    for field, value in protected_fields.items():
                                        if field in new_data and new_data[field] == value:
                                            issues.append(f"Mass assignment of {field}")
        
        if issues:
            self.results.append({
                "test": "Mass Assignment",
                "status": "FAIL",
                "severity": "HIGH",
                "details": f"Vulnerable to mass assignment: {', '.join(issues)}"
            })
            print(f"   ❌ Mass assignment vulnerabilities found: {len(issues)}")
        else:
            self.results.append({
                "test": "Mass Assignment",
                "status": "PASS",
                "details": "No mass assignment vulnerabilities detected"
            })
            print("   ✅ No mass assignment vulnerabilities detected")
    
    async def test_api_versioning(self):
        """Test API versioning security"""
        print("\n🔍 Testing API Versioning...")
        
        issues = []
        
        # Test different API versions
        versions = ["v1", "v2", "v0", ""]
        
        for version in versions:
            test_url = f"{self.base_url}/api/{version}/users" if version else f"{self.base_url}/api/users"
            
            try:
                async with self.session.get(test_url) as response:
                    if response.status in [200, 401, 403]:
                        if version not in ["v1"]:  # Assuming v1 is current
                            issues.append(f"Accessible API version: {version if version else 'unversioned'}")
            except:
                pass
        
        # Test for deprecated endpoints
        deprecated_endpoints = ["/api/old", "/api/legacy", "/api/v0"]
        for endpoint in deprecated_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status in [200, 401, 403]:
                        issues.append(f"Deprecated endpoint accessible: {endpoint}")
            except:
                pass
        
        if issues:
            self.results.append({
                "test": "API Versioning",
                "status": "WARN",
                "severity": "LOW",
                "details": f"API versioning issues: {'; '.join(issues)}"
            })
            print(f"   ⚠️  API versioning issues found: {len(issues)}")
        else:
            self.results.append({
                "test": "API Versioning",
                "status": "PASS",
                "details": "API versioning properly controlled"
            })
            print("   ✅ API versioning properly controlled")
    
    async def test_cors_configuration(self):
        """Test CORS configuration"""
        print("\n🔍 Testing CORS Configuration...")
        
        issues = []
        
        # Test with different origins
        test_origins = [
            "http://evil.com",
            "null",
            "file://",
            "*"
        ]
        
        for origin in test_origins:
            headers = {"Origin": origin}
            
            async with self.session.options(
                f"{self.api_base}/users",
                headers=headers
            ) as response:
                cors_headers = {
                    "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
                    "access-control-allow-credentials": response.headers.get("Access-Control-Allow-Credentials"),
                    "access-control-allow-methods": response.headers.get("Access-Control-Allow-Methods")
                }
                
                # Check for overly permissive CORS
                if cors_headers["access-control-allow-origin"] == "*":
                    issues.append("Wildcard origin allowed")
                elif cors_headers["access-control-allow-origin"] == origin:
                    issues.append(f"Arbitrary origin accepted: {origin}")
                
                if cors_headers["access-control-allow-credentials"] == "true" and \
                   cors_headers["access-control-allow-origin"] == "*":
                    issues.append("Credentials allowed with wildcard origin")
        
        if issues:
            self.results.append({
                "test": "CORS Configuration",
                "status": "FAIL",
                "severity": "MEDIUM",
                "details": f"CORS misconfigurations: {'; '.join(issues)}"
            })
            print(f"   ❌ CORS misconfigurations found: {len(issues)}")
        else:
            self.results.append({
                "test": "CORS Configuration",
                "status": "PASS",
                "details": "CORS properly configured"
            })
            print("   ✅ CORS properly configured")
    
    async def test_http_methods(self):
        """Test for unnecessary HTTP methods"""
        print("\n🔍 Testing HTTP Methods...")
        
        issues = []
        
        # Test various endpoints for unnecessary methods
        test_endpoints = ["/users", "/reports", "/cycles"]
        unnecessary_methods = ["TRACE", "TRACK", "DEBUG", "CONNECT"]
        
        for endpoint in test_endpoints:
            for method in unnecessary_methods:
                try:
                    async with self.session.request(
                        method,
                        f"{self.api_base}{endpoint}"
                    ) as response:
                        if response.status != 405:  # Method Not Allowed
                            issues.append(f"{method} allowed on {endpoint}")
                except:
                    pass
            
            # Test OPTIONS for information disclosure
            async with self.session.options(f"{self.api_base}{endpoint}") as response:
                allow_header = response.headers.get("Allow", "")
                if "TRACE" in allow_header or "TRACK" in allow_header:
                    issues.append(f"Dangerous methods in Allow header: {endpoint}")
        
        if issues:
            self.results.append({
                "test": "HTTP Methods",
                "status": "FAIL",
                "severity": "LOW",
                "details": f"Unnecessary HTTP methods: {'; '.join(issues)}"
            })
            print(f"   ❌ Unnecessary HTTP methods found: {len(issues)}")
        else:
            self.results.append({
                "test": "HTTP Methods",
                "status": "PASS",
                "details": "Only necessary HTTP methods allowed"
            })
            print("   ✅ Only necessary HTTP methods allowed")
    
    async def test_content_type_validation(self):
        """Test content type validation"""
        print("\n🔍 Testing Content Type Validation...")
        
        issues = []
        
        # Test with various content types
        test_data = {"test": "data"}
        content_types = [
            "application/json",
            "text/plain",
            "application/xml",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "application/octet-stream"
        ]
        
        for content_type in content_types:
            headers = {"Content-Type": content_type}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Send JSON data with wrong content type
            async with self.session.post(
                f"{self.api_base}/users",
                data=json.dumps(test_data) if content_type != "application/json" else None,
                json=test_data if content_type == "application/json" else None,
                headers=headers
            ) as response:
                # If non-JSON content type is accepted for JSON endpoint
                if content_type != "application/json" and response.status in [200, 201, 400]:
                    issues.append(f"Accepts {content_type} for JSON endpoint")
        
        if issues:
            self.results.append({
                "test": "Content Type Validation",
                "status": "WARN",
                "severity": "LOW",
                "details": f"Content type validation issues: {'; '.join(issues)}"
            })
            print(f"   ⚠️  Content type validation issues: {len(issues)}")
        else:
            self.results.append({
                "test": "Content Type Validation",
                "status": "PASS",
                "details": "Content types properly validated"
            })
            print("   ✅ Content types properly validated")
    
    async def test_api_dos(self):
        """Test for API DoS vulnerabilities"""
        print("\n🔍 Testing API DoS Protection...")
        
        issues = []
        
        # Test large payload
        large_data = {"data": "x" * 1000000}  # 1MB of data
        
        try:
            async with self.session.post(
                f"{self.api_base}/test",
                json=large_data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status in [200, 201]:
                    issues.append("Large payloads accepted without limit")
        except:
            pass
        
        # Test deeply nested JSON
        nested_data = {"a": {}}
        current = nested_data["a"]
        for _ in range(1000):
            current["a"] = {}
            current = current["a"]
        
        try:
            async with self.session.post(
                f"{self.api_base}/test",
                json=nested_data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status in [200, 201]:
                    issues.append("Deeply nested JSON accepted")
        except:
            pass
        
        # Test array bombs
        array_bomb = [[[[[[[[[[[]]]]]]]]]]] * 1000
        
        try:
            async with self.session.post(
                f"{self.api_base}/test",
                json=array_bomb,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status in [200, 201]:
                    issues.append("Array bombs accepted")
        except:
            pass
        
        if issues:
            self.results.append({
                "test": "API DoS Protection",
                "status": "FAIL",
                "severity": "MEDIUM",
                "details": f"DoS vulnerabilities: {'; '.join(issues)}"
            })
            print(f"   ❌ API DoS vulnerabilities found: {len(issues)}")
        else:
            self.results.append({
                "test": "API DoS Protection",
                "status": "PASS",
                "details": "API protected against DoS attacks"
            })
            print("   ✅ API protected against DoS attacks")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 API SECURITY TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r.get("status") == "WARN")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Warnings: {warned}")
        
        if failed > 0:
            print("\n⚠️  CRITICAL SECURITY ISSUES:")
            for result in self.results:
                if result["status"] == "FAIL":
                    severity = result.get("severity", "UNKNOWN")
                    print(f"\n  [{severity}] {result['test']}")
                    print(f"  Details: {result['details']}")
        
        # Save detailed report
        report_file = f"api_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "summary": {
                    "total": len(self.results),
                    "passed": passed,
                    "failed": failed,
                    "warnings": warned
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")


async def main():
    tester = APISecurityTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())