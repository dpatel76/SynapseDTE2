#!/usr/bin/env python3
"""
Docker Testing Framework for SynapseDTE
Base classes and utilities for container testing
"""

import os
import sys
import time
import json
import subprocess
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import docker
import psycopg2
import redis
from contextlib import contextmanager


@dataclass
class TestConfig:
    """Test configuration"""
    compose_file: str = "docker-compose.yml"
    compose_override: str = ""
    project_name: str = "synapse-test"
    startup_timeout: int = 300  # 5 minutes
    health_check_interval: int = 5
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:80"
    temporal_url: str = "http://localhost:8088"
    

class DockerTestFramework:
    """Base framework for Docker testing"""
    
    def __init__(self, config: TestConfig = None):
        self.config = config or TestConfig()
        self.docker_client = docker.from_env()
        self.start_time = None
        self.test_results = []
        
    def run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command"""
        return subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
    
    def docker_compose(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run docker-compose command"""
        compose_cmd = f"docker-compose -p {self.config.project_name}"
        if self.config.compose_file:
            compose_cmd += f" -f {self.config.compose_file}"
        if self.config.compose_override:
            compose_cmd += f" -f {self.config.compose_override}"
        
        full_command = f"{compose_cmd} {command}"
        return self.run_command(full_command, check)
    
    def start_services(self, services: List[str] = None) -> bool:
        """Start Docker services"""
        print("🚀 Starting Docker services...")
        self.start_time = time.time()
        
        services_str = " ".join(services) if services else ""
        result = self.docker_compose(f"up -d {services_str}")
        
        if result.returncode != 0:
            print(f"❌ Failed to start services: {result.stderr}")
            return False
            
        print("✅ Services started successfully")
        return True
    
    def stop_services(self, remove_volumes: bool = True) -> bool:
        """Stop Docker services"""
        print("🛑 Stopping Docker services...")
        
        volumes_flag = "-v" if remove_volumes else ""
        result = self.docker_compose(f"down {volumes_flag}")
        
        if result.returncode != 0:
            print(f"❌ Failed to stop services: {result.stderr}")
            return False
            
        print("✅ Services stopped successfully")
        return True
    
    def wait_for_healthy(self, service: str, timeout: int = None) -> bool:
        """Wait for service to be healthy"""
        timeout = timeout or self.config.startup_timeout
        print(f"⏳ Waiting for {service} to be healthy...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.docker_compose(f"ps {service}", check=False)
            if result.returncode == 0 and "healthy" in result.stdout:
                print(f"✅ {service} is healthy")
                return True
            elif "unhealthy" in result.stdout:
                print(f"❌ {service} is unhealthy")
                return False
            
            time.sleep(self.config.health_check_interval)
        
        print(f"⏱️ Timeout waiting for {service} to be healthy")
        return False
    
    def get_service_logs(self, service: str, tail: int = 100) -> str:
        """Get service logs"""
        result = self.docker_compose(f"logs --tail={tail} {service}", check=False)
        return result.stdout + result.stderr
    
    def test_service_running(self, service: str) -> bool:
        """Test if service is running"""
        result = self.docker_compose(f"ps {service}", check=False)
        return result.returncode == 0 and service in result.stdout
    
    def test_port_accessible(self, host: str, port: int, timeout: int = 5) -> bool:
        """Test if port is accessible"""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((host, port))
            return result == 0
        finally:
            sock.close()
    
    def test_http_endpoint(self, url: str, expected_status: int = 200, 
                          timeout: int = 10) -> Tuple[bool, Optional[Dict]]:
        """Test HTTP endpoint"""
        try:
            response = requests.get(url, timeout=timeout)
            success = response.status_code == expected_status
            
            try:
                data = response.json()
            except:
                data = {"text": response.text}
                
            return success, data
        except Exception as e:
            return False, {"error": str(e)}
    
    def test_database_connection(self, host: str = "localhost", port: int = 5432,
                                dbname: str = "synapse_dt", user: str = "synapse_user",
                                password: str = "synapse_password") -> bool:
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                connect_timeout=10
            )
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def test_redis_connection(self, host: str = "localhost", port: int = 6379,
                             password: str = None) -> bool:
        """Test Redis connection"""
        try:
            r = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_connect_timeout=10
            )
            r.ping()
            return True
        except Exception as e:
            print(f"Redis connection failed: {e}")
            return False
    
    def execute_in_container(self, service: str, command: str) -> Tuple[bool, str]:
        """Execute command in container"""
        result = self.docker_compose(f"exec -T {service} {command}", check=False)
        return result.returncode == 0, result.stdout
    
    def get_container_stats(self, service: str) -> Optional[Dict]:
        """Get container resource stats"""
        try:
            container = self.docker_client.containers.get(f"{self.config.project_name}_{service}_1")
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
            number_cpus = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
            cpu_percent = (cpu_delta / system_cpu_delta) * number_cpus * 100.0
            
            # Calculate memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage / 1024 / 1024, 2),
                'memory_percent': round(memory_percent, 2),
                'network_rx_mb': round(stats['networks']['eth0']['rx_bytes'] / 1024 / 1024, 2),
                'network_tx_mb': round(stats['networks']['eth0']['tx_bytes'] / 1024 / 1024, 2),
            }
        except Exception as e:
            print(f"Failed to get stats for {service}: {e}")
            return None
    
    def add_test_result(self, test_name: str, passed: bool, 
                       duration: float = None, details: Dict = None):
        """Add test result"""
        self.test_results.append({
            'test_name': test_name,
            'passed': passed,
            'duration': duration,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_report(self, output_file: str = None) -> Dict:
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_duration': time.time() - self.start_time if self.start_time else 0
            },
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
                
        return report
    
    @contextmanager
    def test_context(self, test_name: str):
        """Context manager for test execution"""
        print(f"\n🧪 Running test: {test_name}")
        start_time = time.time()
        passed = False
        details = {}
        
        try:
            yield details
            passed = True
            print(f"✅ {test_name} passed")
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            details['error'] = str(e)
        finally:
            duration = time.time() - start_time
            self.add_test_result(test_name, passed, duration, details)


class TestRunner:
    """Base class for test runners"""
    
    def __init__(self, framework: DockerTestFramework):
        self.framework = framework
        
    def run(self) -> bool:
        """Run tests - to be implemented by subclasses"""
        raise NotImplementedError
        
    def setup(self) -> bool:
        """Setup test environment"""
        return True
        
    def teardown(self) -> bool:
        """Teardown test environment"""
        return True