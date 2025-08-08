#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from app.models.testing import DataProviderAssignment
from app.models.report_attribute import ReportAttribute
from app.models.user import User
from app.models.lob import LOB

async def check_assignments():
    """Check current CDO assignments"""
    
    engine = create_async_engine('sqlite+aiosqlite:///./synapse_dt.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=== CDO ASSIGNMENTS CHECK ===\n")
        
        # 1. Check all DataProviderAssignment records
        print("1. All DataProviderAssignment Records:")
        all_assignments = await session.execute(
            select(DataProviderAssignment.assignment_id,
                   DataProviderAssignment.cycle_id,
                   DataProviderAssignment.report_id,
                   DataProviderAssignment.attribute_id,
                   DataProviderAssignment.cdo_id,
                   DataProviderAssignment.assigned_by,
                   DataProviderAssignment.data_owner_id,
                   DataProviderAssignment.status)
        )
        assignments = all_assignments.all()
        
        for assignment in assignments:
            print(f"   Assignment {assignment.assignment_id}: C{assignment.cycle_id}/R{assignment.report_id}/A{assignment.attribute_id}")
            print(f"     CDO ID: {assignment.cdo_id}, Assigned By: {assignment.assigned_by}")
            print(f"     Data Provider: {assignment.data_owner_id}, Status: {assignment.status}")
        
        print()
        
        # 2. Test the exact query used by the service
        print("2. Testing Service Query (cdo_id = 5):")
        service_query = await session.execute(
            select(DataProviderAssignment, ReportAttribute, User, LOB)
            .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderAssignment.data_owner_id == User.user_id)
            .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
            .where(DataProviderAssignment.cdo_id == 5)
        )
        service_results = service_query.all()
        
        print(f"   Found {len(service_results)} assignments for CDO ID 5")
        for assignment, attribute, user, lob in service_results:
            print(f"   Assignment {assignment.assignment_id}:")
            print(f"     Attribute: {attribute.attribute_name}")
            print(f"     Data Provider: {user.first_name} {user.last_name}")
            print(f"     LOB: {lob.lob_name}")
            print(f"     Status: {assignment.status}")
        
        print()
        
        # 3. Check if there are any issues with the joins
        print("3. Testing Individual Components:")
        
        # Check DataProviderAssignment with cdo_id = 5
        cdo_assignments = await session.execute(
            select(DataProviderAssignment)
            .where(DataProviderAssignment.cdo_id == 5)
        )
        cdo_results = cdo_assignments.all()
        print(f"   DataProviderAssignment records with cdo_id=5: {len(cdo_results)}")
        
        # Check if attributes exist
        for assignment in cdo_results:
            attr_check = await session.execute(
                select(ReportAttribute.attribute_name)
                .where(ReportAttribute.attribute_id == assignment.attribute_id)
            )
            attr_result = attr_check.first()
            print(f"     Assignment {assignment.assignment_id} -> Attribute {assignment.attribute_id}: {attr_result[0] if attr_result else 'NOT FOUND'}")

if __name__ == "__main__":
    asyncio.run(check_assignments()) 