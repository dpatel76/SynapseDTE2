#!/usr/bin/env python3
"""
Setup data owner for testing evidence submission flow
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
import bcrypt
import uuid

DATABASE_URL = "postgresql+asyncpg://synapse_user:synapse_password@localhost/synapse_dt"


async def setup_data_owner():
    """Create data owner user if not exists"""
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # Check if data owner exists
        result = await conn.execute(
            text("SELECT user_id FROM users WHERE email = 'data1@example.com'")
        )
        existing = result.fetchone()
        
        if not existing:
            # Create data owner
            password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_id = str(uuid.uuid4())
            
            await conn.execute(
                text("""
                    INSERT INTO users (user_id, email, password_hash, first_name, last_name, role, is_active)
                    VALUES (:user_id, :email, :password_hash, :first_name, :last_name, :role, :is_active)
                """),
                {
                    "user_id": user_id,
                    "email": "data1@example.com",
                    "password_hash": password_hash,
                    "first_name": "Data",
                    "last_name": "Owner",
                    "role": "Data Owner",
                    "is_active": True
                }
            )
            print("✅ Created data owner user: data1@example.com")
        else:
            print("✅ Data owner already exists: data1@example.com")
            user_id = existing[0]
        
        # Ensure tester exists
        result = await conn.execute(
            text("SELECT user_id FROM users WHERE email = 'tester@example.com'")
        )
        tester = result.fetchone()
        
        if not tester:
            # Create tester
            password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            tester_id = str(uuid.uuid4())
            
            await conn.execute(
                text("""
                    INSERT INTO users (user_id, email, password_hash, first_name, last_name, role, is_active)
                    VALUES (:user_id, :email, :password_hash, :first_name, :last_name, :role, :is_active)
                """),
                {
                    "user_id": tester_id,
                    "email": "tester@example.com",
                    "password_hash": password_hash,
                    "first_name": "Test",
                    "last_name": "User",
                    "role": "Tester",
                    "is_active": True
                }
            )
            print("✅ Created tester user: tester@example.com")
        else:
            print("✅ Tester already exists: tester@example.com")
        
        # Create assignment for data owner if not exists
        result = await conn.execute(
            text("""
                SELECT id FROM universal_assignments 
                WHERE to_user_id = :user_id 
                AND assignment_type = 'LOB Assignment'
                AND status = 'Assigned'
                LIMIT 1
            """),
            {"user_id": user_id}
        )
        assignment = result.fetchone()
        
        if not assignment:
            print("⚠️ No assignments found for data owner")
            
            # Get phase_id for RFI
            phase_result = await conn.execute(
                text("""
                    SELECT phase_id FROM workflow_phases 
                    WHERE cycle_id = 55 AND report_id = 156 
                    AND phase_name = 'Request for Information'
                """)
            )
            phase = phase_result.fetchone()
            
            if phase:
                phase_id = phase[0]
                # Create test assignment
                await conn.execute(
                    text("""
                        INSERT INTO universal_assignments 
                        (phase_id, assignment_type, context_type, context_data, 
                         from_user_id, to_user_id, status, priority, due_date)
                        VALUES (:phase_id, :assignment_type, :context_type, :context_data,
                                :from_user_id, :to_user_id, :status, :priority, CURRENT_DATE + INTERVAL '7 days')
                    """),
                    {
                        "phase_id": phase_id,
                        "assignment_type": "LOB Assignment",
                        "context_type": "RFI",
                        "context_data": '{"attribute_name": "Current Credit limit", "lob": "Commercial"}',
                        "from_user_id": user_id,  # Self-assigned for testing
                        "to_user_id": user_id,
                        "status": "Assigned",
                        "priority": "High"
                    }
                )
                print("✅ Created test assignment for data owner")


if __name__ == "__main__":
    asyncio.run(setup_data_owner())