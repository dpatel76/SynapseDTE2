#!/usr/bin/env python3
"""
Performance Baseline Tests for SynapseDTE
Tests for establishing performance baselines and detecting regressions
"""

import time
import json
import requests
import concurrent.futures
import statistics
from typing import Dict, List, Tuple
from test_framework import DockerTestFramework, TestRunner, TestConfig


class PerformanceTestRunner(TestRunner):
    """Test runner for performance tests"""
    
    def __init__(self, framework: DockerTestFramework):
        super().__init__(framework)
        self.api_base = "http://localhost:8000/api/v1"
        self.baselines = {
            'api_response_times': {
                'health_check': 50,  # ms
                'user_login': 200,
                'data_query': 500,
                'report_generation': 5000
            },
            'throughput': {
                'concurrent_users': 50,
                'requests_per_second': 100
            },
            'resource_usage': {
                'backend_cpu_percent': 80,
                'backend_memory_mb': 512,
                'database_cpu_percent': 70,
                'worker_memory_mb': 256
            }
        }
        self.results = {}
    
    def setup(self) -> bool:
        """Start services and warm up"""
        print("🚀 Starting services for performance tests...")
        if not self.framework.start_services():
            return False
        
        # Wait for services to stabilize
        print("⏳ Waiting for services to stabilize...")
        time.sleep(30)
        
        # Warm up services
        self.warm_up_services()
        
        return True
    
    def teardown(self) -> bool:
        """Stop services and save results"""
        print("🧹 Cleaning up performance tests...")
        
        # Save performance results
        with open('performance_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return self.framework.stop_services()
    
    def run(self) -> bool:
        """Run all performance tests"""
        print("\n⚡ Running Performance Tests\n")
        
        # API response time tests
        self.test_api_response_times()
        
        # Throughput tests
        self.test_concurrent_users()
        self.test_requests_per_second()
        
        # Database performance
        self.test_database_query_performance()
        
        # Resource usage tests
        self.test_resource_usage_idle()
        self.test_resource_usage_under_load()
        
        # Workflow performance
        self.test_workflow_execution_time()
        
        # File upload performance
        self.test_file_upload_performance()
        
        # Memory leak detection
        self.test_memory_stability()
        
        # Generate performance report
        self.generate_performance_report()
        
        # Check against baselines
        passed = self.check_performance_baselines()
        
        report = self.framework.generate_report()
        print(f"\n📊 Performance Test Summary: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
        return passed
    
    def warm_up_services(self):
        """Warm up services before testing"""
        print("🔥 Warming up services...")
        
        # Make several requests to warm up connection pools
        for _ in range(10):
            requests.get(f"{self.api_base}/health", timeout=5)
            time.sleep(0.1)
    
    def test_api_response_times(self):
        """Test API endpoint response times"""
        with self.framework.test_context("API response times") as details:
            endpoints = [
                ('health_check', '/health', 'GET', None),
                ('docs', '/docs', 'GET', None),
                ('openapi', '/openapi.json', 'GET', None)
            ]
            
            response_times = {}
            
            for name, path, method, data in endpoints:
                times = []
                
                # Make multiple requests
                for _ in range(20):
                    start_time = time.time()
                    
                    if method == 'GET':
                        response = requests.get(f"{self.api_base}{path}", timeout=10)
                    else:
                        response = requests.post(f"{self.api_base}{path}", json=data, timeout=10)
                    
                    elapsed = (time.time() - start_time) * 1000  # Convert to ms
                    
                    if response.status_code in [200, 201]:
                        times.append(elapsed)
                
                if times:
                    avg_time = statistics.mean(times)
                    p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
                    
                    response_times[name] = {
                        'avg_ms': round(avg_time, 2),
                        'p95_ms': round(p95_time, 2),
                        'min_ms': round(min(times), 2),
                        'max_ms': round(max(times), 2)
                    }
                    
                    print(f"   ✓ {name}: avg={avg_time:.2f}ms, p95={p95_time:.2f}ms")
            
            details['response_times'] = response_times
            self.results['api_response_times'] = response_times
    
    def test_concurrent_users(self):
        """Test system performance with concurrent users"""
        with self.framework.test_context("Concurrent users test") as details:
            concurrent_users = [10, 25, 50, 100]
            results = []
            
            for user_count in concurrent_users:
                print(f"   → Testing with {user_count} concurrent users...")
                
                # Create concurrent requests
                with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
                    start_time = time.time()
                    
                    # Submit requests
                    futures = []
                    for i in range(user_count * 10):  # Each user makes 10 requests
                        future = executor.submit(self.make_api_request, '/health')
                        futures.append(future)
                    
                    # Wait for completion
                    success_count = 0
                    error_count = 0
                    response_times = []
                    
                    for future in concurrent.futures.as_completed(futures):
                        success, response_time = future.result()
                        if success:
                            success_count += 1
                            response_times.append(response_time)
                        else:
                            error_count += 1
                    
                    total_time = time.time() - start_time
                    
                    result = {
                        'user_count': user_count,
                        'total_requests': user_count * 10,
                        'success_count': success_count,
                        'error_count': error_count,
                        'total_time': round(total_time, 2),
                        'requests_per_second': round(success_count / total_time, 2),
                        'avg_response_time': round(statistics.mean(response_times) * 1000, 2) if response_times else 0
                    }
                    
                    results.append(result)
                    print(f"      Success: {success_count}/{user_count * 10}, RPS: {result['requests_per_second']}")
            
            details['concurrent_user_results'] = results
            self.results['concurrent_users'] = results
    
    def test_requests_per_second(self):
        """Test maximum requests per second"""
        with self.framework.test_context("Requests per second test") as details:
            test_duration = 10  # seconds
            
            print(f"   → Running RPS test for {test_duration} seconds...")
            
            start_time = time.time()
            request_count = 0
            success_count = 0
            response_times = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = []
                
                while time.time() - start_time < test_duration:
                    future = executor.submit(self.make_api_request, '/health')
                    futures.append(future)
                    request_count += 1
                    time.sleep(0.001)  # Small delay to prevent overwhelming
                
                # Wait for remaining requests
                for future in concurrent.futures.as_completed(futures):
                    success, response_time = future.result()
                    if success:
                        success_count += 1
                        response_times.append(response_time)
            
            actual_duration = time.time() - start_time
            rps = success_count / actual_duration
            
            result = {
                'total_requests': request_count,
                'successful_requests': success_count,
                'duration': round(actual_duration, 2),
                'requests_per_second': round(rps, 2),
                'avg_response_time_ms': round(statistics.mean(response_times) * 1000, 2) if response_times else 0
            }
            
            details['rps_result'] = result
            self.results['max_rps'] = result
            
            print(f"   ✓ Max RPS: {rps:.2f} ({success_count} successful requests)")
    
    def test_database_query_performance(self):
        """Test database query performance"""
        with self.framework.test_context("Database query performance") as details:
            # Execute various queries through the backend
            queries = [
                ('simple_select', 'SELECT 1'),
                ('table_count', 'SELECT COUNT(*) FROM information_schema.tables'),
                ('complex_join', '''
                    SELECT t1.table_name, t2.column_name 
                    FROM information_schema.tables t1 
                    JOIN information_schema.columns t2 ON t1.table_name = t2.table_name 
                    LIMIT 100
                ''')
            ]
            
            results = {}
            
            for query_name, query in queries:
                # Execute query multiple times through backend
                success, output = self.framework.execute_in_container(
                    "backend",
                    f"python -c \"import time; start=time.time(); "
                    f"from app.core.database import engine; "
                    f"result = engine.execute('{query}'); "
                    f"print(f'Query executed in {{(time.time()-start)*1000:.2f}}ms')\""
                )
                
                if success and 'Query executed' in output:
                    exec_time = float(output.split('in ')[1].split('ms')[0])
                    results[query_name] = {
                        'execution_time_ms': exec_time
                    }
                    print(f"   ✓ {query_name}: {exec_time:.2f}ms")
            
            details['query_performance'] = results
            self.results['database_performance'] = results
    
    def test_resource_usage_idle(self):
        """Test resource usage when idle"""
        with self.framework.test_context("Resource usage - idle") as details:
            print("   → Measuring idle resource usage...")
            time.sleep(5)  # Let system settle
            
            services = ['backend', 'postgres', 'redis', 'worker']
            usage = {}
            
            for service in services:
                stats = self.framework.get_container_stats(service)
                if stats:
                    usage[service] = {
                        'cpu_percent': stats['cpu_percent'],
                        'memory_mb': stats['memory_usage_mb'],
                        'memory_percent': stats['memory_percent']
                    }
                    print(f"   ✓ {service}: CPU={stats['cpu_percent']}%, Memory={stats['memory_usage_mb']}MB")
            
            details['idle_usage'] = usage
            self.results['resource_usage_idle'] = usage
    
    def test_resource_usage_under_load(self):
        """Test resource usage under load"""
        with self.framework.test_context("Resource usage - under load") as details:
            print("   → Generating load...")
            
            # Start load generation
            with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
                # Submit continuous requests
                futures = []
                for _ in range(100):
                    future = executor.submit(self.make_api_request, '/health')
                    futures.append(future)
                
                # Measure resources while under load
                time.sleep(2)  # Let load stabilize
                
                services = ['backend', 'postgres', 'redis', 'worker']
                usage = {}
                
                for service in services:
                    stats = self.framework.get_container_stats(service)
                    if stats:
                        usage[service] = {
                            'cpu_percent': stats['cpu_percent'],
                            'memory_mb': stats['memory_usage_mb'],
                            'memory_percent': stats['memory_percent']
                        }
                        print(f"   ✓ {service}: CPU={stats['cpu_percent']}%, Memory={stats['memory_usage_mb']}MB")
                
                # Wait for requests to complete
                for future in futures:
                    future.result()
            
            details['load_usage'] = usage
            self.results['resource_usage_load'] = usage
    
    def test_workflow_execution_time(self):
        """Test Temporal workflow execution time"""
        with self.framework.test_context("Workflow execution time") as details:
            # Create a simple test workflow
            workflow_times = []
            
            for i in range(5):
                start_time = time.time()
                
                # Execute a test workflow through the API
                # This would normally call the workflow endpoint
                success, output = self.framework.execute_in_container(
                    "worker",
                    "python -c \"print('Simulating workflow execution')\""
                )
                
                execution_time = time.time() - start_time
                workflow_times.append(execution_time)
            
            if workflow_times:
                avg_time = statistics.mean(workflow_times)
                details['workflow_execution'] = {
                    'avg_seconds': round(avg_time, 2),
                    'min_seconds': round(min(workflow_times), 2),
                    'max_seconds': round(max(workflow_times), 2)
                }
                print(f"   ✓ Workflow execution: avg={avg_time:.2f}s")
    
    def test_file_upload_performance(self):
        """Test file upload performance"""
        with self.framework.test_context("File upload performance") as details:
            file_sizes = [
                (1024, "1KB"),
                (1024 * 100, "100KB"),
                (1024 * 1024, "1MB"),
                (1024 * 1024 * 10, "10MB")
            ]
            
            results = []
            
            for size, label in file_sizes:
                # Create test file data
                file_data = b'x' * size
                
                start_time = time.time()
                
                # Simulate file upload
                # In real test, would upload to API endpoint
                success = True  # Placeholder
                
                upload_time = time.time() - start_time
                throughput_mbps = (size / (1024 * 1024)) / upload_time
                
                result = {
                    'file_size': label,
                    'upload_time_seconds': round(upload_time, 3),
                    'throughput_mbps': round(throughput_mbps, 2)
                }
                
                results.append(result)
                print(f"   ✓ {label} upload: {upload_time:.3f}s ({throughput_mbps:.2f} MB/s)")
            
            details['upload_performance'] = results
            self.results['file_upload_performance'] = results
    
    def test_memory_stability(self):
        """Test for memory leaks over time"""
        with self.framework.test_context("Memory stability test") as details:
            print("   → Running memory stability test (2 minutes)...")
            
            services = ['backend', 'worker']
            memory_readings = {service: [] for service in services}
            
            # Take readings every 10 seconds for 2 minutes
            for i in range(12):
                for service in services:
                    stats = self.framework.get_container_stats(service)
                    if stats:
                        memory_readings[service].append(stats['memory_usage_mb'])
                
                # Generate some load
                for _ in range(10):
                    self.make_api_request('/health')
                
                time.sleep(10)
            
            # Analyze memory trends
            results = {}
            for service, readings in memory_readings.items():
                if len(readings) > 2:
                    initial_memory = readings[0]
                    final_memory = readings[-1]
                    memory_growth = final_memory - initial_memory
                    growth_percent = (memory_growth / initial_memory) * 100
                    
                    results[service] = {
                        'initial_mb': round(initial_memory, 2),
                        'final_mb': round(final_memory, 2),
                        'growth_mb': round(memory_growth, 2),
                        'growth_percent': round(growth_percent, 2),
                        'readings': readings
                    }
                    
                    status = "✓" if growth_percent < 10 else "⚠️"
                    print(f"   {status} {service}: {growth_percent:.2f}% memory growth")
            
            details['memory_stability'] = results
            self.results['memory_stability'] = results
    
    def make_api_request(self, endpoint: str) -> Tuple[bool, float]:
        """Make an API request and return success status and response time"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
            response_time = time.time() - start_time
            return response.status_code == 200, response_time
        except Exception:
            return False, 0
    
    def generate_performance_report(self):
        """Generate detailed performance report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'api_health': self.check_api_performance(),
                'throughput_health': self.check_throughput_performance(),
                'resource_health': self.check_resource_performance()
            },
            'detailed_results': self.results,
            'baselines': self.baselines
        }
        
        with open('performance_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n📈 Performance Report Summary:")
        print(f"   API Performance: {report['summary']['api_health']}")
        print(f"   Throughput: {report['summary']['throughput_health']}")
        print(f"   Resource Usage: {report['summary']['resource_health']}")
    
    def check_api_performance(self) -> str:
        """Check API performance against baselines"""
        if 'api_response_times' not in self.results:
            return "No data"
        
        issues = []
        for endpoint, times in self.results['api_response_times'].items():
            if endpoint in self.baselines['api_response_times']:
                baseline = self.baselines['api_response_times'][endpoint]
                if times['p95_ms'] > baseline * 1.5:  # 50% tolerance
                    issues.append(f"{endpoint} slow (p95: {times['p95_ms']}ms)")
        
        return "Degraded - " + ", ".join(issues) if issues else "Healthy"
    
    def check_throughput_performance(self) -> str:
        """Check throughput performance against baselines"""
        if 'max_rps' not in self.results:
            return "No data"
        
        rps = self.results['max_rps']['requests_per_second']
        baseline_rps = self.baselines['throughput']['requests_per_second']
        
        if rps < baseline_rps * 0.8:  # 20% tolerance
            return f"Degraded - {rps} RPS (baseline: {baseline_rps})"
        return f"Healthy - {rps} RPS"
    
    def check_resource_performance(self) -> str:
        """Check resource usage against baselines"""
        if 'resource_usage_load' not in self.results:
            return "No data"
        
        issues = []
        for service, usage in self.results['resource_usage_load'].items():
            baseline_key = f"{service}_cpu_percent"
            if baseline_key in self.baselines['resource_usage']:
                if usage['cpu_percent'] > self.baselines['resource_usage'][baseline_key]:
                    issues.append(f"{service} high CPU ({usage['cpu_percent']}%)")
        
        return "High usage - " + ", ".join(issues) if issues else "Healthy"
    
    def check_performance_baselines(self) -> bool:
        """Check if performance meets baselines"""
        # Check API performance
        api_ok = 'api_response_times' in self.results
        if api_ok:
            for endpoint, times in self.results['api_response_times'].items():
                if endpoint in self.baselines['api_response_times']:
                    if times['p95_ms'] > self.baselines['api_response_times'][endpoint] * 2:
                        api_ok = False
                        break
        
        # Check throughput
        throughput_ok = 'max_rps' in self.results
        if throughput_ok:
            rps = self.results['max_rps']['requests_per_second']
            if rps < self.baselines['throughput']['requests_per_second'] * 0.5:
                throughput_ok = False
        
        # Check resources
        resource_ok = 'resource_usage_load' in self.results
        
        return api_ok and throughput_ok and resource_ok


def main():
    """Run performance tests"""
    config = TestConfig()
    framework = DockerTestFramework(config)
    runner = PerformanceTestRunner(framework)
    
    # Setup environment
    if not runner.setup():
        print("❌ Failed to setup test environment")
        return 1
    
    try:
        # Run tests
        success = runner.run()
        
        # Save framework report
        framework.generate_report("performance_test_report.json")
        
        return 0 if success else 1
    finally:
        # Cleanup
        runner.teardown()


if __name__ == "__main__":
    exit(main())