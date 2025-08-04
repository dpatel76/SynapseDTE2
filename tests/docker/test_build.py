#!/usr/bin/env python3
"""
Container Build Tests for SynapseDTE
Tests for Dockerfile validation, image building, and security scanning
"""

import os
import json
import subprocess
from typing import Dict, List
from test_framework import DockerTestFramework, TestRunner, TestConfig


class BuildTestRunner(TestRunner):
    """Test runner for container build tests"""
    
    def __init__(self, framework: DockerTestFramework):
        super().__init__(framework)
        self.images = [
            {'name': 'synapse-backend', 'dockerfile': 'Dockerfile.backend'},
            {'name': 'synapse-frontend', 'dockerfile': 'Dockerfile.frontend'},
            {'name': 'synapse-worker', 'dockerfile': 'Dockerfile.worker'}
        ]
    
    def run(self) -> bool:
        """Run all build tests"""
        print("\n🏗️  Running Container Build Tests\n")
        
        # Test Dockerfile linting
        self.test_dockerfile_lint()
        
        # Test image builds
        for image in self.images:
            self.test_image_build(image['name'], image['dockerfile'])
            self.test_image_size(image['name'])
            self.test_image_layers(image['name'])
            
        # Test security scanning if tools available
        if self.is_trivy_available():
            for image in self.images:
                self.test_security_scan(image['name'])
        
        # Test multi-stage builds
        self.test_multistage_optimization()
        
        # Generate report
        report = self.framework.generate_report()
        passed = report['summary']['failed'] == 0
        
        print(f"\n📊 Build Test Summary: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
        return passed
    
    def test_dockerfile_lint(self):
        """Test Dockerfile best practices using hadolint"""
        for image in self.images:
            with self.framework.test_context(f"Dockerfile lint - {image['dockerfile']}"):
                # Check if hadolint is available
                result = subprocess.run("which hadolint", shell=True, capture_output=True)
                
                if result.returncode != 0:
                    print("⚠️  hadolint not found, skipping Dockerfile linting")
                    print("   Install with: brew install hadolint")
                    return
                
                # Run hadolint
                cmd = f"hadolint --ignore DL3008 --ignore DL3009 {image['dockerfile']}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"Dockerfile linting failed:\n{result.stdout}")
                
                print(f"   ✓ {image['dockerfile']} follows best practices")
    
    def test_image_build(self, image_name: str, dockerfile: str):
        """Test building Docker image"""
        with self.framework.test_context(f"Build image - {image_name}") as details:
            # Build image
            cmd = f"docker build -f {dockerfile} -t {image_name}:test ."
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                details['build_output'] = result.stderr
                raise Exception(f"Failed to build image:\n{result.stderr}")
            
            # Verify image exists
            cmd = f"docker images {image_name}:test --format json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if not result.stdout:
                raise Exception("Image not found after build")
            
            image_info = json.loads(result.stdout)
            details['image_id'] = image_info.get('ID', 'unknown')
            details['size'] = image_info.get('Size', 'unknown')
            
            print(f"   ✓ Built {image_name} ({details['size']})")
    
    def test_image_size(self, image_name: str):
        """Test image size is within acceptable limits"""
        with self.framework.test_context(f"Image size check - {image_name}") as details:
            # Get image size
            cmd = f"docker images {image_name}:test --format '{{{{.Size}}}}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception("Failed to get image size")
            
            size_str = result.stdout.strip()
            details['size'] = size_str
            
            # Parse size to MB
            size_mb = self._parse_size_to_mb(size_str)
            details['size_mb'] = size_mb
            
            # Define size limits
            size_limits = {
                'synapse-backend': 500,  # 500MB
                'synapse-frontend': 100,  # 100MB
                'synapse-worker': 500,    # 500MB
            }
            
            limit = size_limits.get(image_name, 600)
            if size_mb > limit:
                raise Exception(f"Image size {size_mb}MB exceeds limit of {limit}MB")
            
            print(f"   ✓ Image size {size_str} is within limit ({limit}MB)")
    
    def test_image_layers(self, image_name: str):
        """Test number of layers in image"""
        with self.framework.test_context(f"Image layers check - {image_name}") as details:
            # Get layer count
            cmd = f"docker history {image_name}:test --format '{{{{.CreatedBy}}}}' | wc -l"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception("Failed to get image history")
            
            layer_count = int(result.stdout.strip())
            details['layer_count'] = layer_count
            
            # Check layer count is reasonable
            if layer_count > 50:
                raise Exception(f"Too many layers ({layer_count}), consider optimizing Dockerfile")
            
            print(f"   ✓ Image has {layer_count} layers")
    
    def test_security_scan(self, image_name: str):
        """Test image security using Trivy"""
        with self.framework.test_context(f"Security scan - {image_name}") as details:
            # Run Trivy scan
            cmd = f"trivy image --severity HIGH,CRITICAL --exit-code 1 {image_name}:test"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            details['scan_output'] = result.stdout
            
            if result.returncode != 0:
                # Parse vulnerabilities
                vulnerabilities = self._parse_trivy_output(result.stdout)
                details['vulnerabilities'] = vulnerabilities
                
                if vulnerabilities.get('critical', 0) > 0:
                    raise Exception(f"Found {vulnerabilities['critical']} critical vulnerabilities")
                elif vulnerabilities.get('high', 0) > 5:
                    raise Exception(f"Found {vulnerabilities['high']} high vulnerabilities")
            
            print(f"   ✓ No critical vulnerabilities found")
    
    def test_multistage_optimization(self):
        """Test multi-stage build optimization"""
        with self.framework.test_context("Multi-stage build optimization") as details:
            for image in self.images:
                # Check if Dockerfile uses multi-stage
                with open(image['dockerfile'], 'r') as f:
                    content = f.read()
                    
                from_count = content.count('FROM ')
                details[f"{image['name']}_stages"] = from_count
                
                if from_count < 2:
                    print(f"   ⚠️  {image['dockerfile']} is not using multi-stage build")
                else:
                    print(f"   ✓ {image['dockerfile']} uses {from_count} stages")
    
    def is_trivy_available(self) -> bool:
        """Check if Trivy is available"""
        result = subprocess.run("which trivy", shell=True, capture_output=True)
        if result.returncode != 0:
            print("⚠️  Trivy not found, skipping security scans")
            print("   Install with: brew install aquasecurity/trivy/trivy")
            return False
        return True
    
    def _parse_size_to_mb(self, size_str: str) -> float:
        """Parse Docker size string to MB"""
        size_str = size_str.strip()
        if 'GB' in size_str:
            return float(size_str.replace('GB', '')) * 1024
        elif 'MB' in size_str:
            return float(size_str.replace('MB', ''))
        elif 'KB' in size_str:
            return float(size_str.replace('KB', '')) / 1024
        else:
            return 0
    
    def _parse_trivy_output(self, output: str) -> Dict[str, int]:
        """Parse Trivy scan output for vulnerability counts"""
        vulnerabilities = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for line in output.split('\n'):
            if 'CRITICAL:' in line:
                try:
                    count = int(line.split('CRITICAL:')[1].strip().split()[0])
                    vulnerabilities['critical'] = count
                except:
                    pass
            elif 'HIGH:' in line:
                try:
                    count = int(line.split('HIGH:')[1].strip().split()[0])
                    vulnerabilities['high'] = count
                except:
                    pass
        
        return vulnerabilities


def main():
    """Run build tests"""
    config = TestConfig()
    framework = DockerTestFramework(config)
    runner = BuildTestRunner(framework)
    
    success = runner.run()
    
    # Save detailed report
    framework.generate_report("build_test_report.json")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())