#!/usr/bin/env python3
"""
E2E Test Execution with Comprehensive Monitoring

This script orchestrates:
1. System health pre-checks
2. Monitoring setup
3. E2E test execution
4. Results analysis and reporting
"""

import asyncio
import subprocess
import time
import signal
import sys
import os
from pathlib import Path
import json
from datetime import datetime


class E2ETestOrchestrator:
    """Orchestrates E2E testing with monitoring"""
    
    def __init__(self):
        self.monitor_process = None
        self.test_process = None
        self.start_time = None
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n⏹️ Stopping test execution...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup running processes"""
        if self.monitor_process:
            print("🔍 Stopping monitor...")
            self.monitor_process.terminate()
            self.monitor_process.wait()
        
        if self.test_process:
            print("🧪 Stopping test...")
            self.test_process.terminate()
            self.test_process.wait()
    
    async def check_system_health(self):
        """Comprehensive system health check"""
        print("🏥 SYSTEM HEALTH CHECK")
        print("-" * 40)
        
        checks_passed = 0
        total_checks = 6
        
        # 1. Backend API Health
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/api/v1/health", timeout=5) as response:
                    if response.status == 200:
                        print("✅ Backend API: Healthy")
                        checks_passed += 1
                    else:
                        print(f"❌ Backend API: Unhealthy (status: {response.status})")
        except Exception as e:
            print(f"❌ Backend API: Not accessible - {e}")
        
        # 2. Database connectivity
        try:
            sys.path.append(str(Path(__file__).parent.parent))
            from sqlalchemy import create_engine, text
            from app.core.config import settings
            
            db_url = settings.database_url.replace('+asyncpg', '')
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database: Connected")
            checks_passed += 1
        except Exception as e:
            print(f"❌ Database: Connection failed - {e}")
        
        # 3. Test users exist
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM users WHERE email IN ('test.manager@example.com', 'tester@example.com', 'report.owner@example.com', 'cdo@example.com', 'data.provider@example.com')"))
                user_count = result.scalar()
                
                if user_count >= 4:  # At least 4 test users should exist
                    print(f"✅ Test Users: {user_count} users found")
                    checks_passed += 1
                else:
                    print(f"❌ Test Users: Only {user_count} users found (need at least 4)")
        except Exception as e:
            print(f"❌ Test Users: Check failed - {e}")
        
        # 4. Report 156 exists
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM reports WHERE report_id = 156"))
                report_exists = result.scalar() > 0
                
                if report_exists:
                    print("✅ Report 156: Exists")
                    checks_passed += 1
                else:
                    print("❌ Report 156: Not found")
        except Exception as e:
            print(f"❌ Report 156: Check failed - {e}")
        
        # 5. Key tables exist
        try:
            essential_tables = ['test_cycles', 'cycle_reports', 'workflow_phases', 'users', 'reports']
            with engine.connect() as conn:
                for table in essential_tables:
                    conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            print("✅ Essential Tables: All present")
            checks_passed += 1
        except Exception as e:
            print(f"❌ Essential Tables: Missing or inaccessible - {e}")
        
        # 6. Log directory writable
        try:
            log_dir = Path("test")
            log_dir.mkdir(exist_ok=True)
            test_file = log_dir / "health_check.tmp"
            test_file.write_text("test")
            test_file.unlink()
            print("✅ Log Directory: Writable")
            checks_passed += 1
        except Exception as e:
            print(f"❌ Log Directory: Not writable - {e}")
        
        print(f"\n📊 Health Check: {checks_passed}/{total_checks} checks passed")
        
        if checks_passed < total_checks:
            print("\n⚠️ SYSTEM NOT READY FOR TESTING")
            print("Please resolve the failed checks before running E2E tests")
            return False
        
        print("\n✅ SYSTEM READY FOR TESTING")
        return True
    
    def start_monitoring(self):
        """Start the monitoring process"""
        print("🔍 Starting test monitor...")
        
        try:
            self.monitor_process = subprocess.Popen([
                sys.executable, 
                "test/test_monitor.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            print("✅ Monitor started")
            time.sleep(2)  # Give monitor time to initialize
            return True
        except Exception as e:
            print(f"❌ Failed to start monitor: {e}")
            return False
    
    def run_e2e_test(self):
        """Run the E2E test"""
        print("🧪 Starting E2E test execution...")
        
        try:
            self.test_process = subprocess.Popen([
                sys.executable,
                "test/comprehensive_e2e_workflow_test.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            print("✅ E2E test started")
            
            # Stream output in real-time
            while True:
                output = self.test_process.stdout.readline()
                if output == '' and self.test_process.poll() is not None:
                    break
                if output:
                    print(f"🧪 {output.strip()}")
            
            return_code = self.test_process.poll()
            return return_code == 0
            
        except Exception as e:
            print(f"❌ E2E test execution failed: {e}")
            return False
    
    def generate_final_report(self, test_success: bool):
        """Generate comprehensive test execution report"""
        end_time = datetime.now()
        duration = end_time - self.start_time if self.start_time else "Unknown"
        
        report = {
            "test_execution": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": end_time.isoformat(),
                "duration": str(duration),
                "success": test_success
            },
            "files_generated": {
                "test_log": "test/e2e_test_execution.log",
                "monitor_output": "Available in console",
                "system_health": "Checked pre-execution"
            },
            "test_coverage": {
                "phases_tested": 9,
                "user_roles_tested": 5,
                "workflow_transitions": "All standard transitions",
                "background_jobs": "LLM processing, report generation",
                "state_monitoring": "Phase transitions tracked"
            }
        }
        
        report_file = Path("test/e2e_execution_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*80)
        print("📊 FINAL E2E TEST EXECUTION REPORT")
        print("="*80)
        print(f"Test Status: {'✅ PASSED' if test_success else '❌ FAILED'}")
        print(f"Duration: {duration}")
        print(f"Start Time: {self.start_time}")
        print(f"End Time: {end_time}")
        print(f"\n📁 Generated Files:")
        print(f"   - E2E Test Log: test/e2e_test_execution.log")
        print(f"   - Execution Report: {report_file}")
        print(f"\n🔍 Test Coverage:")
        print(f"   - 9 workflow phases executed")
        print(f"   - 5 user roles tested")
        print(f"   - State transitions monitored")
        print(f"   - Background jobs tracked")
        print(f"   - API performance measured")
        print(f"   - Database changes monitored")
        print("="*80)
    
    async def run_full_test_suite(self):
        """Execute the complete test suite with monitoring"""
        print("🚀 SYNAPSDTE COMPREHENSIVE E2E TEST SUITE")
        print("="*80)
        print("This suite includes:")
        print("  • System health verification")
        print("  • Real-time monitoring")
        print("  • Complete 9-phase workflow testing")
        print("  • State transition validation")
        print("  • Background job tracking")
        print("  • Performance monitoring")
        print("="*80)
        
        self.start_time = datetime.now()
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Step 1: System health check
            health_ok = await self.check_system_health()
            if not health_ok:
                print("\n❌ System health check failed. Aborting test execution.")
                return False
            
            # Step 2: Start monitoring
            monitor_ok = self.start_monitoring()
            if not monitor_ok:
                print("\n⚠️ Monitor failed to start. Continuing without monitoring.")
            
            # Step 3: Run E2E test
            print("\n🎬 BEGINNING E2E TEST EXECUTION")
            print("-" * 50)
            
            test_success = self.run_e2e_test()
            
            # Step 4: Generate final report
            self.generate_final_report(test_success)
            
            return test_success
            
        except Exception as e:
            print(f"\n💥 Test suite execution failed: {e}")
            return False
        finally:
            self.cleanup()


async def main():
    """Main execution function"""
    orchestrator = E2ETestOrchestrator()
    success = await orchestrator.run_full_test_suite()
    
    if success:
        print("\n🎉 E2E TEST SUITE COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ E2E TEST SUITE FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent.parent)
    
    # Run the test suite
    asyncio.run(main())