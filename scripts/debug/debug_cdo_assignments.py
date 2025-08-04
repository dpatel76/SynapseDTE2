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
from app.models.test_cycle import TestCycle
from app.models.report import Report

async def debug_cdo_assignments():
    """Debug CDO assignments to understand why they're not showing in dashboard"""
    
    engine = create_async_engine('sqlite+aiosqlite:///./synapse_dt.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=== CDO ASSIGNMENTS DEBUG ===\n")
        
        # 1. Check CDO user details
        print("1. CDO User Details:")
        cdo_result = await session.execute(
            select(User.user_id, User.first_name, User.last_name, User.email, User.role, User.lob_id)
            .where(User.role == 'Data Executive')
        )
        cdo_users = cdo_result.all()
        for user in cdo_users:
            print(f"   CDO: {user.first_name} {user.last_name} (ID: {user.user_id}, Email: {user.email}, LOB: {user.lob_id})")
        
        print()
        
        # 2. Check all DataProviderAssignment records
        print("2. All DataProviderAssignment Records:")
        assignments_result = await session.execute(
            select(DataProviderAssignment.assignment_id,
                   DataProviderAssignment.cycle_id,
                   DataProviderAssignment.report_id,
                   DataProviderAssignment.attribute_id,
                   DataProviderAssignment.cdo_id,
                   DataProviderAssignment.assigned_by,
                   DataProviderAssignment.data_owner_id,
                   DataProviderAssignment.status,
                   DataProviderAssignment.assigned_at)
        )
        assignments = assignments_result.all()
        
        if not assignments:
            print("   No assignments found!")
        else:
            for assignment in assignments:
                print(f"   Assignment {assignment.assignment_id}: Cycle {assignment.cycle_id}, Report {assignment.report_id}")
                print(f"     Attribute: {assignment.attribute_id}, CDO: {assignment.cdo_id}, Assigned By: {assignment.assigned_by}")
                print(f"     Data Provider: {assignment.data_owner_id}, Status: {assignment.status}")
                print(f"     Assigned At: {assignment.assigned_at}")
                print()
        
        # 3. Check assignments for cycle 9, report 156 specifically
        print("3. Assignments for Cycle 9, Report 156:")
        cycle9_result = await session.execute(
            select(DataProviderAssignment, ReportAttribute, User, LOB)
            .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderAssignment.data_owner_id == User.user_id)
            .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
            .where(and_(
                DataProviderAssignment.cycle_id == 9,
                DataProviderAssignment.report_id == 156
            ))
        )
        cycle9_assignments = cycle9_result.all()
        
        if not cycle9_assignments:
            print("   No assignments found for Cycle 9, Report 156!")
        else:
            for assignment, attribute, dp_user, lob in cycle9_assignments:
                print(f"   Assignment {assignment.assignment_id}:")
                print(f"     Attribute: {attribute.attribute_name} (ID: {attribute.attribute_id})")
                print(f"     Data Provider: {dp_user.first_name} {dp_user.last_name} (ID: {dp_user.user_id})")
                print(f"     LOB: {lob.lob_name} (ID: {lob.lob_id})")
                print(f"     CDO ID: {assignment.cdo_id}, Assigned By: {assignment.assigned_by}")
                print(f"     Status: {assignment.status}, Assigned At: {assignment.assigned_at}")
                print()
        
        # 4. Check what the API query would return for CDO user ID 5
        print("4. API Query Simulation for CDO User ID 5:")
        print("   Query 1: Using assigned_by field (current API logic)")
        api_result1 = await session.execute(
            select(DataProviderAssignment, ReportAttribute, User, LOB)
            .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderAssignment.data_owner_id == User.user_id)
            .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
            .where(DataProviderAssignment.assigned_by == 5)
        )
        api_assignments1 = api_result1.all()
        print(f"     Found {len(api_assignments1)} assignments using assigned_by=5")
        
        print("   Query 2: Using cdo_id field (what should be used)")
        api_result2 = await session.execute(
            select(DataProviderAssignment, ReportAttribute, User, LOB)
            .join(ReportAttribute, DataProviderAssignment.attribute_id == ReportAttribute.attribute_id)
            .join(User, DataProviderAssignment.data_owner_id == User.user_id)
            .join(LOB, DataProviderAssignment.lob_id == LOB.lob_id)
            .where(DataProviderAssignment.cdo_id == 5)
        )
        api_assignments2 = api_result2.all()
        print(f"     Found {len(api_assignments2)} assignments using cdo_id=5")
        
        if api_assignments2:
            print("     Details of assignments found with cdo_id=5:")
            for assignment, attribute, dp_user, lob in api_assignments2:
                print(f"       Assignment {assignment.assignment_id}: {attribute.attribute_name} -> {dp_user.first_name} {dp_user.last_name}")
        
        # 5. Check cycle and report details
        print("\n5. Cycle and Report Details:")
        cycle_result = await session.execute(
            select(TestCycle.cycle_id, TestCycle.cycle_name, TestCycle.status)
            .where(TestCycle.cycle_id == 9)
        )
        cycle = cycle_result.first()
        if cycle:
            print(f"   Cycle 9: {cycle.cycle_name} (Status: {cycle.status})")
        
        report_result = await session.execute(
            select(Report.report_id, Report.report_name, Report.status)
            .where(Report.report_id == 156)
        )
        report = report_result.first()
        if report:
            print(f"   Report 156: {report.report_name} (Status: {report.status})")

if __name__ == "__main__":
    asyncio.run(debug_cdo_assignments()) 