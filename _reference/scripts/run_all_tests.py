#!/usr/bin/env python
"""
Master test runner - runs all phase tests
"""

import subprocess
import sys
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_script(script_name, description):
    """Run a test script and return success status"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running: {description}")
    logger.info(f"Script: {script_name}")
    logger.info(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - PASSED")
            return True
        else:
            logger.error(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} - TIMEOUT")
        return False
    except Exception as e:
        logger.error(f"❌ {description} - ERROR: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("SYNAPSE DTE2 - COMPREHENSIVE TEST SUITE")
    logger.info("="*60)
    
    # Restart backend to ensure clean state
    logger.info("\nRestarting backend container...")
    subprocess.run(["docker-compose", "-f", "docker-compose.container.yml", "restart", "backend"], 
                   capture_output=True)
    time.sleep(10)  # Wait for backend to be ready
    
    # List of tests to run
    tests = [
        ("scripts/test_phase_initializations.py", "Phase Initialization Tests"),
        ("scripts/test_data_provider_id_initialization.py", "Data Provider ID Initialization"),
        ("scripts/test_all_phases_comprehensive.py", "Comprehensive Phase Tests"),
    ]
    
    results = {}
    
    # Run each test
    for script, description in tests:
        success = run_script(script, description)
        results[description] = success
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUITE SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for s in results.values() if s)
    failed = sum(1 for s in results.values() if not s)
    
    for test, success in results.items():
        symbol = "✅" if success else "❌"
        status = "PASSED" if success else "FAILED"
        logger.info(f"{symbol} {test}: {status}")
    
    logger.info(f"\nTotal Tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! The system is working correctly.")
        return 0
    else:
        logger.info(f"\n⚠️ {failed} TEST(S) FAILED. Please investigate the failures.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)