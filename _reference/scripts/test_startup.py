#!/usr/bin/env python3
"""Test that all components can start without errors"""

import subprocess
import time
import requests
import os
import signal
import sys

def test_backend():
    """Test backend server startup"""
    print("Testing Backend Server...")
    print("-" * 50)
    
    # Start the backend server
    env = os.environ.copy()
    env['DATABASE_URL'] = 'postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt'
    
    proc = subprocess.Popen(
        ['python', '-m', 'uvicorn', 'app.main:app', '--port', '8001'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give it time to start
    time.sleep(5)
    
    try:
        # Check if it's running
        response = requests.get('http://localhost:8001/docs')
        if response.status_code == 200:
            print("✅ Backend server started successfully")
            print("   - API docs available at http://localhost:8001/docs")
        else:
            print(f"❌ Backend server returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend server failed to start")
        # Print any errors
        stdout, stderr = proc.communicate(timeout=1)
        if stderr:
            print("Errors:", stderr)
    finally:
        # Kill the process
        proc.terminate()
        proc.wait()
    
    print()

def test_temporal_worker():
    """Test Temporal worker startup"""
    print("Testing Temporal Worker...")
    print("-" * 50)
    
    try:
        # Try to import the worker
        from app.temporal.worker import main as worker_main
        print("✅ Temporal worker imports successfully")
    except Exception as e:
        print(f"❌ Temporal worker import failed: {e}")
        return
    
    # Test worker configuration
    try:
        from app.temporal.activities import planning_activities
        from app.temporal.workflows import test_cycle_workflow
        print("✅ Temporal activities and workflows import successfully")
    except Exception as e:
        print(f"❌ Temporal components import failed: {e}")
    
    print()

def test_frontend():
    """Test frontend build"""
    print("Testing Frontend...")
    print("-" * 50)
    
    # Check if package.json exists
    if not os.path.exists('frontend/package.json'):
        print("❌ Frontend package.json not found")
        return
    
    # Check node_modules
    if not os.path.exists('frontend/node_modules'):
        print("⚠️  node_modules not found - run 'npm install' first")
    else:
        print("✅ Frontend dependencies installed")
    
    # Test build
    proc = subprocess.run(
        ['npm', 'run', 'build'],
        cwd='frontend',
        capture_output=True,
        text=True
    )
    
    if proc.returncode == 0:
        print("✅ Frontend builds successfully")
    else:
        print(f"❌ Frontend build failed")
        if proc.stderr:
            print("Errors:", proc.stderr[:500])  # First 500 chars of error
    
    print()

def check_database_connection():
    """Check database connection"""
    print("Testing Database Connection...")
    print("-" * 50)
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine('postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check key tables
            tables = ['report_inventory', 'cycle_reports', 'users', 'test_cycles']
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   - {table}: {count} records")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    print()

def main():
    print("=== SynapseDTE Component Startup Test ===")
    print()
    
    # Test database first
    check_database_connection()
    
    # Test backend
    test_backend()
    
    # Test Temporal worker
    test_temporal_worker()
    
    # Test frontend
    test_frontend()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    main()