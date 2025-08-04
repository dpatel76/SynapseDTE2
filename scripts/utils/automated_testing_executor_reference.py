#!/usr/bin/env python3
"""
Enhanced Automated Testing Executor for SynapseDT System
Fixed authentication, dependency management, and async handling
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('testing_execution_enhanced.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = None
        self.auth_tokens = {}
        self.token_expiry = {}
        self.test_results = {
            "foundation": {"passed": 0, "failed": 0, "total": 60},
            "role_based": {"passed": 0, "failed": 0, "total": 44},
            "workflow": {"passed": 0, "failed": 0, "total": 147},
            "integration": {"passed": 0, "failed": 0, "total": 27},
            "sla": {"passed": 0, "failed": 0, "total": 21},
            "llm": {"passed": 0, "failed": 0, "total": 33},
            "error_handling": {"passed": 0, "failed": 0, "total": 33}
        }
        self.test_data = {}
        self.retry_count = 3
        self.timeout = 30
        
    async def initialize_session(self):
        """Initialize HTTP session with proper timeout and error handling"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("🚀 Initializing enhanced system testing session")
        
    async def cleanup_session(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            
    async def log_test_result(self, test_id: str, category: str, success: bool, details: str):
        """Log test result and update progress"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_id}: {details}")
        
        if success:
            self.test_results[category]["passed"] += 1
        else:
            self.test_results[category]["failed"] += 1
            
    async def authenticate_user(self, email: str, password: str = "AdminUser123!") -> str:
        """Enhanced authentication with token caching and expiry management"""
        # Check if we have a valid cached token
        if email in self.auth_tokens and email in self.token_expiry:
            if datetime.utcnow() < self.token_expiry[email]:
                return self.auth_tokens[email]
        
        # Use different password for test users
        if email.endswith("@synapse.com"):
            password = "TestUser123!"
            
        auth_data = {"email": email, "password": password}
        
        for attempt in range(self.retry_count):
            try:
                async with self.session.post(f"{self.base_url}/api/v1/auth/login", json=auth_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        token = result.get("access_token")
                        expires_in = result.get("expires_in", 1800)  # Default 30 minutes
                        
                        # Cache token with expiry
                        self.auth_tokens[email] = token
                        self.token_expiry[email] = datetime.utcnow() + timedelta(seconds=expires_in - 60)  # 1 min buffer
                        
                        logger.info(f"🔐 Authenticated user: {email}")
                        return token
                    else:
                        logger.error(f"❌ Authentication failed for {email}: {response.status}")
                        if attempt < self.retry_count - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        return None
            except Exception as e:
                logger.error(f"❌ Authentication error for {email} (attempt {attempt + 1}): {str(e)}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        return None
            
    async def make_api_call(self, method: str, endpoint: str, token: str = None, data: dict = None) -> Dict[str, Any]:
        """Enhanced API call with retry logic and better error handling"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        url = f"{self.base_url}/api/v1{endpoint}"
        
        for attempt in range(self.retry_count):
            try:
                if method.upper() == "GET":
                    async with self.session.get(url, headers=headers) as response:
                        response_data = None
                        try:
                            if response.status < 400:
                                response_data = await response.json()
                        except:
                            pass
                        return {"status": response.status, "data": response_data}
                        
                elif method.upper() == "POST":
                    async with self.session.post(url, headers=headers, json=data) as response:
                        response_data = None
                        try:
                            if response.status < 400:
                                response_data = await response.json()
                        except:
                            pass
                        return {"status": response.status, "data": response_data}
                        
                elif method.upper() == "PUT":
                    async with self.session.put(url, headers=headers, json=data) as response:
                        response_data = None
                        try:
                            if response.status < 400:
                                response_data = await response.json()
                        except:
                            pass
                        return {"status": response.status, "data": response_data}
                        
                elif method.upper() == "DELETE":
                    async with self.session.delete(url, headers=headers) as response:
                        response_data = None
                        try:
                            if response.status < 400:
                                response_data = await response.json()
                        except:
                            pass
                        return {"status": response.status, "data": response_data}
                        
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout on {method} {endpoint} (attempt {attempt + 1})")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {"status": 408, "data": None, "error": "Request timeout"}
                
            except Exception as e:
                logger.error(f"❌ API call error {method} {endpoint} (attempt {attempt + 1}): {str(e)}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {"status": 500, "data": None, "error": str(e)}
        
        return {"status": 500, "data": None, "error": "Max retries exceeded"}
    
    async def setup_test_data(self):
        """Set up required test data for dependent tests"""
        logger.info("🔧 Setting up test data dependencies")
        
        admin_token = await self.authenticate_user("admin@example.com")
        if not admin_token:
            logger.error("❌ Failed to authenticate admin - cannot set up test data")
            return False
        
        # Create test LOB if needed
        lob_data = {"lob_name": f"Enhanced Test LOB {int(time.time())}"}
        lob_result = await self.make_api_call("POST", "/lobs/", admin_token, lob_data)
        if lob_result["status"] in [200, 201] and lob_result["data"]:
            self.test_data["test_lob_id"] = lob_result["data"].get("lob_id")
            logger.info(f"✅ Created test LOB: {self.test_data['test_lob_id']}")
        
        # Create test report if needed
        if "test_lob_id" in self.test_data:
            report_data = {
                "report_name": f"Enhanced Test Report {int(time.time())}",
                "regulation": "Enhanced Test Regulation",
                "report_owner_id": 3,  # Use valid report owner ID
                "lob_id": self.test_data["test_lob_id"],
                "description": "Enhanced test report",
                "frequency": "monthly",
                "is_active": True
            }
            report_result = await self.make_api_call("POST", "/reports/", admin_token, report_data)
            if report_result["status"] in [200, 201] and report_result["data"]:
                self.test_data["test_report_id"] = report_result["data"].get("report_id")
                logger.info(f"✅ Created test report: {self.test_data['test_report_id']}")
        
        # Create test cycle if needed
        cycle_data = {
            "cycle_name": f"Enhanced Test Cycle {int(time.time())}",
            "start_date": "2025-01-15",
            "end_date": "2025-01-30",
            "test_manager_id": 1
        }
        cycle_result = await self.make_api_call("POST", "/cycles/", admin_token, cycle_data)
        if cycle_result["status"] in [200, 201] and cycle_result["data"]:
            self.test_data["test_cycle_id"] = cycle_result["data"].get("cycle_id")
            logger.info(f"✅ Created test cycle: {self.test_data['test_cycle_id']}")
        
        return True

def main():
    """Main execution function"""
    tester = EnhancedSystemTester()
    asyncio.run(tester.run_comprehensive_testing())

if __name__ == "__main__":
    main() 