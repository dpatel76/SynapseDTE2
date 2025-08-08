#!/usr/bin/env python
"""
Test starting Data Provider ID phase via API
"""

import requests
import json
import time
import psycopg2

# First reset the phase
conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='synapse_dt',
    user='synapse_user',
    password='synapse_password'
)
cur = conn.cursor()

print("=== Resetting Data Provider ID phase ===")
try:
    # Reset activities
    cur.execute("""
        UPDATE workflow_activities 
        SET status = 'NOT_STARTED', started_at = NULL, started_by = NULL,
            completed_at = NULL, completed_by = NULL,
            can_start = CASE WHEN activity_order = 1 THEN true ELSE false END,
            can_complete = false
        WHERE cycle_id = 2 AND report_id = 3 AND phase_name = 'Data Provider ID'
    """)
    
    # Reset phase
    cur.execute("""
        UPDATE workflow_phases
        SET status = 'Not Started', state = 'Not Started',
            actual_start_date = NULL, started_by = NULL, progress_percentage = 0
        WHERE cycle_id = 2 AND report_id = 3 AND phase_name = 'Data Provider ID'
    """)
    
    # Get phase_id and clean up
    cur.execute("""
        SELECT phase_id FROM workflow_phases 
        WHERE cycle_id = 2 AND report_id = 3 AND phase_name = 'Data Provider ID'
    """)
    result = cur.fetchone()
    
    if result:
        phase_id = result[0]
        cur.execute("DELETE FROM cycle_report_data_owner_lob_mapping WHERE phase_id = %s", (phase_id,))
        cur.execute("DELETE FROM cycle_report_data_owner_lob_mapping_versions WHERE phase_id = %s", (phase_id,))
    
    conn.commit()
    print("✅ Phase reset successfully")
    
except Exception as e:
    print(f"❌ Error resetting phase: {str(e)}")
    conn.rollback()

cur.close()
conn.close()

# Login and get token
login_response = requests.post("http://localhost:8001/api/v1/auth/login", json={
    "email": "tester@example.com",
    "password": "password123"
})

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("✅ Logged in successfully")

# Start the Data Provider ID phase
print("\n=== Starting Data Provider ID phase ===")
start_response = requests.post(
    "http://localhost:8001/api/v1/activity-management/activities/Data_Provider_ID_1/start",
    headers=headers,
    json={
        "cycle_id": 2,
        "report_id": 3,
        "phase_name": "Data Provider ID"
    }
)

if start_response.status_code == 200:
    result = start_response.json()
    print(f"✅ Activity started successfully")
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Check if initialization happened
    if result.get("data_provider_initialized"):
        print(f"✅ Data Provider ID phase was initialized!")
    else:
        print(f"⚠️  Data Provider ID phase was not initialized")
else:
    print(f"❌ Failed to start activity: {start_response.status_code}")
    print(f"   Response: {start_response.text}")

# Give it a moment for async operations
time.sleep(2)

# Check if mappings were created
print("\n=== Checking for LOB attribute mappings ===")
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='synapse_dt',
    user='synapse_user',
    password='synapse_password'
)
cur = conn.cursor()

# Check for versions
cur.execute("""
    SELECT COUNT(*) FROM cycle_report_data_owner_lob_mapping_versions 
    WHERE phase_id = (SELECT phase_id FROM workflow_phases 
                      WHERE cycle_id = 2 AND report_id = 3 
                      AND phase_name = 'Data Provider ID')
""")
version_count = cur.fetchone()[0]
print(f"Versions created: {version_count}")

# Check for mappings
cur.execute("""
    SELECT COUNT(*) FROM cycle_report_data_owner_lob_mapping 
    WHERE phase_id = (SELECT phase_id FROM workflow_phases 
                      WHERE cycle_id = 2 AND report_id = 3 
                      AND phase_name = 'Data Provider ID')
""")
mapping_count = cur.fetchone()[0]
print(f"Mappings created: {mapping_count}")

cur.close()
conn.close()

if mapping_count > 0:
    print(f"\n✅ SUCCESS: Data Provider ID initialization is working! {mapping_count} mappings created.")
else:
    print(f"\n❌ FAILURE: No mappings were created")