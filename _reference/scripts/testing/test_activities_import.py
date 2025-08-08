#!/usr/bin/env python
"""Test script to verify all activity imports work"""

import sys

try:
    print("Testing activity imports...")
    
    # Test each activity module
    print("1. Planning activities...", end="")
    from app.temporal.activities.planning_activities_reconciled import *
    print(" OK")
    
    print("2. Scoping activities...", end="")
    from app.temporal.activities.scoping_activities_reconciled import *
    print(" OK")
    
    print("3. Sample selection activities...", end="")
    from app.temporal.activities.sample_selection_activities_reconciled import *
    print(" OK")
    
    print("4. Data provider activities...", end="")
    from app.temporal.activities.data_provider_activities_reconciled import *
    print(" OK")
    
    print("5. Request info activities...", end="")
    from app.temporal.activities.request_info_activities_reconciled import *
    print(" OK")
    
    print("6. Test execution activities...", end="")
    from app.temporal.activities.test_execution_activities_reconciled import *
    print(" OK")
    
    print("7. Observation activities...", end="")
    from app.temporal.activities.observation_activities_reconciled import *
    print(" OK")
    
    print("8. Test report activities...", end="")
    from app.temporal.activities.test_report_activities_reconciled import *
    print(" OK")
    
    print("\nAll activity imports successful!")
    
except ImportError as e:
    print(f"\nFAILED: {e}")
    sys.exit(1)