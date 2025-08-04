#!/usr/bin/env python3
"""
Master Test Runner for SynapseDTE Docker Tests
Orchestrates running all test suites and generates a comprehensive report
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Optional


class MasterTestRunner:
    """Orchestrates all Docker test suites"""
    
    def __init__(self, args):
        self.args = args
        self.start_time = None
        self.test_suites = [
            {
                'name': 'Build Tests',
                'script': 'test_build.py',
                'description': 'Container build validation and security scanning',
                'required': True
            },
            {
                'name': 'Health Tests',
                'script': 'test_health.py',
                'description': 'Service health checks and startup validation',
                'required': True
            },
            {
                'name': 'Integration Tests',
                'script': 'test_integration.py',
                'description': 'Inter-service communication and API testing',
                'required': True
            },
            {
                'name': 'E2E Tests',
                'script': 'test_e2e.py',
                'description': 'End-to-end application workflows',
                'required': False
            },
            {
                'name': 'Performance Tests',
                'script': 'test_performance.py',
                'description': 'Performance baselines and load testing',
                'required': False
            }
        ]
        self.results = {}
    
    def run(self) -> int:
        """Run all test suites"""
        self.start_time = time.time()
        
        print("="*60)
        print("🚀 SynapseDTE Docker Test Suite")
        print("="*60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test mode: {'Quick' if self.args.quick else 'Full'}")
        print(f"Keep containers: {self.args.keep_containers}")
        print("="*60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return 1
        
        # Build containers if requested
        if self.args.build:
            if not self.build_containers():
                return 1
        
        # Run test suites
        failed_suites = []
        skipped_suites = []
        
        for suite in self.test_suites:
            # Skip non-required tests in quick mode
            if self.args.quick and not suite['required']:
                skipped_suites.append(suite['name'])
                continue
            
            # Skip specific suites if requested
            if self.args.skip and suite['script'].replace('test_', '').replace('.py', '') in self.args.skip:
                skipped_suites.append(suite['name'])
                continue
            
            # Run only specific suites if requested
            if self.args.only:
                test_name = suite['script'].replace('test_', '').replace('.py', '')
                if test_name not in self.args.only:
                    skipped_suites.append(suite['name'])
                    continue
            
            print(f"\n{'='*60}")
            print(f"📋 Running {suite['name']}")
            print(f"   {suite['description']}")
            print("="*60)
            
            success = self.run_test_suite(suite)
            if not success:
                failed_suites.append(suite['name'])
                if self.args.fail_fast:
                    print("\n❌ Fail-fast enabled, stopping test execution")
                    break
        
        # Generate final report
        self.generate_final_report(failed_suites, skipped_suites)
        
        # Cleanup if requested
        if not self.args.keep_containers:
            self.cleanup_containers()
        
        # Return appropriate exit code
        return 0 if len(failed_suites) == 0 else 1
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("\n🔍 Checking prerequisites...")
        
        checks = [
            ('Docker', 'docker --version'),
            ('Docker Compose', 'docker-compose --version'),
            ('Python packages', 'python -c "import docker, psycopg2, redis, requests"')
        ]
        
        all_ok = True
        for name, command in checks:
            result = subprocess.run(command, shell=True, capture_output=True)
            if result.returncode == 0:
                print(f"   ✓ {name}")
            else:
                print(f"   ❌ {name} - not found or not working")
                all_ok = False
        
        # Check Docker daemon
        result = subprocess.run("docker ps", shell=True, capture_output=True)
        if result.returncode == 0:
            print("   ✓ Docker daemon running")
        else:
            print("   ❌ Docker daemon not running")
            all_ok = False
        
        # Check available resources
        if self.args.check_resources:
            self.check_system_resources()
        
        return all_ok
    
    def check_system_resources(self):
        """Check system resources"""
        print("\n📊 System resources:")
        
        # Docker info
        result = subprocess.run("docker system df", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        
        # Memory info (macOS/Linux)
        if sys.platform == "darwin":
            result = subprocess.run("vm_stat | grep 'Pages free'", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   Memory: {result.stdout.strip()}")
        elif sys.platform.startswith("linux"):
            result = subprocess.run("free -h | grep Mem", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   Memory: {result.stdout.strip()}")
    
    def build_containers(self) -> bool:
        """Build all containers"""
        print("\n🔨 Building containers...")
        
        build_commands = [
            ("Backend", "docker build -f Dockerfile.backend -t synapse-backend:test ."),
            ("Frontend", "docker build -f Dockerfile.frontend -t synapse-frontend:test ."),
            ("Worker", "docker build -f Dockerfile.worker -t synapse-worker:test .")
        ]
        
        for name, command in build_commands:
            print(f"\n   Building {name}...")
            result = subprocess.run(command, shell=True)
            if result.returncode != 0:
                print(f"   ❌ Failed to build {name}")
                return False
            print(f"   ✓ {name} built successfully")
        
        return True
    
    def run_test_suite(self, suite: Dict) -> bool:
        """Run a single test suite"""
        test_start = time.time()
        
        # Prepare command
        cmd = f"python {suite['script']}"
        if self.args.verbose:
            cmd += " --verbose"
        
        # Run test
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        test_duration = time.time() - test_start
        
        # Store result
        self.results[suite['name']] = {
            'success': result.returncode == 0,
            'duration': test_duration,
            'exit_code': result.returncode
        }
        
        # Load detailed report if available
        report_file = suite['script'].replace('.py', '_report.json')
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                self.results[suite['name']]['detailed_report'] = json.load(f)
        
        if result.returncode == 0:
            print(f"\n✅ {suite['name']} completed successfully ({test_duration:.2f}s)")
        else:
            print(f"\n❌ {suite['name']} failed with exit code {result.returncode}")
        
        return result.returncode == 0
    
    def generate_final_report(self, failed_suites: List[str], skipped_suites: List[str]):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("📊 FINAL TEST REPORT")
        print("="*60)
        
        # Summary
        total_suites = len(self.test_suites)
        run_suites = len(self.results)
        passed_suites = sum(1 for r in self.results.values() if r['success'])
        
        print(f"\n📈 Summary:")
        print(f"   Total test suites: {total_suites}")
        print(f"   Suites run: {run_suites}")
        print(f"   Suites passed: {passed_suites}")
        print(f"   Suites failed: {len(failed_suites)}")
        print(f"   Suites skipped: {len(skipped_suites)}")
        print(f"   Total duration: {total_duration:.2f}s")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for suite_name, result in self.results.items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"\n   {suite_name}: {status}")
            print(f"      Duration: {result['duration']:.2f}s")
            
            if 'detailed_report' in result:
                report = result['detailed_report']
                if 'summary' in report:
                    summary = report['summary']
                    print(f"      Tests run: {summary.get('total_tests', 'N/A')}")
                    print(f"      Tests passed: {summary.get('passed', 'N/A')}")
                    print(f"      Tests failed: {summary.get('failed', 'N/A')}")
        
        # Failed suites
        if failed_suites:
            print(f"\n❌ Failed Suites:")
            for suite in failed_suites:
                print(f"   - {suite}")
        
        # Skipped suites
        if skipped_suites:
            print(f"\n⏭️  Skipped Suites:")
            for suite in skipped_suites:
                print(f"   - {suite}")
        
        # Save comprehensive report
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': total_duration,
            'summary': {
                'total_suites': total_suites,
                'run_suites': run_suites,
                'passed_suites': passed_suites,
                'failed_suites': len(failed_suites),
                'skipped_suites': len(skipped_suites)
            },
            'suite_results': self.results,
            'failed_suites': failed_suites,
            'skipped_suites': skipped_suites,
            'test_configuration': {
                'quick_mode': self.args.quick,
                'fail_fast': self.args.fail_fast,
                'keep_containers': self.args.keep_containers,
                'build_containers': self.args.build
            }
        }
        
        with open('final_test_report.json', 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: final_test_report.json")
        
        # Overall result
        print("\n" + "="*60)
        if len(failed_suites) == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"❌ TESTS FAILED - {len(failed_suites)} suite(s) failed")
        print("="*60)
    
    def cleanup_containers(self):
        """Clean up Docker containers and volumes"""
        print("\n🧹 Cleaning up containers...")
        
        commands = [
            "docker-compose -p synapse-test down -v",
            "docker system prune -f"
        ]
        
        for cmd in commands:
            subprocess.run(cmd, shell=True, capture_output=True)
        
        print("   ✓ Cleanup completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run SynapseDTE Docker test suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_all_tests.py
  
  # Run only required tests (quick mode)
  python run_all_tests.py --quick
  
  # Run specific test suites
  python run_all_tests.py --only integration e2e
  
  # Skip specific test suites
  python run_all_tests.py --skip performance
  
  # Build containers before testing
  python run_all_tests.py --build
  
  # Keep containers running after tests
  python run_all_tests.py --keep-containers
  
  # Stop on first failure
  python run_all_tests.py --fail-fast
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                        help='Run only required tests (build, health, integration)')
    parser.add_argument('--build', action='store_true',
                        help='Build containers before running tests')
    parser.add_argument('--keep-containers', action='store_true',
                        help='Keep containers running after tests')
    parser.add_argument('--fail-fast', action='store_true',
                        help='Stop on first test suite failure')
    parser.add_argument('--only', nargs='+', choices=['build', 'health', 'integration', 'e2e', 'performance'],
                        help='Run only specified test suites')
    parser.add_argument('--skip', nargs='+', choices=['build', 'health', 'integration', 'e2e', 'performance'],
                        help='Skip specified test suites')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--check-resources', action='store_true',
                        help='Check system resources before running')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.only and args.skip:
        print("❌ Cannot use --only and --skip together")
        return 1
    
    # Run tests
    runner = MasterTestRunner(args)
    return runner.run()


if __name__ == "__main__":
    exit(main())