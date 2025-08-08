#!/usr/bin/env python3
"""
Test Monitoring Script for E2E Workflow Test

This script monitors:
- Backend logs for errors
- Database state changes
- API response times
- Phase state transitions
- Background job progress
- Console errors (if browser automation is used)

Run this in parallel with the E2E test for comprehensive monitoring.
"""

import asyncio
import aiohttp
import json
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import sys

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


class TestMonitor:
    """Comprehensive test monitoring system"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_base = f"{self.base_url}/api/v1"
        self.session = None
        self.monitoring = True
        
        # Monitoring data
        self.api_response_times = []
        self.error_count = 0
        self.phase_transitions = []
        self.background_jobs = {}
        
        # Database connection
        try:
            db_url = settings.database_url.replace('+asyncpg', '')
            self.db_engine = create_engine(db_url)
        except Exception as e:
            print(f"⚠️ Database connection failed: {e}")
            self.db_engine = None
    
    async def setup_session(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    def monitor_backend_logs(self):
        """Monitor backend logs for errors and important events"""
        print("👀 Starting backend log monitoring...")
        
        log_files = [
            "backend.log",
            "logs/backend.log", 
            "app.log"
        ]
        
        active_log_file = None
        for log_file in log_files:
            if Path(log_file).exists():
                active_log_file = log_file
                break
        
        if not active_log_file:
            print("⚠️ No backend log file found")
            return
        
        try:
            # Monitor log file for new entries
            process = subprocess.Popen(
                ['tail', '-f', active_log_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"📄 Monitoring log file: {active_log_file}")
            
            while self.monitoring:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    # Check for important events
                    if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed']):
                        print(f"🚨 [{timestamp}] ERROR: {line}")
                        self.error_count += 1
                    elif any(keyword in line.lower() for keyword in ['warning', 'warn']):
                        print(f"⚠️ [{timestamp}] WARNING: {line}")
                    elif any(keyword in line.lower() for keyword in ['phase', 'workflow', 'transition']):
                        print(f"🔄 [{timestamp}] WORKFLOW: {line}")
                        self.phase_transitions.append({
                            'timestamp': timestamp,
                            'event': line
                        })
                    elif any(keyword in line.lower() for keyword in ['job', 'task', 'background']):
                        print(f"⚙️ [{timestamp}] JOB: {line}")
                    elif 'llm' in line.lower():
                        print(f"🤖 [{timestamp}] LLM: {line}")
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Log monitoring error: {e}")
        finally:
            if 'process' in locals():
                process.terminate()
    
    async def monitor_api_health(self):
        """Monitor API health and response times"""
        print("🌐 Starting API health monitoring...")
        
        while self.monitoring:
            try:
                start_time = time.time()
                
                async with self.session.get(f"{self.api_base}/health") as response:
                    response_time = time.time() - start_time
                    self.api_response_times.append(response_time)
                    
                    if response.status == 200:
                        if len(self.api_response_times) % 20 == 0:  # Log every 20 checks
                            avg_time = sum(self.api_response_times[-20:]) / 20
                            print(f"💓 API Health: OK (avg response: {avg_time:.3f}s)")
                    else:
                        print(f"🚨 API Health: DEGRADED (status: {response.status})")
                
            except Exception as e:
                print(f"❌ API Health check failed: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def monitor_database_state(self):
        """Monitor database state changes during testing"""
        if not self.db_engine:
            return
        
        print("🗄️ Starting database state monitoring...")
        
        # Track key tables
        previous_counts = {}
        
        while self.monitoring:
            try:
                with self.db_engine.connect() as conn:
                    tables_to_monitor = [
                        'test_cycles', 'cycle_reports', 'workflow_phases',
                        'test_executions', 'observations', 'sample_sets',
                        'llm_audit_log', 'audit_log'
                    ]
                    
                    current_counts = {}
                    for table in tables_to_monitor:
                        try:
                            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            current_counts[table] = result.scalar()
                        except Exception:
                            # Table might not exist
                            current_counts[table] = 0
                    
                    # Check for changes
                    for table, count in current_counts.items():
                        if table in previous_counts and count != previous_counts[table]:
                            change = count - previous_counts[table]
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"📊 [{timestamp}] DB CHANGE: {table} {change:+d} rows (total: {count})")
                    
                    previous_counts = current_counts
                
            except Exception as e:
                print(f"❌ Database monitoring error: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def monitor_background_jobs(self):
        """Monitor background job status"""
        print("⚙️ Starting background job monitoring...")
        
        while self.monitoring:
            try:
                async with self.session.get(f"{self.api_base}/jobs/status") as response:
                    if response.status == 200:
                        jobs_data = await response.json()
                        
                        active_jobs = [job for job in jobs_data if job.get('status') in ['running', 'pending']]
                        
                        if active_jobs:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            print(f"⚙️ [{timestamp}] Active jobs: {len(active_jobs)}")
                            
                            for job in active_jobs:
                                job_id = job.get('job_id', 'unknown')
                                job_type = job.get('job_type', 'unknown')
                                status = job.get('status', 'unknown')
                                progress = job.get('progress', 0)
                                
                                print(f"  📋 Job {job_id}: {job_type} - {status} ({progress}%)")
                
            except Exception as e:
                if "Connection refused" not in str(e):
                    print(f"❌ Job monitoring error: {e}")
            
            await asyncio.sleep(15)  # Check every 15 seconds
    
    async def monitor_system_performance(self):
        """Monitor system performance metrics"""
        print("📈 Starting system performance monitoring...")
        
        while self.monitoring:
            try:
                # Check API performance
                if self.api_response_times:
                    recent_times = self.api_response_times[-10:]
                    avg_response_time = sum(recent_times) / len(recent_times)
                    max_response_time = max(recent_times)
                    
                    if avg_response_time > 2.0:  # 2 second threshold
                        print(f"⚠️ Performance warning: Avg response time {avg_response_time:.3f}s")
                    
                    if max_response_time > 5.0:  # 5 second threshold
                        print(f"🚨 Performance alert: Max response time {max_response_time:.3f}s")
                
                # Check error rate
                if self.error_count > 0:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"📊 [{timestamp}] Total errors detected: {self.error_count}")
                
            except Exception as e:
                print(f"❌ Performance monitoring error: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def generate_monitoring_report(self):
        """Generate final monitoring report"""
        print("\n" + "="*60)
        print("📊 MONITORING REPORT")
        print("="*60)
        
        # API Performance
        if self.api_response_times:
            avg_time = sum(self.api_response_times) / len(self.api_response_times)
            max_time = max(self.api_response_times)
            min_time = min(self.api_response_times)
            
            print(f"🌐 API Performance:")
            print(f"   Average response time: {avg_time:.3f}s")
            print(f"   Max response time: {max_time:.3f}s")
            print(f"   Min response time: {min_time:.3f}s")
            print(f"   Total API calls monitored: {len(self.api_response_times)}")
        
        # Error Summary
        print(f"\n🚨 Error Summary:")
        print(f"   Total errors detected: {self.error_count}")
        
        # Phase Transitions
        print(f"\n🔄 Phase Transitions Detected: {len(self.phase_transitions)}")
        for transition in self.phase_transitions[-5:]:  # Show last 5
            print(f"   {transition['timestamp']}: {transition['event'][:80]}...")
        
        # Background Jobs
        print(f"\n⚙️ Background Jobs Monitored: {len(self.background_jobs)}")
        
        print("\n" + "="*60)
    
    async def start_monitoring(self):
        """Start all monitoring tasks"""
        print("🔍 STARTING COMPREHENSIVE TEST MONITORING")
        print("="*60)
        print("Monitoring:")
        print("  - Backend logs for errors and events")
        print("  - API health and response times")
        print("  - Database state changes")
        print("  - Background job progress")
        print("  - System performance metrics")
        print("="*60)
        
        await self.setup_session()
        
        # Start background log monitoring in separate thread
        log_thread = threading.Thread(target=self.monitor_backend_logs)
        log_thread.daemon = True
        log_thread.start()
        
        # Start async monitoring tasks
        tasks = [
            self.monitor_api_health(),
            self.monitor_database_state(),
            self.monitor_background_jobs(),
            self.monitor_system_performance()
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
        finally:
            self.monitoring = False
            await self.cleanup_session()
            self.generate_monitoring_report()


async def main():
    """Main monitoring execution"""
    monitor = TestMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n👋 Monitoring terminated")


if __name__ == "__main__":
    print("🔍 SynapseDTE Test Monitor")
    print("This script monitors system health during E2E testing")
    print("Run this alongside the E2E test for comprehensive monitoring")
    print("\nPress Ctrl+C to stop monitoring")
    print("-" * 60)
    
    asyncio.run(main())