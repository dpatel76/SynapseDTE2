#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.request_info import RequestInfoPhase, TestCase, DataProviderNotification
from app.core.database import AsyncSessionLocal
from sqlalchemy import select

async def check_notifications():
    async with AsyncSessionLocal() as db:
        try:
            print("=== DATA PROVIDER NOTIFICATIONS ===")
            result = await db.execute(select(DataProviderNotification))
            notifications = result.scalars().all()
            print(f"Total notifications: {len(notifications)}")
            
            for notification in notifications:
                print(f"Notification ID: {notification.notification_id}")
                print(f"  Phase ID: {notification.phase_id}")
                print(f"  Data Provider ID: {notification.data_owner_id}")
                print(f"  Status: {notification.status}")
                print(f"  Sent At: {notification.notification_sent_at}")
                print(f"  Acknowledged: {notification.is_acknowledged}")
                print()
            
            print("=== CHECKING PHASE 0980a908-336c-4d4e-9032-e30f0a335e84 ===")
            phase_id = "0980a908-336c-4d4e-9032-e30f0a335e84"
            
            # Check if notification exists for data provider 6
            result = await db.execute(
                select(DataProviderNotification).where(
                    (DataProviderNotification.phase_id == phase_id) &
                    (DataProviderNotification.data_owner_id == 6)
                )
            )
            notification = result.scalar_one_or_none()
            
            if notification:
                print(f"✅ Notification exists for Data Provider 6")
                print(f"   Status: {notification.status}")
                print(f"   Sent: {notification.notification_sent_at}")
            else:
                print(f"❌ No notification found for Data Provider 6 in phase {phase_id}")
                
                # Check what test cases exist for this data provider
                result = await db.execute(
                    select(TestCase).where(
                        (TestCase.phase_id == phase_id) &
                        (TestCase.data_owner_id == 6)
                    )
                )
                test_cases = result.scalars().all()
                print(f"   But {len(test_cases)} test cases exist for this data provider")
        
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(check_notifications()) 