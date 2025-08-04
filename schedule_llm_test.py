#!/usr/bin/env python3
"""
Schedule LLM test to run at 1:01 AM
Can also be run immediately with --now flag
"""

import subprocess
import time
import os
from datetime import datetime, timedelta
import sys

def run_tests():
    """Run the test sequence"""
    print(f"\n{'='*60}")
    print(f"Starting LLM fix and test at {datetime.now()}")
    print(f"{'='*60}\n")
    
    # Step 1: Apply the fix
    print("Step 1: Applying LLM service fix...")
    result = subprocess.run(
        [sys.executable, "auto_fix_llm_service.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Step 2: Run the test
    print("\nStep 2: Testing LLM service...")
    result = subprocess.run(
        [sys.executable, "test_llm_fix.py"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Step 3: Run comprehensive tests
    print("\nStep 3: Running comprehensive tests...")
    result = subprocess.run(
        [sys.executable, "automated_llm_test.py", "--now"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    print(f"\n{'='*60}")
    print(f"Tests completed at {datetime.now()}")
    print(f"{'='*60}\n")

def wait_until_time(hour, minute):
    """Wait until specific time"""
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If target time has passed today, wait until tomorrow
    if target <= now:
        target += timedelta(days=1)
    
    wait_seconds = (target - now).total_seconds()
    print(f"Waiting until {target} ({wait_seconds/3600:.1f} hours)...")
    
    # Show countdown every hour
    while wait_seconds > 0:
        hours_left = wait_seconds / 3600
        print(f"\r{hours_left:.1f} hours remaining...", end="", flush=True)
        
        sleep_time = min(3600, wait_seconds)  # Sleep for max 1 hour
        time.sleep(sleep_time)
        wait_seconds -= sleep_time
    
    print("\nTime reached!")

def main():
    if "--now" in sys.argv:
        print("Running immediately...")
        run_tests()
    else:
        print("Scheduler started. Will run at 1:01 AM.")
        print("Use --now flag to run immediately.")
        
        # Keep running daily
        while True:
            wait_until_time(1, 1)
            run_tests()
            
            # Wait a bit before scheduling next run
            time.sleep(60)

if __name__ == "__main__":
    # Make scripts executable
    for script in ["auto_fix_llm_service.py", "automated_llm_test.py"]:
        if os.path.exists(script):
            os.chmod(script, 0o755)
    
    main()