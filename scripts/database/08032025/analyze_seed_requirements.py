#!/usr/bin/env python3
"""
Analyze minimal seed data requirements for fully functional system
"""

import asyncio
import asyncpg
import json
from pathlib import Path
from collections import defaultdict

# Database configuration - READ ONLY
DB_CONFIG = {
    'host': 'localhost',
    'database': 'synapse_dt',
    'user': 'synapse_user',
    'password': 'synapse_password',
    'port': 5432
}

async def analyze_seed_requirements():
    """Analyze what seed data is required for system functionality"""
    conn = await asyncpg.connect(**DB_CONFIG)
    
    requirements = {
        "authentication": {},
        "workflow": {},
        "data_model": {},
        "permissions": {},
        "configuration": {}
    }
    
    try:
        print("=== Analyzing System Requirements ===\n")
        
        # 1. Authentication Requirements
        print("1. AUTHENTICATION & AUTHORIZATION")
        print("-" * 40)
        
        # Check authentication endpoint expectations from CLAUDE.md
        auth_users = [
            ('tester@example.com', 'password123', 'Tester'),
            ('admin@example.com', 'admin123', 'Admin'),
            ('report.owner@example.com', 'password123', 'Report Owner'),
            ('data.owner@example.com', 'password123', 'Data Owner'),
            ('data.executive@example.com', 'password123', 'Data Executive')
        ]
        
        print("Required test users:")
        for email, pwd, role in auth_users:
            print(f"  - {email} ({role})")
            
        # Get existing users and roles
        user_query = """
            SELECT u.email, r.name as role_name
            FROM users u
            LEFT JOIN rbac_user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN rbac_roles r ON ur.role_id = r.id
            WHERE u.email LIKE '%@example.com'
            ORDER BY u.email
        """
        existing_users = await conn.fetch(user_query)
        
        requirements["authentication"]["required_users"] = len(auth_users)
        requirements["authentication"]["existing_users"] = len(existing_users)
        
        # 2. Workflow Requirements
        print("\n2. WORKFLOW PHASES")
        print("-" * 40)
        
        phase_query = """
            SELECT phase_name, phase_order, COUNT(*) OVER() as total_phases
            FROM workflow_phases
            WHERE is_active = true
            ORDER BY phase_order
        """
        phases = await conn.fetch(phase_query)
        
        if phases:
            print(f"Total active phases: {phases[0]['total_phases']}")
            for phase in phases[:5]:
                print(f"  {phase['phase_order']}. {phase['phase_name']}")
            if len(phases) > 5:
                print(f"  ... and {len(phases) - 5} more")
                
        # Activity definitions per phase
        activity_query = """
            SELECT 
                phase_name,
                COUNT(*) as activity_count,
                MIN(sequence_order) as min_seq,
                MAX(sequence_order) as max_seq
            FROM activity_definitions
            WHERE is_active = true
            GROUP BY phase_name
            ORDER BY MIN(sequence_order)
        """
        activities = await conn.fetch(activity_query)
        
        print(f"\nActivities per phase:")
        for act in activities[:5]:
            print(f"  - {act['phase_name']}: {act['activity_count']} activities")
            
        requirements["workflow"]["phases"] = len(phases)
        requirements["workflow"]["activities"] = sum(a['activity_count'] for a in activities)
        
        # 3. Data Model Requirements
        print("\n3. DATA MODEL")
        print("-" * 40)
        
        # Reports and attributes
        report_query = """
            SELECT 
                r.report_id,
                r.report_name,
                COUNT(DISTINCT rd.attribute_id) as attribute_count,
                l.lob_name
            FROM reports r
            JOIN lobs l ON r.lob_id = l.lob_id
            LEFT JOIN regulatory_data_dictionaries rd ON r.report_id = rd.report_id
            WHERE r.is_active = true
            GROUP BY r.report_id, r.report_name, l.lob_name
            ORDER BY r.report_id
            LIMIT 10
        """
        reports = await conn.fetch(report_query)
        
        print(f"Sample reports with attributes:")
        total_attrs = 0
        for report in reports[:5]:
            print(f"  - {report['report_name']} ({report['lob_name']}): {report['attribute_count']} attributes")
            total_attrs += report['attribute_count']
            
        requirements["data_model"]["reports"] = len(reports)
        requirements["data_model"]["total_attributes"] = total_attrs
        
        # 4. Permission Structure
        print("\n4. PERMISSION STRUCTURE")
        print("-" * 40)
        
        perm_query = """
            SELECT 
                resource,
                COUNT(DISTINCT action) as action_count,
                COUNT(DISTINCT rp.role_id) as role_count
            FROM rbac_permissions p
            LEFT JOIN rbac_role_permissions rp ON p.id = rp.permission_id
            WHERE p.is_active = true
            GROUP BY resource
            ORDER BY COUNT(DISTINCT action) DESC
            LIMIT 10
        """
        permissions = await conn.fetch(perm_query)
        
        print("Permission resources:")
        for perm in permissions[:5]:
            print(f"  - {perm['resource']}: {perm['action_count']} actions, {perm['role_count']} roles")
            
        # 5. Test Cycle Configuration
        print("\n5. TEST CYCLE CONFIGURATION")
        print("-" * 40)
        
        cycle_query = """
            SELECT 
                tc.cycle_id,
                tc.cycle_name,
                COUNT(DISTINCT cr.report_id) as report_count,
                COUNT(DISTINCT crtc.test_case_id) as test_case_count
            FROM test_cycles tc
            LEFT JOIN cycle_reports cr ON tc.cycle_id = cr.cycle_id
            LEFT JOIN cycle_report_test_cases crtc ON cr.cycle_id = crtc.cycle_id 
                AND cr.report_id = crtc.report_id
            GROUP BY tc.cycle_id, tc.cycle_name
            ORDER BY tc.cycle_id DESC
            LIMIT 5
        """
        cycles = await conn.fetch(cycle_query)
        
        print("Recent test cycles:")
        for cycle in cycles:
            print(f"  - {cycle['cycle_name']}: {cycle['report_count']} reports, {cycle['test_case_count']} test cases")
            
        # 6. Data Dependencies
        print("\n6. CRITICAL DATA DEPENDENCIES")
        print("-" * 40)
        
        # Tables that must have data for system to function
        critical_tables = {
            'users': 'Authentication',
            'rbac_roles': 'Authorization',
            'rbac_permissions': 'Access control',
            'rbac_role_permissions': 'Role-permission mapping',
            'rbac_user_roles': 'User-role assignment',
            'lobs': 'Business units',
            'reports': 'Report definitions',
            'regulatory_data_dictionaries': 'Report attributes',
            'workflow_phases': 'Workflow structure',
            'activity_definitions': 'Phase activities',
            'test_cycles': 'Test cycle context',
            'cycle_reports': 'Cycle-report mapping'
        }
        
        for table, purpose in critical_tables.items():
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  - {table}: {count} records ({purpose})")
            requirements["configuration"][table] = count
            
        # Generate enhanced seed data recommendations
        print("\n" + "=" * 60)
        print("SEED DATA RECOMMENDATIONS")
        print("=" * 60)
        
        print("\n1. MINIMUM VIABLE SEED DATA:")
        print("   - 5 test users (one per major role)")
        print("   - 7 roles with full permission sets")
        print("   - All workflow phases (18) and activities (47)")
        print("   - At least 2 LOBs with 2-3 reports each")
        print("   - Sample attributes for each report (10-20 per report)")
        print("   - 1 active test cycle with cycle_reports")
        
        print("\n2. ENHANCED SEED DATA FOR TESTING:")
        print("   - Planning phase: PDE mappings, data sources")
        print("   - Data profiling: Sample rules and results")
        print("   - Scoping: Attribute decisions and versions")
        print("   - Sample selection: Sample records")
        print("   - Test execution: Test cases and results")
        print("   - Observations: Sample findings")
        
        # Save requirements summary
        output_file = Path(__file__).parent / "seed_requirements_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(requirements, f, indent=2, default=str)
            
        print(f"\nAnalysis saved to: {output_file}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(analyze_seed_requirements())