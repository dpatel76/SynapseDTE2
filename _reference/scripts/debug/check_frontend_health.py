#!/usr/bin/env python3
"""
Check frontend health and common issues
"""

import os
import subprocess
import requests
import json

def check_frontend_process():
    """Check if frontend process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'react-scripts'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Frontend process is running")
            return True
        else:
            print("❌ Frontend process is not running")
            return False
    except Exception as e:
        print(f"❌ Error checking frontend process: {e}")
        return False

def check_frontend_logs():
    """Check frontend logs for errors"""
    log_file = "frontend.log"
    if os.path.exists(log_file):
        print(f"\nChecking {log_file} for errors...")
        error_count = 0
        warning_count = 0
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines
                
            for line in lines:
                if "ERROR" in line or "Error:" in line:
                    error_count += 1
                    if error_count <= 3:  # Show first 3 errors
                        print(f"  ❌ Error: {line.strip()[:100]}...")
                elif "WARNING" in line or "Warning:" in line:
                    warning_count += 1
                    
            if error_count == 0:
                print("  ✅ No errors found in frontend logs")
            else:
                print(f"  ❌ Found {error_count} errors in frontend logs")
                
            if warning_count > 0:
                print(f"  ⚠️  Found {warning_count} warnings in frontend logs")
                
        except Exception as e:
            print(f"  ❌ Error reading frontend logs: {e}")
    else:
        print("  ℹ️  No frontend.log file found")

def check_api_connectivity():
    """Check if frontend can connect to backend"""
    try:
        # Check if frontend proxy is configured correctly
        resp = requests.get("http://localhost:3000/api/v1/health", timeout=5)
        if resp.status_code == 200:
            print("✅ Frontend proxy to backend is working")
        else:
            print(f"❌ Frontend proxy returned status {resp.status_code}")
    except Exception as e:
        print(f"⚠️  Could not test frontend proxy: {e}")

def check_build_issues():
    """Check for common React build issues"""
    print("\nChecking for common frontend issues...")
    
    # Check if node_modules exists
    if os.path.exists("frontend/node_modules"):
        print("  ✅ node_modules directory exists")
    else:
        print("  ❌ node_modules directory missing - run 'npm install'")
    
    # Check package.json
    if os.path.exists("frontend/package.json"):
        with open("frontend/package.json", 'r') as f:
            package = json.load(f)
            
        # Check React version
        react_version = package.get("dependencies", {}).get("react", "Not found")
        print(f"  ℹ️  React version: {react_version}")
        
        # Check proxy configuration
        proxy = package.get("proxy")
        if proxy:
            print(f"  ✅ Proxy configured: {proxy}")
        else:
            print("  ⚠️  No proxy configured in package.json")
    else:
        print("  ❌ package.json not found")

def check_env_variables():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    env_file = "frontend/.env"
    if os.path.exists(env_file):
        print("  ✅ .env file exists")
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key = line.split('=')[0].strip()
                    print(f"    - {key}")
    else:
        print("  ℹ️  No .env file in frontend directory")

def main():
    print("🔍 Frontend Health Check")
    print("="*50)
    
    # Change to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    check_frontend_process()
    check_frontend_logs()
    check_api_connectivity()
    check_build_issues()
    check_env_variables()
    
    print("\n" + "="*50)
    print("Frontend health check completed")

if __name__ == "__main__":
    main()