#!/usr/bin/env python3
"""
Isolated Test Configuration for SynapseDTE
Runs tests on alternative ports to avoid conflicts with running services
"""

from test_framework import TestConfig, DockerTestFramework

class IsolatedTestConfig(TestConfig):
    """Configuration for isolated testing"""
    
    def __init__(self):
        super().__init__(
            compose_file="docker-compose.test.yml",
            project_name="synapse-isolated-test",
            api_base_url="http://localhost:18000",
            frontend_url="http://localhost:18080",
            temporal_url="http://localhost:18088"
        )
        
        # Override service ports
        self.service_ports = {
            'postgres': ('localhost', 15432),
            'redis': ('localhost', 16379),
            'backend': ('localhost', 18000),
            'frontend': ('localhost', 18080),
            'temporal': ('localhost', 17233),
            'temporal-ui': ('localhost', 18088)
        }
        
        # Override health endpoints
        self.health_endpoints = {
            'backend': {
                'url': 'http://localhost:18000/api/v1/health',
                'expected_status': 200
            },
            'frontend': {
                'url': 'http://localhost:18080/health',
                'expected_status': 200
            },
            'temporal-ui': {
                'url': 'http://localhost:18088',
                'expected_status': 200
            }
        }


def run_isolated_tests():
    """Run tests in isolated environment"""
    config = IsolatedTestConfig()
    framework = DockerTestFramework(config)
    
    print("🔒 Running tests in isolated environment")
    print(f"   API: {config.api_base_url}")
    print(f"   Frontend: {config.frontend_url}")
    print(f"   Project: {config.project_name}")
    
    return framework


if __name__ == "__main__":
    run_isolated_tests()