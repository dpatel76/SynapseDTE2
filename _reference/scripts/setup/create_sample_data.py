#!/usr/bin/env python3
"""
Script to create sample data for the SynapseDT application
"""

import asyncio
import sys
import os
from datetime import date, datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.auth import get_password_hash
from app.models.lob import LOB
from app.models.user import User
from app.models.report import Report
from app.models.test_cycle import TestCycle
from app.models.cycle_report import CycleReport


async def create_sample_data():
    """Create sample data for testing"""
    print("Creating sample data...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Create LOBs
            lobs_data = [
                {"lob_name": "Retail Banking"},
                {"lob_name": "Commercial Banking"},
                {"lob_name": "Investment Banking"},
                {"lob_name": "Risk Management"},
                {"lob_name": "Compliance"}
            ]
            
            lobs = []
            for lob_data in lobs_data:
                lob = LOB(**lob_data)
                db.add(lob)
                lobs.append(lob)
            
            await db.commit()
            
            # Refresh to get the generated IDs
            for lob in lobs:
                await db.refresh(lob)
            
            # Store lob_ids for later use
            lob_ids = [lob.lob_id for lob in lobs]
            
            print(f"✅ Created {len(lobs_data)} LOBs")
            
            # Create Users
            users_data = [
                {
                    "first_name": "John",
                    "last_name": "Smith",
                    "email": "john.smith@synapse.com",
                    "phone": "+1-555-0101",
                    "role": "Test Executive",
                    "lob_id": None,
                    "is_active": True,
                    "hashed_password": get_password_hash("TestManager123!")
                },
                {
                    "first_name": "Sarah",
                    "last_name": "Johnson",
                    "email": "sarah.johnson@synapse.com",
                    "phone": "+1-555-0102",
                    "role": "Report Owner",
                    "lob_id": None,
                    "is_active": True,
                    "hashed_password": get_password_hash("ReportOwner123!")
                },
                {
                    "first_name": "Mike",
                    "last_name": "Davis",
                    "email": "mike.davis@synapse.com",
                    "phone": "+1-555-0103",
                    "role": "Tester",
                    "lob_id": lob_ids[0],  # Retail Banking
                    "is_active": True,
                    "hashed_password": get_password_hash("Tester123!")
                },
                {
                    "first_name": "Lisa",
                    "last_name": "Wilson",
                    "email": "lisa.wilson@synapse.com",
                    "phone": "+1-555-0104",
                    "role": "Data Executive",
                    "lob_id": lob_ids[0],  # Retail Banking
                    "is_active": True,
                    "hashed_password": get_password_hash("CDO123!")
                },
                {
                    "first_name": "David",
                    "last_name": "Brown",
                    "email": "david.brown@synapse.com",
                    "phone": "+1-555-0105",
                    "role": "Data Owner",
                    "lob_id": lob_ids[0],  # Retail Banking
                    "is_active": True,
                    "hashed_password": get_password_hash("DataProvider123!")
                },
                {
                    "first_name": "Emily",
                    "last_name": "Taylor",
                    "email": "emily.taylor@synapse.com",
                    "phone": "+1-555-0106",
                    "role": "Report Owner Executive",
                    "lob_id": None,
                    "is_active": True,
                    "hashed_password": get_password_hash("Executive123!")
                }
            ]
            
            users = []
            for user_data in users_data:
                user = User(**user_data)
                db.add(user)
                users.append(user)
            
            await db.commit()
            
            # Refresh to get the generated IDs
            for user in users:
                await db.refresh(user)
            
            # Store user_ids for later use
            user_ids = [user.user_id for user in users]
            
            print(f"✅ Created {len(users_data)} users")
            
            # Create Reports
            reports_data = [
                {
                    "report_name": "CCAR Stress Testing Report",
                    "regulation": "Federal Reserve CCAR",
                    "report_owner_id": user_ids[1],  # Sarah Johnson
                    "lob_id": lob_ids[0]  # Retail Banking
                },
                {
                    "report_name": "Basel III Capital Adequacy Report",
                    "regulation": "Basel III",
                    "report_owner_id": user_ids[1],  # Sarah Johnson
                    "lob_id": lob_ids[1]  # Commercial Banking
                },
                {
                    "report_name": "Liquidity Coverage Ratio Report",
                    "regulation": "Basel III LCR",
                    "report_owner_id": user_ids[1],  # Sarah Johnson
                    "lob_id": lob_ids[2]  # Investment Banking
                }
            ]
            
            reports = []
            for report_data in reports_data:
                report = Report(**report_data)
                db.add(report)
                reports.append(report)
            
            await db.commit()
            
            # Refresh to get the generated IDs
            for report in reports:
                await db.refresh(report)
            
            print(f"✅ Created {len(reports_data)} reports")
            
            # Create Test Cycle
            test_cycle = TestCycle(
                cycle_name="Q4 2024 Regulatory Testing Cycle",
                start_date=date(2024, 10, 1),
                end_date=date(2024, 12, 31),
                test_manager_id=user_ids[0],  # John Smith
                status="Active"
            )
            db.add(test_cycle)
            
            await db.commit()
            await db.refresh(test_cycle)
            print("✅ Created test cycle")
            
            print("\n🎉 Sample data creation completed successfully!")
            print("\nSample Users Created:")
            print("- Test Manager: john.smith@synapse.com / TestManager123!")
            print("- Report Owner: sarah.johnson@synapse.com / ReportOwner123!")
            print("- Tester: mike.davis@synapse.com / Tester123!")
            print("- CDO: lisa.wilson@synapse.com / CDO123!")
            print("- Data Provider: david.brown@synapse.com / DataProvider123!")
            print("- Executive: emily.taylor@synapse.com / Executive123!")
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_sample_data()) 