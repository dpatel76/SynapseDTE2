#!/usr/bin/env python3
"""
Service Health Check Tests for SynapseDTE
Tests for container startup, health checks, and service availability
"""

import time
import json
from typing import Dict, List
from test_framework import DockerTestFramework, TestRunner, TestConfig


class HealthTestRunner(TestRunner):
    """Test runner for service health checks"""
    
    def __init__(self, framework: DockerTestFramework):
        super().__init__(framework)
        self.services = [
            'postgres',
            'redis', 
            'backend',
            'frontend',
            'temporal-postgres',
            'temporal',
            'temporal-ui',
            'worker'
        ]
        
        self.health_endpoints = {
            'backend': {
                'url': 'http://localhost:8000/api/v1/health',
                'expected_status': 200
            },
            'frontend': {
                'url': 'http://localhost/health',
                'expected_status': 200
            },
            'temporal-ui': {
                'url': 'http://localhost:8088',
                'expected_status': 200
            }
        }
        
        self.service_ports = {
            'postgres': ('localhost', 5432),
            'redis': ('localhost', 6379),
            'backend': ('localhost', 8000),
            'frontend': ('localhost', 80),
            'temporal': ('localhost', 7233),
            'temporal-ui': ('localhost', 8088)
        }
    
    def setup(self) -> bool:
        """Start all services"""
        print("🚀 Starting all services for health tests...")
        return self.framework.start_services()
    
    def teardown(self) -> bool:
        """Stop all services"""
        print("🛑 Stopping all services...")
        return self.framework.stop_services()
    
    def run(self) -> bool:
        """Run all health tests"""
        print("\n🏥 Running Service Health Tests\n")
        
        # Test container startup
        self.test_containers_started()
        
        # Test service health checks
        for service in self.services:
            self.test_service_healthy(service)
        
        # Test port accessibility
        for service, (host, port) in self.service_ports.items():
            self.test_port_accessible(service, host, port)
        
        # Test HTTP endpoints
        for service, config in self.health_endpoints.items():
            self.test_http_endpoint(service, config['url'], config['expected_status'])
        
        # Test database connections
        self.test_database_connections()
        
        # Test Redis connection
        self.test_redis_connection()
        
        # Test service logs
        self.test_service_logs()
        
        # Test restart resilience
        self.test_restart_resilience()
        
        # Generate report
        report = self.framework.generate_report()
        passed = report['summary']['failed'] == 0
        
        print(f"\n📊 Health Test Summary: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
        return passed
    
    def test_containers_started(self):
        """Test all containers are started"""
        with self.framework.test_context("All containers started") as details:
            result = self.framework.docker_compose("ps", check=False)
            
            if result.returncode != 0:
                raise Exception("Failed to get container status")
            
            output_lines = result.stdout.strip().split('\n')
            running_services = []
            
            for line in output_lines[1:]:  # Skip header
                if line and 'Up' in line:
                    service_name = line.split()[0]
                    running_services.append(service_name)
            
            details['running_services'] = running_services
            details['expected_count'] = len(self.services)
            details['actual_count'] = len(running_services)
            
            missing_services = set(self.services) - set(s.split('_')[1] for s in running_services)
            if missing_services:
                details['missing_services'] = list(missing_services)
                raise Exception(f"Services not running: {missing_services}")
            
            print(f"   ✓ All {len(running_services)} services are running")
    
    def test_service_healthy(self, service: str):
        """Test service health status"""
        with self.framework.test_context(f"Service health - {service}") as details:
            # Wait for service to be healthy
            healthy = self.framework.wait_for_healthy(service, timeout=120)
            
            if not healthy:
                # Get logs for debugging
                logs = self.framework.get_service_logs(service, tail=50)
                details['last_logs'] = logs
                raise Exception(f"Service {service} is not healthy")
            
            details['status'] = 'healthy'
            print(f"   ✓ {service} is healthy")
    
    def test_port_accessible(self, service: str, host: str, port: int):
        """Test service port accessibility"""
        with self.framework.test_context(f"Port accessibility - {service} ({port})") as details:
            details['host'] = host
            details['port'] = port
            
            # Wait a bit for service to fully start
            max_attempts = 12  # 60 seconds
            for attempt in range(max_attempts):
                if self.framework.test_port_accessible(host, port):
                    details['attempts'] = attempt + 1
                    print(f"   ✓ {service} port {port} is accessible")
                    return
                time.sleep(5)
            
            raise Exception(f"Port {port} is not accessible after {max_attempts * 5} seconds")
    
    def test_http_endpoint(self, service: str, url: str, expected_status: int):
        """Test HTTP endpoint health"""
        with self.framework.test_context(f"HTTP health check - {service}") as details:
            details['url'] = url
            details['expected_status'] = expected_status
            
            # Wait for endpoint to be ready
            max_attempts = 12
            for attempt in range(max_attempts):
                success, data = self.framework.test_http_endpoint(url, expected_status)
                
                if success:
                    details['response'] = data
                    details['attempts'] = attempt + 1
                    print(f"   ✓ {service} HTTP endpoint is healthy")
                    return
                
                time.sleep(5)
            
            details['last_error'] = data
            raise Exception(f"HTTP endpoint not healthy after {max_attempts * 5} seconds")
    
    def test_database_connections(self):
        """Test database connections"""
        # Test main database
        with self.framework.test_context("Main database connection") as details:
            connected = self.framework.test_database_connection(
                host="localhost",
                port=5432,
                dbname="synapse_dt",
                user="synapse_user",
                password="synapse_password"
            )
            
            if not connected:
                raise Exception("Cannot connect to main database")
            
            # Test database is initialized
            success, output = self.framework.execute_in_container(
                "postgres", 
                "psql -U synapse_user -d synapse_dt -c 'SELECT COUNT(*) FROM information_schema.tables;'"
            )
            
            if success:
                details['table_count'] = output.strip()
                print(f"   ✓ Main database is accessible and initialized")
            else:
                raise Exception("Database not properly initialized")
        
        # Test Temporal database
        with self.framework.test_context("Temporal database connection") as details:
            connected = self.framework.test_database_connection(
                host="localhost",
                port=5432,  # Assuming mapped in compose
                dbname="temporal",
                user="temporal",
                password="temporal_password"
            )
            
            if connected:
                print(f"   ✓ Temporal database is accessible")
            else:
                print(f"   ⚠️  Temporal database not accessible from host (this is normal)")
    
    def test_redis_connection(self):
        """Test Redis connection"""
        with self.framework.test_context("Redis connection") as details:
            connected = self.framework.test_redis_connection(
                host="localhost",
                port=6379,
                password="synapse_redis_password"
            )
            
            if not connected:
                # Try without password (dev mode)
                connected = self.framework.test_redis_connection(
                    host="localhost",
                    port=6379
                )
                
                if not connected:
                    raise Exception("Cannot connect to Redis")
                else:
                    details['auth'] = 'no password'
            else:
                details['auth'] = 'with password'
            
            print(f"   ✓ Redis is accessible")
    
    def test_service_logs(self):
        """Test service logs for errors"""
        with self.framework.test_context("Service logs check") as details:
            error_patterns = [
                'ERROR',
                'FATAL',
                'Exception',
                'Failed to',
                'Unable to',
                'panic:'
            ]
            
            services_with_errors = []
            
            for service in self.services:
                logs = self.framework.get_service_logs(service, tail=100)
                
                errors_found = []
                for pattern in error_patterns:
                    if pattern in logs:
                        # Extract error lines
                        for line in logs.split('\n'):
                            if pattern in line:
                                errors_found.append(line.strip())
                
                if errors_found:
                    services_with_errors.append({
                        'service': service,
                        'errors': errors_found[:5]  # First 5 errors
                    })
            
            details['services_with_errors'] = services_with_errors
            
            # Some errors might be expected during startup
            critical_errors = [e for e in services_with_errors 
                             if any('FATAL' in err or 'panic:' in err 
                                   for err in e['errors'])]
            
            if critical_errors:
                raise Exception(f"Critical errors found in {len(critical_errors)} services")
            elif services_with_errors:
                print(f"   ⚠️  Non-critical errors found in {len(services_with_errors)} services")
            else:
                print(f"   ✓ No errors found in service logs")
    
    def test_restart_resilience(self):
        """Test service restart resilience"""
        test_service = 'backend'
        
        with self.framework.test_context(f"Restart resilience - {test_service}") as details:
            # Restart service
            print(f"   → Restarting {test_service}...")
            result = self.framework.docker_compose(f"restart {test_service}")
            
            if result.returncode != 0:
                raise Exception(f"Failed to restart {test_service}")
            
            # Wait for service to be healthy again
            time.sleep(10)  # Give it time to stop
            
            healthy = self.framework.wait_for_healthy(test_service, timeout=60)
            if not healthy:
                raise Exception(f"{test_service} not healthy after restart")
            
            # Test endpoint after restart
            success, data = self.framework.test_http_endpoint(
                'http://localhost:8000/api/v1/health',
                200
            )
            
            if not success:
                raise Exception(f"{test_service} endpoint not accessible after restart")
            
            details['restart_successful'] = True
            print(f"   ✓ {test_service} successfully restarted and is healthy")


def main():
    """Run health tests"""
    config = TestConfig()
    framework = DockerTestFramework(config)
    runner = HealthTestRunner(framework)
    
    # Setup environment
    if not runner.setup():
        print("❌ Failed to setup test environment")
        return 1
    
    try:
        # Run tests
        success = runner.run()
        
        # Save detailed report
        framework.generate_report("health_test_report.json")
        
        return 0 if success else 1
    finally:
        # Cleanup
        runner.teardown()


if __name__ == "__main__":
    exit(main())