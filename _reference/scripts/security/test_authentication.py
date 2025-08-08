#!/usr/bin/env python3
"""
Authentication Security Testing Script
Tests for common authentication vulnerabilities
"""

import asyncio
import aiohttp
import time
import jwt
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
import hashlib
import random
import string

class AuthenticationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.results = []
        self.test_users = []
        
    async def run_all_tests(self):
        """Run all authentication tests"""
        print("🔐 Starting Authentication Security Tests")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Run tests
            await self.test_brute_force_protection()
            await self.test_password_policy()
            await self.test_jwt_security()
            await self.test_session_management()
            await self.test_password_reset_security()
            await self.test_user_enumeration()
            await self.test_rate_limiting()
            await self.test_concurrent_sessions()
            
        # Generate report
        self.generate_report()
    
    async def test_brute_force_protection(self):
        """Test for brute force attack protection"""
        print("\n🔍 Testing Brute Force Protection...")
        
        test_email = "test@example.com"
        attempts = []
        
        # Try 10 failed login attempts
        for i in range(10):
            start_time = time.time()
            
            async with self.session.post(
                f"{self.api_base}/auth/login",
                json={"email": test_email, "password": f"wrong{i}"}
            ) as response:
                end_time = time.time()
                attempts.append({
                    "attempt": i + 1,
                    "status": response.status,
                    "time": end_time - start_time
                })
                
                # Check if account gets locked
                if response.status == 429 or response.status == 423:
                    self.results.append({
                        "test": "Brute Force Protection",
                        "status": "PASS",
                        "details": f"Account locked after {i + 1} attempts"
                    })
                    print(f"   ✅ Account locked after {i + 1} attempts")
                    return
        
        # If we get here, no lockout occurred
        self.results.append({
            "test": "Brute Force Protection",
            "status": "FAIL",
            "severity": "HIGH",
            "details": "No account lockout after 10 failed attempts"
        })
        print("   ❌ No account lockout detected")
    
    async def test_password_policy(self):
        """Test password policy enforcement"""
        print("\n🔍 Testing Password Policy...")
        
        weak_passwords = [
            "123456",
            "password",
            "12345678",
            "qwerty",
            "abc123",
            "Password1",  # No special char
            "P@ssw0rd",   # Common pattern
            "short",      # Too short
        ]
        
        results = []
        for pwd in weak_passwords:
            async with self.session.post(
                f"{self.api_base}/auth/register",
                json={
                    "email": f"test_{random.randint(1000,9999)}@example.com",
                    "password": pwd,
                    "first_name": "Test",
                    "last_name": "User"
                }
            ) as response:
                if response.status == 200 or response.status == 201:
                    results.append(f"Accepted weak password: {pwd}")
        
        if results:
            self.results.append({
                "test": "Password Policy",
                "status": "FAIL",
                "severity": "MEDIUM",
                "details": f"Weak passwords accepted: {', '.join(results)}"
            })
            print(f"   ❌ {len(results)} weak passwords accepted")
        else:
            self.results.append({
                "test": "Password Policy",
                "status": "PASS",
                "details": "All weak passwords rejected"
            })
            print("   ✅ All weak passwords rejected")
    
    async def test_jwt_security(self):
        """Test JWT token security"""
        print("\n🔍 Testing JWT Security...")
        
        issues = []
        
        # First, get a valid token
        async with self.session.post(
            f"{self.api_base}/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                token = data.get("access_token")
                
                if token:
                    # Decode without verification to inspect
                    try:
                        header = jwt.get_unverified_header(token)
                        payload = jwt.decode(token, options={"verify_signature": False})
                        
                        # Check algorithm
                        if header.get("alg") == "none":
                            issues.append("JWT using 'none' algorithm")
                        elif header.get("alg") in ["HS256", "HS384", "HS512"]:
                            # Try common secrets
                            common_secrets = ["secret", "key", "password", "123456", "admin"]
                            for secret in common_secrets:
                                try:
                                    jwt.decode(token, secret, algorithms=[header.get("alg")])
                                    issues.append(f"JWT using weak secret: {secret}")
                                    break
                                except:
                                    pass
                        
                        # Check expiration
                        exp = payload.get("exp")
                        if exp:
                            exp_time = datetime.fromtimestamp(exp)
                            now = datetime.now()
                            if exp_time - now > timedelta(days=1):
                                issues.append(f"JWT expiration too long: {exp_time - now}")
                        else:
                            issues.append("JWT has no expiration")
                        
                        # Test algorithm confusion
                        # Create a token with 'none' algorithm
                        fake_token = jwt.encode(payload, "", algorithm="none")
                        async with self.session.get(
                            f"{self.api_base}/users/me",
                            headers={"Authorization": f"Bearer {fake_token}"}
                        ) as test_response:
                            if test_response.status == 200:
                                issues.append("Algorithm confusion vulnerability - 'none' algorithm accepted")
                    
                    except Exception as e:
                        issues.append(f"JWT parsing error: {str(e)}")
        
        if issues:
            self.results.append({
                "test": "JWT Security",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "; ".join(issues)
            })
            print(f"   ❌ {len(issues)} JWT security issues found")
        else:
            self.results.append({
                "test": "JWT Security",
                "status": "PASS",
                "details": "JWT implementation appears secure"
            })
            print("   ✅ JWT implementation appears secure")
    
    async def test_session_management(self):
        """Test session management security"""
        print("\n🔍 Testing Session Management...")
        
        issues = []
        
        # Login and get token
        async with self.session.post(
            f"{self.api_base}/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                token = data.get("access_token")
                
                # Test token reuse after logout
                async with self.session.post(
                    f"{self.api_base}/auth/logout",
                    headers={"Authorization": f"Bearer {token}"}
                ) as logout_response:
                    pass
                
                # Try to use token after logout
                async with self.session.get(
                    f"{self.api_base}/users/me",
                    headers={"Authorization": f"Bearer {token}"}
                ) as test_response:
                    if test_response.status == 200:
                        issues.append("Token still valid after logout")
                
                # Test session fixation
                # Check if session ID changes after login
                cookies_before = self.session.cookie_jar
                async with self.session.post(
                    f"{self.api_base}/auth/login",
                    json={"email": "admin@example.com", "password": "admin123"}
                ) as response:
                    cookies_after = self.session.cookie_jar
                    # Simple check - in real test would compare session IDs
                    if str(cookies_before) == str(cookies_after):
                        issues.append("Possible session fixation vulnerability")
        
        if issues:
            self.results.append({
                "test": "Session Management",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "; ".join(issues)
            })
            print(f"   ❌ {len(issues)} session management issues found")
        else:
            self.results.append({
                "test": "Session Management",
                "status": "PASS",
                "details": "Session management appears secure"
            })
            print("   ✅ Session management appears secure")
    
    async def test_password_reset_security(self):
        """Test password reset flow security"""
        print("\n🔍 Testing Password Reset Security...")
        
        issues = []
        
        # Test password reset token generation
        test_email = "test@example.com"
        
        # Request password reset
        async with self.session.post(
            f"{self.api_base}/auth/forgot-password",
            json={"email": test_email}
        ) as response:
            if response.status == 200:
                # In a real test, we'd check:
                # 1. Token randomness
                # 2. Token expiration
                # 3. Token single-use
                # 4. Rate limiting on reset requests
                
                # Test predictable tokens by requesting multiple resets
                tokens = []
                for _ in range(3):
                    async with self.session.post(
                        f"{self.api_base}/auth/forgot-password",
                        json={"email": test_email}
                    ) as resp:
                        # In real app, would extract token from email/response
                        pass
                
                # Test timing attack - compare response times
                start_valid = time.time()
                async with self.session.post(
                    f"{self.api_base}/auth/forgot-password",
                    json={"email": "admin@example.com"}
                ) as resp:
                    time_valid = time.time() - start_valid
                
                start_invalid = time.time()
                async with self.session.post(
                    f"{self.api_base}/auth/forgot-password",
                    json={"email": "nonexistent@example.com"}
                ) as resp:
                    time_invalid = time.time() - start_invalid
                
                # If times differ significantly, possible user enumeration
                if abs(time_valid - time_invalid) > 0.1:
                    issues.append("Timing attack possible in password reset")
        
        if issues:
            self.results.append({
                "test": "Password Reset Security",
                "status": "FAIL",
                "severity": "MEDIUM",
                "details": "; ".join(issues)
            })
            print(f"   ❌ {len(issues)} password reset issues found")
        else:
            self.results.append({
                "test": "Password Reset Security",
                "status": "PASS",
                "details": "Password reset appears secure"
            })
            print("   ✅ Password reset appears secure")
    
    async def test_user_enumeration(self):
        """Test for user enumeration vulnerabilities"""
        print("\n🔍 Testing User Enumeration...")
        
        issues = []
        
        # Test login endpoint
        # Valid user, wrong password
        start = time.time()
        async with self.session.post(
            f"{self.api_base}/auth/login",
            json={"email": "admin@example.com", "password": "wrongpass"}
        ) as response:
            valid_user_time = time.time() - start
            valid_user_msg = await response.text()
        
        # Invalid user
        start = time.time()
        async with self.session.post(
            f"{self.api_base}/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpass"}
        ) as response:
            invalid_user_time = time.time() - start
            invalid_user_msg = await response.text()
        
        # Check for differences
        if valid_user_msg != invalid_user_msg:
            issues.append("Different error messages for valid/invalid users")
        
        if abs(valid_user_time - invalid_user_time) > 0.1:
            issues.append("Timing difference allows user enumeration")
        
        # Test registration endpoint
        async with self.session.post(
            f"{self.api_base}/auth/register",
            json={
                "email": "admin@example.com",
                "password": "Test123!@#",
                "first_name": "Test",
                "last_name": "User"
            }
        ) as response:
            if response.status == 409 or "already exists" in await response.text():
                issues.append("Registration endpoint reveals existing users")
        
        if issues:
            self.results.append({
                "test": "User Enumeration",
                "status": "FAIL",
                "severity": "MEDIUM",
                "details": "; ".join(issues)
            })
            print(f"   ❌ {len(issues)} user enumeration issues found")
        else:
            self.results.append({
                "test": "User Enumeration",
                "status": "PASS",
                "details": "No user enumeration vulnerabilities found"
            })
            print("   ✅ No user enumeration vulnerabilities found")
    
    async def test_rate_limiting(self):
        """Test rate limiting effectiveness"""
        print("\n🔍 Testing Rate Limiting...")
        
        endpoint = f"{self.api_base}/auth/login"
        requests_made = 0
        rate_limited = False
        
        # Make rapid requests
        start_time = time.time()
        for i in range(100):
            async with self.session.post(
                endpoint,
                json={"email": "test@example.com", "password": "test"}
            ) as response:
                requests_made += 1
                if response.status == 429:
                    rate_limited = True
                    break
        
        elapsed = time.time() - start_time
        
        if rate_limited:
            self.results.append({
                "test": "Rate Limiting",
                "status": "PASS",
                "details": f"Rate limited after {requests_made} requests in {elapsed:.2f}s"
            })
            print(f"   ✅ Rate limited after {requests_made} requests")
        else:
            self.results.append({
                "test": "Rate Limiting",
                "status": "FAIL",
                "severity": "HIGH",
                "details": f"No rate limiting after {requests_made} requests in {elapsed:.2f}s"
            })
            print(f"   ❌ No rate limiting detected after {requests_made} requests")
    
    async def test_concurrent_sessions(self):
        """Test concurrent session handling"""
        print("\n🔍 Testing Concurrent Sessions...")
        
        # Create test user
        test_email = f"concurrent_test_{random.randint(1000,9999)}@example.com"
        test_password = "Test123!@#"
        
        async with self.session.post(
            f"{self.api_base}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "first_name": "Test",
                "last_name": "User"
            }
        ) as response:
            if response.status in [200, 201]:
                # Login from multiple "devices"
                tokens = []
                for i in range(3):
                    async with self.session.post(
                        f"{self.api_base}/auth/login",
                        json={"email": test_email, "password": test_password}
                    ) as login_resp:
                        if login_resp.status == 200:
                            data = await login_resp.json()
                            tokens.append(data.get("access_token"))
                
                # Check if all tokens are valid
                valid_tokens = 0
                for token in tokens:
                    async with self.session.get(
                        f"{self.api_base}/users/me",
                        headers={"Authorization": f"Bearer {token}"}
                    ) as test_resp:
                        if test_resp.status == 200:
                            valid_tokens += 1
                
                if valid_tokens == len(tokens):
                    self.results.append({
                        "test": "Concurrent Sessions",
                        "status": "INFO",
                        "details": f"Multiple concurrent sessions allowed ({valid_tokens} active)"
                    })
                    print(f"   ℹ️  Multiple concurrent sessions allowed")
                else:
                    self.results.append({
                        "test": "Concurrent Sessions",
                        "status": "INFO",
                        "details": f"Limited concurrent sessions ({valid_tokens}/{len(tokens)} active)"
                    })
                    print(f"   ℹ️  Limited concurrent sessions")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 AUTHENTICATION SECURITY TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        info = sum(1 for r in self.results if r["status"] == "INFO")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ℹ️  Info: {info}")
        
        if failed > 0:
            print("\n⚠️  SECURITY ISSUES FOUND:")
            for result in self.results:
                if result["status"] == "FAIL":
                    severity = result.get("severity", "UNKNOWN")
                    print(f"\n  [{severity}] {result['test']}")
                    print(f"  Details: {result['details']}")
        
        # Save detailed report
        report_file = f"auth_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "summary": {
                    "total": len(self.results),
                    "passed": passed,
                    "failed": failed,
                    "info": info
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")


async def main():
    tester = AuthenticationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())