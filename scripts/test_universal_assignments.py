#!/usr/bin/env python3
"""
Test script for Universal Assignments integration
Tests the complete flow of creating and managing assignments
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.universal_assignment import UniversalAssignment
from app.models.user import User
from app.services.universal_assignment_service import UniversalAssignmentService
from app.services.email_service import EmailService
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_universal_assignments():
    """Test Universal Assignments functionality"""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/synapse_dt")
    
    # Convert to async URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    # Create database engine
    engine = create_async_engine(database_url, echo=True)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as db:
        try:
            print("\n=== Testing Universal Assignments ===\n")
            
            # Get test users
            tester = await db.get(User, 1)  # Assuming user ID 1 is a tester
            test_manager = await db.get(User, 2)  # Assuming user ID 2 is a test manager
            
            if not tester or not test_manager:
                print("Error: Test users not found. Please run create_test_users.py first.")
                return
            
            print(f"Tester: {tester.full_name} (ID: {tester.user_id})")
            print(f"Test Manager: {test_manager.full_name} (ID: {test_manager.user_id})")
            
            # Initialize services
            email_service = EmailService()
            assignment_service = UniversalAssignmentService(db, email_service)
            
            # Test 1: Create a Phase Review assignment
            print("\n1. Creating Phase Review assignment...")
            assignment1 = await assignment_service.create_assignment(
                assignment_type="Phase Review",
                from_role="Tester",
                to_role="Test Manager",
                from_user_id=tester.user_id,
                to_user_id=test_manager.user_id,
                title="Review Planning Phase",
                description="Please review the generated test attributes for the planning phase",
                context_type="Report",
                context_data={
                    "cycle_id": 21,
                    "report_id": 156,
                    "phase_name": "Planning"
                },
                priority="High",
                due_date=datetime.utcnow() + timedelta(hours=24)
            )
            await db.commit()
            print(f"✓ Created assignment: {assignment1.assignment_id}")
            
            # Test 2: Acknowledge the assignment
            print("\n2. Acknowledging assignment...")
            acknowledged = await assignment_service.acknowledge_assignment(
                assignment1.assignment_id, 
                test_manager.user_id
            )
            await db.commit()
            print(f"✓ Assignment acknowledged at: {acknowledged.acknowledged_at}")
            
            # Test 3: Start working on the assignment
            print("\n3. Starting assignment...")
            started = await assignment_service.start_assignment(
                assignment1.assignment_id,
                test_manager.user_id
            )
            await db.commit()
            print(f"✓ Assignment started at: {started.started_at}")
            
            # Test 4: Complete the assignment
            print("\n4. Completing assignment...")
            completed = await assignment_service.complete_assignment(
                assignment1.assignment_id,
                test_manager.user_id,
                completion_notes="Reviewed and approved all test attributes",
                completion_data={"attributes_reviewed": 25, "approved": True}
            )
            await db.commit()
            print(f"✓ Assignment completed at: {completed.completed_at}")
            
            # Test 5: Create a Scoping Approval assignment
            print("\n5. Creating Scoping Approval assignment...")
            assignment2 = await assignment_service.create_assignment(
                assignment_type="Scoping Approval",
                from_role="Tester",
                to_role="Test Manager",
                from_user_id=tester.user_id,
                to_user_id=test_manager.user_id,
                title="Review Scoping Decisions",
                description="Review and approve the scoping decisions for testing",
                context_type="Report",
                context_data={
                    "cycle_id": 21,
                    "report_id": 156,
                    "phase_name": "Scoping",
                    "selected_attributes": 18,
                    "total_attributes": 25
                },
                priority="High",
                due_date=datetime.utcnow() + timedelta(hours=48),
                requires_approval=True,
                approval_role="Report Owner"
            )
            await db.commit()
            print(f"✓ Created assignment: {assignment2.assignment_id}")
            
            # Test 6: Query assignments for user
            print("\n6. Querying assignments for Test Manager...")
            assignments = await assignment_service.get_assignments_for_user(
                user_id=test_manager.user_id,
                status_filter=["Assigned", "Acknowledged", "In Progress"],
                limit=10
            )
            print(f"✓ Found {len(assignments)} assignments for Test Manager")
            for assign in assignments:
                print(f"  - {assign.title} ({assign.status})")
            
            # Test 7: Get metrics
            print("\n7. Getting assignment metrics...")
            metrics = await assignment_service.get_assignment_metrics(
                user_id=test_manager.user_id
            )
            print(f"✓ Assignment metrics:")
            print(f"  - Total: {metrics['total_assignments']}")
            print(f"  - Completed: {metrics['completed_assignments']}")
            print(f"  - In Progress: {metrics['in_progress_assignments']}")
            print(f"  - Completion Rate: {metrics['completion_rate']:.1f}%")
            
            print("\n✅ All tests passed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_universal_assignments())