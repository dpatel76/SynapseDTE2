#!/usr/bin/env python3
"""Check phase states using direct SQL"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/synapse_dte")
# Convert to sync URL
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Connect to database
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("\n📊 Workflow Phases for Cycle 9, Report 156:")
print("=" * 80)

# Get workflow phases
cur.execute("""
    SELECT phase_id, phase_name, state, status, schedule_status, 
           state_override, status_override, actual_start_date, actual_end_date
    FROM workflow_phases
    WHERE cycle_id = 9 AND report_id = 156
    ORDER BY phase_id
""")

phases = cur.fetchall()
for phase in phases:
    print(f"\n{phase[1]}:")
    print(f"  - Phase ID: {phase[0]}")
    print(f"  - State: {phase[2]}")
    print(f"  - Status: {phase[3]}")
    print(f"  - Schedule Status: {phase[4]}")
    print(f"  - State Override: {phase[5]}")
    print(f"  - Status Override: {phase[6]}")
    print(f"  - Actual Start Date: {phase[7]}")
    print(f"  - Actual End Date: {phase[8]}")

# Check activities
print("\n\n🔍 Checking Phase Activities:")
print("=" * 80)

# Request Info
cur.execute("""
    SELECT COUNT(*) FROM request_info_submissions
    WHERE cycle_id = 9 AND report_id = 156
""")
print(f"\nRequest Info Submissions: {cur.fetchone()[0]}")

cur.execute("""
    SELECT COUNT(*) FROM test_cases
    WHERE cycle_id = 9 AND report_id = 156
""")
print(f"Test Cases Generated: {cur.fetchone()[0]}")

# Testing
cur.execute("""
    SELECT COUNT(*), 
           SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
           SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
    FROM cycle_report_test_execution_test_executions
    WHERE cycle_id = 9 AND report_id = 156
""")
result = cur.fetchone()
print(f"\nTest Executions: {result[0]}")
if result[0] > 0:
    print(f"  - In Progress: {result[1]}")
    print(f"  - Completed: {result[2]}")

# Observations
cur.execute("""
    SELECT COUNT(*),
           SUM(CASE WHEN status = 'Draft' THEN 1 ELSE 0 END) as draft,
           SUM(CASE WHEN status = 'Pending Approval' THEN 1 ELSE 0 END) as pending,
           SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) as approved
    FROM observations
    WHERE cycle_id = 9 AND report_id = 156
""")
result = cur.fetchone()
print(f"\nObservations: {result[0]}")
if result[0] > 0:
    print(f"  - Draft: {result[1]}")
    print(f"  - Pending Approval: {result[2]}")
    print(f"  - Approved: {result[3]}")

cur.close()
conn.close()