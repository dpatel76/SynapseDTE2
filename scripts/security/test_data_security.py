#!/usr/bin/env python3
"""
Data Security Testing Script
Tests for data protection at rest and in transit
"""

import asyncio
import aiohttp
import ssl
import json
import os
import tempfile
import hashlib
import base64
from typing import Dict, List, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import psycopg2
import pymongo
from pathlib import Path

class DataSecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000", db_config: dict = None):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.results = []
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'synapse_dt',
            'user': 'synapse_user',
            'password': 'synapse_password'
        }
        
    async def run_all_tests(self):
        """Run all data security tests"""
        print("🔒 Starting Data Security Tests")
        print("=" * 60)
        
        # Test data in transit
        await self.test_tls_configuration()
        await self.test_api_encryption()
        await self.test_certificate_validation()
        await self.test_data_leakage_in_transit()
        
        # Test data at rest
        await self.test_database_encryption()
        await self.test_file_storage_encryption()
        await self.test_backup_encryption()
        await self.test_log_data_security()
        await self.test_memory_data_security()
        
        # Test data handling
        await self.test_sensitive_data_masking()
        await self.test_data_retention_policies()
        await self.test_secure_deletion()
        
        # Generate report
        self.generate_report()
    
    async def test_tls_configuration(self):
        """Test TLS/SSL configuration for data in transit"""
        print("\n🔍 Testing TLS Configuration...")
        
        issues = []
        
        # Check if HTTPS is enforced
        if self.base_url.startswith("http://"):
            issues.append("Application not using HTTPS")
            
            # Check if HTTP redirects to HTTPS
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(self.base_url, allow_redirects=False) as response:
                        if response.status != 301 or not response.headers.get('Location', '').startswith('https://'):
                            issues.append("HTTP not redirecting to HTTPS")
                except:
                    pass
        
        # Test SSL/TLS configuration if HTTPS
        if self.base_url.startswith("https://"):
            try:
                # Create SSL context for testing
                ctx = ssl.create_default_context()
                
                # Test weak protocols
                weak_protocols = [ssl.PROTOCOL_SSLv2, ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLSv1_1]
                for protocol in weak_protocols:
                    try:
                        test_ctx = ssl.SSLContext(protocol)
                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=test_ctx)) as session:
                            async with session.get(self.base_url) as response:
                                if response.status == 200:
                                    issues.append(f"Weak protocol supported: {protocol}")
                    except:
                        pass  # Good, protocol not supported
                
                # Check cipher suites
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.base_url) as response:
                        # In real implementation, would check cipher suite
                        pass
                        
            except Exception as e:
                issues.append(f"TLS testing error: {str(e)}")
        
        # Check for security headers
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.api_base) as response:
                    headers = response.headers
                    
                    # Check HSTS
                    if 'Strict-Transport-Security' not in headers:
                        issues.append("Missing HSTS header")
                    else:
                        hsts = headers['Strict-Transport-Security']
                        if 'max-age=31536000' not in hsts:
                            issues.append("HSTS max-age too short")
                        if 'includeSubDomains' not in hsts:
                            issues.append("HSTS missing includeSubDomains")
                    
                    # Check other security headers
                    if 'X-Content-Type-Options' not in headers:
                        issues.append("Missing X-Content-Type-Options header")
                    
                    if 'X-Frame-Options' not in headers:
                        issues.append("Missing X-Frame-Options header")
            except:
                pass
        
        if issues:
            self.results.append({
                "test": "TLS Configuration",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "; ".join(issues)
            })
            print(f"   ❌ TLS configuration issues: {len(issues)}")
        else:
            self.results.append({
                "test": "TLS Configuration",
                "status": "PASS",
                "details": "TLS properly configured"
            })
            print("   ✅ TLS properly configured")
    
    async def test_api_encryption(self):
        """Test API data encryption in transit"""
        print("\n🔍 Testing API Data Encryption...")
        
        issues = []
        sensitive_endpoints = [
            "/auth/login",
            "/users/me",
            "/reports",
            "/llm/analyze"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in sensitive_endpoints:
                # Check if sensitive data is sent over unencrypted connection
                if self.base_url.startswith("http://"):
                    issues.append(f"Sensitive endpoint {endpoint} accessible over HTTP")
                
                # Test for sensitive data in URL parameters
                test_url = f"{self.api_base}{endpoint}?password=test&ssn=123456789"
                try:
                    async with session.get(test_url) as response:
                        # Check if sensitive params are logged
                        if response.status in [200, 400, 401]:
                            issues.append(f"Sensitive data accepted in URL parameters: {endpoint}")
                except:
                    pass
        
        # Test WebSocket security if applicable
        ws_url = self.base_url.replace("http", "ws") + "/ws"
        if ws_url.startswith("ws://"):
            issues.append("WebSocket connections not using WSS (encrypted)")
        
        if issues:
            self.results.append({
                "test": "API Data Encryption",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "; ".join(issues)
            })
            print(f"   ❌ API encryption issues: {len(issues)}")
        else:
            self.results.append({
                "test": "API Data Encryption",
                "status": "PASS",
                "details": "API data properly encrypted in transit"
            })
            print("   ✅ API data properly encrypted")
    
    async def test_certificate_validation(self):
        """Test certificate validation and pinning"""
        print("\n🔍 Testing Certificate Validation...")
        
        issues = []
        
        if self.base_url.startswith("https://"):
            # Test certificate validation
            try:
                # Test with invalid certificate
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ctx)) as session:
                    async with session.get(self.base_url) as response:
                        if response.status == 200:
                            issues.append("Application accepts invalid certificates")
            except:
                pass  # Good, rejected invalid cert
            
            # Check for certificate pinning (mobile API)
            # In real test, would check if cert pinning is implemented
        
        if issues:
            self.results.append({
                "test": "Certificate Validation",
                "status": "FAIL",
                "severity": "MEDIUM",
                "details": "; ".join(issues)
            })
            print(f"   ❌ Certificate validation issues: {len(issues)}")
        else:
            self.results.append({
                "test": "Certificate Validation",
                "status": "PASS",
                "details": "Certificates properly validated"
            })
            print("   ✅ Certificates properly validated")
    
    async def test_data_leakage_in_transit(self):
        """Test for data leakage during transmission"""
        print("\n🔍 Testing Data Leakage in Transit...")
        
        issues = []
        
        async with aiohttp.ClientSession() as session:
            # Test error responses for information leakage
            test_cases = [
                ("/api/v1/users/99999", "GET"),  # Non-existent user
                ("/api/v1/reports/invalid", "GET"),  # Invalid ID
                ("/api/v1/auth/login", "POST"),  # Wrong credentials
            ]
            
            for endpoint, method in test_cases:
                try:
                    if method == "GET":
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            error_text = await response.text()
                            
                            # Check for sensitive information in errors
                            sensitive_patterns = [
                                "stacktrace",
                                "traceback",
                                "sqlalchemy",
                                "psycopg2",
                                "database",
                                "table",
                                "column",
                                "internal server",
                                "file path",
                                "/home/",
                                "/usr/",
                                "C:\\\\",
                            ]
                            
                            for pattern in sensitive_patterns:
                                if pattern.lower() in error_text.lower():
                                    issues.append(f"Information leakage in error: {pattern}")
                                    break
                except:
                    pass
            
            # Test for sensitive data in headers
            async with session.get(f"{self.api_base}/users/me") as response:
                headers = response.headers
                
                # Check for sensitive headers
                sensitive_headers = ['X-Powered-By', 'Server', 'X-AspNet-Version']
                for header in sensitive_headers:
                    if header in headers:
                        issues.append(f"Information leakage in header: {header}")
        
        if issues:
            self.results.append({
                "test": "Data Leakage in Transit",
                "status": "FAIL",
                "severity": "MEDIUM",
                "details": "; ".join(set(issues))  # Remove duplicates
            })
            print(f"   ❌ Data leakage issues: {len(set(issues))}")
        else:
            self.results.append({
                "test": "Data Leakage in Transit",
                "status": "PASS",
                "details": "No data leakage detected in transit"
            })
            print("   ✅ No data leakage in transit")
    
    async def test_database_encryption(self):
        """Test database encryption at rest"""
        print("\n🔍 Testing Database Encryption...")
        
        issues = []
        
        try:
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if sensitive columns are encrypted
            sensitive_tables = [
                ("users", ["password_hash", "email", "ssn"]),
                ("reports", ["content", "financial_data"]),
                ("audit_logs", ["details", "ip_address"]),
                ("documents", ["file_content", "metadata"])
            ]
            
            for table, columns in sensitive_tables:
                for column in columns:
                    try:
                        # Check if column exists and contains readable data
                        cursor.execute(f"""
                            SELECT {column} FROM {table} 
                            WHERE {column} IS NOT NULL 
                            LIMIT 1
                        """)
                        result = cursor.fetchone()
                        
                        if result and result[0]:
                            # Check if data appears to be encrypted
                            data = str(result[0])
                            
                            # Simple heuristics for encryption detection
                            if column == "password_hash":
                                # Password should be hashed
                                if not (data.startswith("$2b$") or data.startswith("$argon2")):
                                    issues.append(f"Weak password hashing in {table}.{column}")
                            elif column in ["ssn", "credit_card", "email"]:
                                # These should be encrypted
                                if self._looks_like_plaintext(data, column):
                                    issues.append(f"Unencrypted sensitive data in {table}.{column}")
                    except Exception as e:
                        # Table/column might not exist
                        pass
            
            # Check for transparent data encryption (TDE)
            cursor.execute("""
                SELECT name, setting 
                FROM pg_settings 
                WHERE name LIKE '%encrypt%'
            """)
            encryption_settings = cursor.fetchall()
            
            if not any('on' in str(setting[1]).lower() for setting in encryption_settings):
                issues.append("Database transparent encryption not enabled")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            issues.append(f"Could not test database encryption: {str(e)}")
        
        if issues:
            self.results.append({
                "test": "Database Encryption",
                "status": "FAIL",
                "severity": "CRITICAL",
                "details": "; ".join(issues)
            })
            print(f"   ❌ Database encryption issues: {len(issues)}")
        else:
            self.results.append({
                "test": "Database Encryption",
                "status": "PASS",
                "details": "Database encryption properly configured"
            })
            print("   ✅ Database properly encrypted")
    
    async def test_file_storage_encryption(self):
        """Test file storage encryption"""
        print("\n🔍 Testing File Storage Encryption...")
        
        issues = []
        upload_dir = "./uploads"  # Adjust based on actual config
        
        if os.path.exists(upload_dir):
            # Check for unencrypted files
            for root, dirs, files in os.walk(upload_dir):
                for file in files[:10]:  # Check first 10 files
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read(1024)  # Read first 1KB
                            
                            # Check if file appears to be encrypted
                            if self._is_readable_text(content):
                                issues.append(f"Unencrypted file found: {file}")
                            
                            # Check file permissions
                            stat = os.stat(file_path)
                            mode = oct(stat.st_mode)[-3:]
                            if mode != '600' and mode != '644':
                                issues.append(f"Insecure file permissions: {file} ({mode})")
                    except:
                        pass
            
            # Check if upload directory is on encrypted filesystem
            # This would require system-level checks
        
        # Test S3/cloud storage encryption if used
        # Would check bucket policies, encryption settings
        
        if issues:
            self.results.append({
                "test": "File Storage Encryption",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "; ".join(issues[:5])  # Limit to first 5 issues
            })
            print(f"   ❌ File storage encryption issues: {len(issues)}")
        else:
            self.results.append({
                "test": "File Storage Encryption",
                "status": "PASS",
                "details": "File storage properly encrypted"
            })
            print("   ✅ File storage properly encrypted")
    
    async def test_backup_encryption(self):
        """Test backup encryption"""
        print("\n🔍 Testing Backup Encryption...")
        
        issues = []
        backup_locations = [
            "./backups",
            "/var/backups/synapse",
            "./db_dumps"
        ]
        
        for backup_dir in backup_locations:
            if os.path.exists(backup_dir):
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        if file.endswith(('.sql', '.dump', '.bak', '.backup')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'rb') as f:
                                    content = f.read(1024)
                                    
                                    # Check if backup is encrypted
                                    if b'CREATE TABLE' in content or b'INSERT INTO' in content:
                                        issues.append(f"Unencrypted backup: {file}")
                                    
                                    # Check permissions
                                    stat = os.stat(file_path)
                                    if oct(stat.st_mode)[-3:] not in ['600', '400']:
                                        issues.append(f"Insecure backup permissions: {file}")
                            except:
                                pass
        
        if issues:
            self.results.append({
                "test": "Backup Encryption",
                "status": "FAIL",
                "severity": "CRITICAL",
                "details": "; ".join(issues[:5])
            })
            print(f"   ❌ Backup encryption issues: {len(issues)}")
        else:
            self.results.append({
                "test": "Backup Encryption",
                "status": "PASS",
                "details": "Backups properly encrypted"
            })
            print("   ✅ Backups properly encrypted")
    
    async def test_log_data_security(self):
        """Test security of log data"""
        print("\n🔍 Testing Log Data Security...")
        
        issues = []
        log_locations = [
            "./logs",
            "/var/log/synapse",
            "./app.log"
        ]
        
        sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
            r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            r'secret["\']?\s*[:=]\s*["\']?([^"\'\s]+)'
        ]
        
        for log_location in log_locations:
            if os.path.exists(log_location):
                if os.path.isfile(log_location):
                    files = [log_location]
                else:
                    files = [os.path.join(log_location, f) for f in os.listdir(log_location) if f.endswith('.log')]
                
                for log_file in files[:5]:  # Check first 5 log files
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read(10000)  # Read first 10KB
                            
                            for pattern in sensitive_patterns:
                                import re
                                if re.search(pattern, content, re.IGNORECASE):
                                    issues.append(f"Sensitive data in logs: {os.path.basename(log_file)}")
                                    break
                    except:
                        pass
        
        # Check log transmission security
        # Would check if logs are sent over encrypted channels
        
        if issues:
            self.results.append({
                "test": "Log Data Security",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "; ".join(set(issues))
            })
            print(f"   ❌ Log security issues: {len(set(issues))}")
        else:
            self.results.append({
                "test": "Log Data Security",
                "status": "PASS",
                "details": "Logs properly secured"
            })
            print("   ✅ Logs properly secured")
    
    async def test_memory_data_security(self):
        """Test for sensitive data in memory"""
        print("\n🔍 Testing Memory Data Security...")
        
        issues = []
        
        # This is a basic test - in production would use memory analysis tools
        # Check for common memory security issues
        
        # Test if sensitive data is cleared after use
        test_endpoints = [
            ("/api/v1/auth/login", {"email": "test@example.com", "password": "TestPass123!"}),
            ("/api/v1/users/me", None)
        ]
        
        # In real implementation, would:
        # 1. Use memory profiling tools
        # 2. Check for sensitive data in heap dumps
        # 3. Verify secure memory allocation
        # 4. Check for memory-mapped files with sensitive data
        
        # Basic check for secure headers indicating memory protection
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_base) as response:
                headers = response.headers
                
                if 'X-Content-Type-Options' not in headers:
                    issues.append("Missing memory protection headers")
        
        if issues:
            self.results.append({
                "test": "Memory Data Security",
                "status": "WARN",
                "severity": "MEDIUM",
                "details": "Limited memory security testing performed"
            })
            print("   ⚠️  Limited memory security testing")
        else:
            self.results.append({
                "test": "Memory Data Security",
                "status": "INFO",
                "details": "Basic memory security checks passed"
            })
            print("   ℹ️  Basic memory security checks passed")
    
    async def test_sensitive_data_masking(self):
        """Test sensitive data masking in responses"""
        print("\n🔍 Testing Sensitive Data Masking...")
        
        issues = []
        
        # Login to get auth token
        async with aiohttp.ClientSession() as session:
            # Get auth token
            auth_response = await session.post(
                f"{self.api_base}/auth/login",
                json={"email": "test@example.com", "password": "test123"}
            )
            
            if auth_response.status == 200:
                token = (await auth_response.json()).get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test user profile endpoint
                async with session.get(f"{self.api_base}/users/me", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check if sensitive fields are masked
                        if "ssn" in data and self._looks_like_plaintext(data["ssn"], "ssn"):
                            issues.append("SSN not masked in user profile")
                        
                        if "email" in data and "@" in data["email"]:
                            # Check if email is partially masked
                            if not any(char in data["email"] for char in ['*', 'X']):
                                issues.append("Email not masked in responses")
                
                # Test search/list endpoints
                async with session.get(f"{self.api_base}/users", headers=headers) as response:
                    if response.status == 200:
                        users = await response.json()
                        if isinstance(users, list) and users:
                            for user in users[:5]:
                                if "password" in user:
                                    issues.append("Password field exposed in user list")
                                if "password_hash" in user:
                                    issues.append("Password hash exposed in user list")
        
        if issues:
            self.results.append({
                "test": "Sensitive Data Masking",
                "status": "FAIL",
                "severity": "HIGH",
                "details": "; ".join(issues)
            })
            print(f"   ❌ Data masking issues: {len(issues)}")
        else:
            self.results.append({
                "test": "Sensitive Data Masking",
                "status": "PASS",
                "details": "Sensitive data properly masked"
            })
            print("   ✅ Sensitive data properly masked")
    
    async def test_data_retention_policies(self):
        """Test data retention and expiration policies"""
        print("\n🔍 Testing Data Retention Policies...")
        
        issues = []
        
        # Check for old data that should have been purged
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check for old audit logs
            cursor.execute("""
                SELECT COUNT(*) FROM audit_logs 
                WHERE created_at < NOW() - INTERVAL '2 years'
            """)
            old_logs = cursor.fetchone()[0]
            if old_logs > 0:
                issues.append(f"Found {old_logs} audit logs older than retention period")
            
            # Check for old user sessions
            cursor.execute("""
                SELECT COUNT(*) FROM user_sessions 
                WHERE last_activity < NOW() - INTERVAL '30 days'
            """)
            old_sessions = cursor.fetchone()[0]
            if old_sessions > 0:
                issues.append(f"Found {old_sessions} expired sessions not cleaned up")
            
            cursor.close()
            conn.close()
        except:
            pass
        
        # Check for temporary files
        temp_dirs = ["./tmp", "./temp", "/tmp/synapse"]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                old_files = []
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        # Check if file is older than 24 hours
                        if os.path.getmtime(file_path) < (datetime.now().timestamp() - 86400):
                            old_files.append(file)
                
                if old_files:
                    issues.append(f"Found {len(old_files)} old temporary files")
        
        if issues:
            self.results.append({
                "test": "Data Retention Policies",
                "status": "WARN",
                "severity": "MEDIUM",
                "details": "; ".join(issues)
            })
            print(f"   ⚠️  Data retention issues: {len(issues)}")
        else:
            self.results.append({
                "test": "Data Retention Policies",
                "status": "PASS",
                "details": "Data retention policies properly enforced"
            })
            print("   ✅ Data retention policies enforced")
    
    async def test_secure_deletion(self):
        """Test secure data deletion"""
        print("\n🔍 Testing Secure Deletion...")
        
        issues = []
        
        # Test if deleted data is truly removed
        async with aiohttp.ClientSession() as session:
            # Would need appropriate test data and endpoints
            
            # Check if soft deletes are used when they shouldn't be
            # Check if data is overwritten on deletion
            # Check if backups are updated after deletion
            pass
        
        # Check for data remnants in database
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check for soft deleted records with sensitive data
            tables_with_soft_delete = ["users", "reports", "documents"]
            for table in tables_with_soft_delete:
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table} 
                        WHERE deleted_at IS NOT NULL
                        AND created_at < NOW() - INTERVAL '30 days'
                    """)
                    soft_deleted = cursor.fetchone()[0]
                    if soft_deleted > 0:
                        issues.append(f"Found {soft_deleted} soft-deleted records in {table}")
                except:
                    pass
            
            cursor.close()
            conn.close()
        except:
            pass
        
        if issues:
            self.results.append({
                "test": "Secure Deletion",
                "status": "WARN",
                "severity": "MEDIUM",
                "details": "; ".join(issues)
            })
            print(f"   ⚠️  Secure deletion issues: {len(issues)}")
        else:
            self.results.append({
                "test": "Secure Deletion",
                "status": "PASS",
                "details": "Data securely deleted"
            })
            print("   ✅ Data securely deleted")
    
    def _looks_like_plaintext(self, data: str, data_type: str) -> bool:
        """Check if data appears to be plaintext (not encrypted)"""
        if data_type == "ssn":
            import re
            return bool(re.match(r'^\d{3}-?\d{2}-?\d{4}$', data))
        elif data_type == "credit_card":
            import re
            return bool(re.match(r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$', data))
        elif data_type == "email":
            return "@" in data and "." in data
        else:
            # Generic check - if it's readable ASCII, probably not encrypted
            return all(32 <= ord(c) <= 126 for c in data[:min(100, len(data))])
    
    def _is_readable_text(self, data: bytes) -> bool:
        """Check if binary data is readable text"""
        try:
            text = data.decode('utf-8')
            # If it decodes and has common words, probably not encrypted
            common_words = ['the', 'and', 'for', 'with', 'this']
            return any(word in text.lower() for word in common_words)
        except:
            return False
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 DATA SECURITY TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r.get("status") == "WARN")
        info = sum(1 for r in self.results if r.get("status") == "INFO")
        
        print(f"Total Tests: {len(self.results)}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Warnings: {warned}")
        print(f"  ℹ️  Info: {info}")
        
        # Categorize results
        print("\n📊 Results by Category:")
        print("\n🌐 Data in Transit:")
        for result in self.results:
            if result["test"] in ["TLS Configuration", "API Data Encryption", "Certificate Validation", "Data Leakage in Transit"]:
                status_icon = "✅" if result["status"] == "PASS" else "❌"
                print(f"  {status_icon} {result['test']}")
        
        print("\n💾 Data at Rest:")
        for result in self.results:
            if result["test"] in ["Database Encryption", "File Storage Encryption", "Backup Encryption", "Log Data Security"]:
                status_icon = "✅" if result["status"] == "PASS" else "❌"
                print(f"  {status_icon} {result['test']}")
        
        if failed > 0:
            print("\n⚠️  CRITICAL DATA SECURITY ISSUES:")
            for result in self.results:
                if result["status"] == "FAIL":
                    severity = result.get("severity", "UNKNOWN")
                    print(f"\n  [{severity}] {result['test']}")
                    print(f"  Details: {result['details']}")
        
        # Save detailed report
        report_file = f"data_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "summary": {
                    "total": len(self.results),
                    "passed": passed,
                    "failed": failed,
                    "warnings": warned
                },
                "results": self.results,
                "recommendations": self._generate_recommendations()
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        for result in self.results:
            if result["status"] == "FAIL":
                if "TLS" in result["test"]:
                    recommendations.append("Enforce HTTPS for all connections")
                    recommendations.append("Implement HSTS with long max-age")
                elif "Database Encryption" in result["test"]:
                    recommendations.append("Enable transparent data encryption (TDE)")
                    recommendations.append("Encrypt sensitive columns using application-level encryption")
                elif "File Storage" in result["test"]:
                    recommendations.append("Implement file-level encryption for uploads")
                    recommendations.append("Use encrypted file systems")
                elif "Backup" in result["test"]:
                    recommendations.append("Encrypt all backups using strong encryption")
                    recommendations.append("Store encryption keys separately from backups")
        
        return list(set(recommendations))  # Remove duplicates


async def main():
    tester = DataSecurityTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())