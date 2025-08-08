#!/usr/bin/env python3
"""
Create Enhanced Seed Data for SynapseDTE
This creates comprehensive seed data for a fully functional system
"""

import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta, date
from pathlib import Path
import random

class EnhancedSeedGenerator:
    """Generate comprehensive seed data for testing"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent / "enhanced_seeds"
        self.output_dir.mkdir(exist_ok=True)
        self.now = datetime.now()
        
        # Password hash for 'password123'
        self.default_password_hash = self._hash_password('password123')
        
    def _hash_password(self, password: str) -> str:
        """Create SHA256 hash of password (simplified for seed data)"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def generate_all_seeds(self):
        """Generate all seed data files"""
        print("Generating enhanced seed data...")
        
        # 1. Core authentication data
        users = self._generate_users()
        roles = self._generate_roles()
        permissions = self._generate_permissions()
        role_permissions = self._generate_role_permissions(roles, permissions)
        user_roles = self._generate_user_roles(users, roles)
        
        # 2. Business structure
        lobs = self._generate_lobs()
        reports = self._generate_reports(lobs)
        attributes = self._generate_attributes(reports)
        
        # 3. Workflow configuration
        phases = self._generate_workflow_phases()
        activities = self._generate_activity_definitions()
        
        # 4. Test cycle data
        cycles = self._generate_test_cycles()
        cycle_reports = self._generate_cycle_reports(cycles, reports)
        
        # 5. Phase-specific data for testing
        planning_data = self._generate_planning_data(cycle_reports, attributes)
        profiling_data = self._generate_profiling_data(cycle_reports, attributes)
        scoping_data = self._generate_scoping_data(cycle_reports, attributes)
        sample_data = self._generate_sample_data(cycle_reports)
        test_data = self._generate_test_data(cycle_reports, attributes)
        observation_data = self._generate_observation_data(cycle_reports, test_data)
        
        # Generate SQL file
        self._generate_sql_file()
        
        print(f"\nEnhanced seed data generated in: {self.output_dir}")
        print("\nGenerated data summary:")
        print(f"  - Users: {len(users)}")
        print(f"  - Roles: {len(roles)}")
        print(f"  - Permissions: {len(permissions)}")
        print(f"  - LOBs: {len(lobs)}")
        print(f"  - Reports: {len(reports)}")
        print(f"  - Attributes: {len(attributes)}")
        print(f"  - Test Cycles: {len(cycles)}")
        print(f"  - Workflow Phases: {len(phases)}")
        print(f"  - Activities: {len(activities)}")
        
    def _generate_users(self):
        """Generate test users for all roles"""
        users = [
            # Authentication test user (from CLAUDE.md)
            {
                "user_id": 1,
                "email": "tester@example.com",
                "first_name": "Test",
                "last_name": "User",
                "hashed_password": self.default_password_hash,
                "role": "Tester",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            # Admin user
            {
                "user_id": 2,
                "email": "admin@example.com",
                "first_name": "System",
                "last_name": "Administrator",
                "hashed_password": self._hash_password('admin123'),
                "role": "Admin",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            # Report Owner
            {
                "user_id": 3,
                "email": "report.owner@example.com",
                "first_name": "Report",
                "last_name": "Owner",
                "hashed_password": self.default_password_hash,
                "role": "Report Owner",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            # Data Owner
            {
                "user_id": 4,
                "email": "data.owner@example.com",
                "first_name": "Data",
                "last_name": "Owner",
                "hashed_password": self.default_password_hash,
                "role": "Data Owner",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            # Data Executive
            {
                "user_id": 5,
                "email": "data.executive@example.com",
                "first_name": "Data",
                "last_name": "Executive",
                "hashed_password": self.default_password_hash,
                "role": "Data Executive",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            # Report Executive
            {
                "user_id": 6,
                "email": "report.executive@example.com",
                "first_name": "Report",
                "last_name": "Executive",
                "hashed_password": self.default_password_hash,
                "role": "Report Executive",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            # Test Executive
            {
                "user_id": 7,
                "email": "test.executive@example.com",
                "first_name": "Test",
                "last_name": "Executive",
                "hashed_password": self.default_password_hash,
                "role": "Test Executive",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            # Additional testers
            {
                "user_id": 8,
                "email": "tester2@example.com",
                "first_name": "Second",
                "last_name": "Tester",
                "hashed_password": self.default_password_hash,
                "role": "Tester",
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            }
        ]
        
        self._save_json("users.json", users)
        return users
        
    def _generate_roles(self):
        """Generate all system roles"""
        roles = [
            {"id": 1, "name": "Admin", "description": "System administrator with full access"},
            {"id": 2, "name": "Tester", "description": "Performs testing activities"},
            {"id": 3, "name": "Test Executive", "description": "Oversees testing process"},
            {"id": 4, "name": "Report Owner", "description": "Owns and manages reports"},
            {"id": 5, "name": "Report Executive", "description": "Executive oversight of reports"},
            {"id": 6, "name": "Data Owner", "description": "Owns and manages data sources"},
            {"id": 7, "name": "Data Executive", "description": "Executive oversight of data"},
            {"id": 8, "name": "Viewer", "description": "Read-only access"},
        ]
        
        for role in roles:
            role["is_active"] = True
            role["created_at"] = self.now.isoformat()
            role["updated_at"] = self.now.isoformat()
            
        self._save_json("rbac_roles.json", roles)
        return roles
        
    def _generate_permissions(self):
        """Generate comprehensive permissions"""
        resources = [
            'users', 'roles', 'permissions', 'reports', 'test_cycles',
            'test_execution', 'observations', 'data_sources', 'planning',
            'data_profiling', 'scoping', 'sample_selection', 'request_info',
            'workflow', 'audit_logs', 'documents', 'evidence'
        ]
        
        actions = ['create', 'read', 'update', 'delete', 'approve', 'execute', 'export']
        
        permissions = []
        perm_id = 1
        
        for resource in resources:
            for action in actions:
                # Not all resources need all actions
                if resource == 'audit_logs' and action in ['update', 'delete']:
                    continue
                if resource in ['workflow', 'evidence'] and action == 'delete':
                    continue
                    
                permissions.append({
                    "id": perm_id,
                    "resource": resource,
                    "action": action,
                    "description": f"{action.capitalize()} {resource}",
                    "is_active": True,
                    "created_at": self.now.isoformat(),
                    "updated_at": self.now.isoformat()
                })
                perm_id += 1
                
        self._save_json("rbac_permissions.json", permissions)
        return permissions
        
    def _generate_role_permissions(self, roles, permissions):
        """Map permissions to roles"""
        mappings = []
        mapping_id = 1
        
        # Admin gets all permissions
        admin_role = next(r for r in roles if r['name'] == 'Admin')
        for perm in permissions:
            mappings.append({
                "id": mapping_id,
                "role_id": admin_role['id'],
                "permission_id": perm['id'],
                "granted_at": self.now.isoformat(),
                "created_at": self.now.isoformat()
            })
            mapping_id += 1
            
        # Tester permissions
        tester_role = next(r for r in roles if r['name'] == 'Tester')
        tester_resources = ['test_execution', 'observations', 'evidence', 'documents']
        for perm in permissions:
            if perm['resource'] in tester_resources or perm['action'] == 'read':
                mappings.append({
                    "id": mapping_id,
                    "role_id": tester_role['id'],
                    "permission_id": perm['id'],
                    "granted_at": self.now.isoformat(),
                    "created_at": self.now.isoformat()
                })
                mapping_id += 1
                
        # Report Owner permissions
        report_owner = next(r for r in roles if r['name'] == 'Report Owner')
        owner_resources = ['reports', 'planning', 'scoping', 'data_profiling']
        for perm in permissions:
            if perm['resource'] in owner_resources or perm['action'] in ['read', 'approve']:
                mappings.append({
                    "id": mapping_id,
                    "role_id": report_owner['id'],
                    "permission_id": perm['id'],
                    "granted_at": self.now.isoformat(),
                    "created_at": self.now.isoformat()
                })
                mapping_id += 1
                
        self._save_json("rbac_role_permissions.json", mappings)
        return mappings
        
    def _generate_user_roles(self, users, roles):
        """Assign roles to users"""
        assignments = []
        assignment_id = 1
        
        # Map users to their roles
        role_mapping = {
            'tester@example.com': 'Tester',
            'admin@example.com': 'Admin',
            'report.owner@example.com': 'Report Owner',
            'data.owner@example.com': 'Data Owner',
            'data.executive@example.com': 'Data Executive',
            'report.executive@example.com': 'Report Executive',
            'test.executive@example.com': 'Test Executive',
            'tester2@example.com': 'Tester'
        }
        
        for user in users:
            role_name = role_mapping.get(user['email'])
            if role_name:
                role = next(r for r in roles if r['name'] == role_name)
                assignments.append({
                    "id": assignment_id,
                    "user_id": user['user_id'],
                    "role_id": role['id'],
                    "assigned_at": self.now.isoformat(),
                    "created_at": self.now.isoformat()
                })
                assignment_id += 1
                
        self._save_json("rbac_user_roles.json", assignments)
        return assignments
        
    def _generate_lobs(self):
        """Generate Lines of Business"""
        lobs = [
            {
                "lob_id": 1,
                "lob_name": "Consumer Banking",
                "lob_code": "CB",
                "description": "Consumer banking operations including retail accounts and loans",
                "is_active": True
            },
            {
                "lob_id": 2,
                "lob_name": "Commercial Banking",
                "lob_code": "CMB",
                "description": "Commercial banking operations for business clients",
                "is_active": True
            },
            {
                "lob_id": 3,
                "lob_name": "Investment Banking",
                "lob_code": "IB",
                "description": "Investment banking and capital markets",
                "is_active": True
            },
            {
                "lob_id": 4,
                "lob_name": "Wealth Management",
                "lob_code": "WM",
                "description": "Private wealth and asset management",
                "is_active": True
            }
        ]
        
        for lob in lobs:
            lob["created_at"] = self.now.isoformat()
            lob["updated_at"] = self.now.isoformat()
            
        self._save_json("lobs.json", lobs)
        return lobs
        
    def _generate_reports(self, lobs):
        """Generate regulatory reports"""
        reports = [
            {
                "report_id": 1,
                "report_name": "FR Y-14M Schedule D.1",
                "report_code": "FRY14M-D1",
                "description": "Commercial Real Estate Loans",
                "frequency": "Monthly",
                "regulatory_framework": "Federal Reserve",
                "lob_id": 2,  # Commercial Banking
                "is_active": True
            },
            {
                "report_id": 2,
                "report_name": "FR Y-14Q Schedule A",
                "report_code": "FRY14Q-A",
                "description": "Retail Exposures",
                "frequency": "Quarterly",
                "regulatory_framework": "Federal Reserve",
                "lob_id": 1,  # Consumer Banking
                "is_active": True
            },
            {
                "report_id": 3,
                "report_name": "FR Y-14Q Schedule B",
                "report_code": "FRY14Q-B",
                "description": "Securities Risk",
                "frequency": "Quarterly",
                "regulatory_framework": "Federal Reserve",
                "lob_id": 3,  # Investment Banking
                "is_active": True
            },
            {
                "report_id": 4,
                "report_name": "FFIEC 031 Schedule RC-C",
                "report_code": "FFIEC031-RCC",
                "description": "Loans and Lease Financing Receivables",
                "frequency": "Quarterly",
                "regulatory_framework": "FFIEC",
                "lob_id": 2,  # Commercial Banking
                "is_active": True
            }
        ]
        
        for report in reports:
            report["created_at"] = self.now.isoformat()
            report["updated_at"] = self.now.isoformat()
            
        self._save_json("reports.json", reports)
        return reports
        
    def _generate_attributes(self, reports):
        """Generate report attributes (regulatory data dictionary)"""
        attributes = []
        attr_id = 1
        
        # Common attribute templates
        common_attrs = [
            ("Reference Number", "REF", "VARCHAR(255)", True, True, True),
            ("Account ID", "ACCT", "VARCHAR(255)", True, False, True),
            ("Customer ID", "CUST", "VARCHAR(255)", True, False, False),
            ("Product Type", "PROD", "VARCHAR(100)", True, False, False),
            ("Balance Amount", "BAL", "DECIMAL(18,2)", True, True, False),
            ("Interest Rate", "RATE", "DECIMAL(5,4)", True, False, False),
            ("Origination Date", "ORIG_DT", "DATE", True, False, False),
            ("Maturity Date", "MAT_DT", "DATE", False, False, False),
            ("Risk Rating", "RISK", "VARCHAR(10)", True, False, False),
            ("Status", "STATUS", "VARCHAR(50)", True, False, False)
        ]
        
        for report in reports:
            # Add 15-20 attributes per report
            line_item = 1
            for i, (name, code, dtype, mandatory, is_cde, is_pk) in enumerate(common_attrs):
                attributes.append({
                    "attribute_id": attr_id,
                    "report_id": report['report_id'],
                    "attribute_name": f"{name} - {report['report_code']}",
                    "attribute_code": f"{code}_{report['report_id']:03d}",
                    "data_type": dtype,
                    "is_mandatory": mandatory,
                    "is_cde": is_cde,
                    "is_primary_key": is_pk,
                    "has_known_issues": random.choice([True, False]) if i > 5 else False,
                    "line_item_number": str(line_item),
                    "created_at": self.now.isoformat(),
                    "updated_at": self.now.isoformat()
                })
                attr_id += 1
                line_item += 1
                
            # Add report-specific attributes
            for j in range(5):
                attributes.append({
                    "attribute_id": attr_id,
                    "report_id": report['report_id'],
                    "attribute_name": f"Custom Field {j+1} - {report['report_code']}",
                    "attribute_code": f"CUST{j+1}_{report['report_id']:03d}",
                    "data_type": random.choice(["VARCHAR(255)", "DECIMAL(18,2)", "DATE", "INTEGER"]),
                    "is_mandatory": random.choice([True, False]),
                    "is_cde": False,
                    "is_primary_key": False,
                    "has_known_issues": random.choice([True, False]),
                    "line_item_number": str(line_item),
                    "created_at": self.now.isoformat(),
                    "updated_at": self.now.isoformat()
                })
                attr_id += 1
                line_item += 1
                
        self._save_json("regulatory_data_dictionaries.json", attributes)
        return attributes
        
    def _generate_workflow_phases(self):
        """Generate workflow phases"""
        phases = [
            ("Planning", 1, "Planning phase for test execution"),
            ("Data Profiling", 2, "Data profiling and rule generation"),
            ("Scoping", 3, "Attribute scoping and selection"),
            ("Sample Selection", 4, "Sample selection for testing"),
            ("Request Info", 5, "Request for information"),
            ("Test Execution", 6, "Execute test cases"),
            ("Observation Management", 7, "Manage test observations")
        ]
        
        phase_data = []
        for name, order, desc in phases:
            phase_data.append({
                "phase_id": str(uuid.uuid4()),
                "phase_name": name,
                "phase_order": order,
                "description": desc,
                "is_active": True,
                "created_at": self.now.isoformat()
            })
            
        self._save_json("workflow_phases.json", phase_data)
        return phase_data
        
    def _generate_activity_definitions(self):
        """Generate activity definitions for each phase"""
        activities = []
        activity_id = 1
        
        # Planning phase activities
        planning_activities = [
            ("Start Planning", "PLAN_START", "START", 1),
            ("Select Attributes", "PLAN_ATTR", "TASK", 2),
            ("Map Data Sources", "PLAN_MAP", "TASK", 3),
            ("Review Planning", "PLAN_REVIEW", "REVIEW", 4),
            ("Approve Planning", "PLAN_APPROVE", "APPROVAL", 5),
            ("Complete Planning", "PLAN_COMPLETE", "COMPLETE", 6)
        ]
        
        for name, code, atype, order in planning_activities:
            activities.append({
                "id": activity_id,
                "phase_name": "Planning",
                "activity_name": name,
                "activity_code": code,
                "activity_type": atype,
                "sequence_order": order,
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            })
            activity_id += 1
            
        # Add activities for other phases (simplified)
        for phase in ["Data Profiling", "Scoping", "Sample Selection", "Request Info", "Test Execution", "Observation Management"]:
            activities.extend([
                {
                    "id": activity_id,
                    "phase_name": phase,
                    "activity_name": f"Start {phase}",
                    "activity_code": f"{phase.upper().replace(' ', '_')}_START",
                    "activity_type": "START",
                    "sequence_order": 1,
                    "is_active": True,
                    "created_at": self.now.isoformat(),
                    "updated_at": self.now.isoformat()
                },
                {
                    "id": activity_id + 1,
                    "phase_name": phase,
                    "activity_name": f"Complete {phase}",
                    "activity_code": f"{phase.upper().replace(' ', '_')}_COMPLETE",
                    "activity_type": "COMPLETE",
                    "sequence_order": 2,
                    "is_active": True,
                    "created_at": self.now.isoformat(),
                    "updated_at": self.now.isoformat()
                }
            ])
            activity_id += 2
            
        self._save_json("activity_definitions.json", activities)
        return activities
        
    def _generate_test_cycles(self):
        """Generate test cycles"""
        cycles = [
            {
                "cycle_id": 1,
                "cycle_name": "Q1 2025 Testing",
                "cycle_year": 2025,
                "cycle_quarter": 1,
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "status": "in_progress",
                "created_by_id": 2,  # Admin
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "cycle_id": 2,
                "cycle_name": "Q4 2024 Testing",
                "cycle_year": 2024,
                "cycle_quarter": 4,
                "start_date": "2024-10-01",
                "end_date": "2024-12-31",
                "status": "completed",
                "created_by_id": 2,
                "created_at": (self.now - timedelta(days=90)).isoformat(),
                "updated_at": (self.now - timedelta(days=30)).isoformat()
            }
        ]
        
        self._save_json("test_cycles.json", cycles)
        return cycles
        
    def _generate_cycle_reports(self, cycles, reports):
        """Generate cycle-report mappings"""
        cycle_reports = []
        cr_id = 1
        
        # Map all reports to current cycle
        current_cycle = cycles[0]
        for report in reports:
            cycle_reports.append({
                "cycle_report_id": cr_id,
                "cycle_id": current_cycle['cycle_id'],
                "report_id": report['report_id'],
                "status": "in_progress",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            })
            cr_id += 1
            
        self._save_json("cycle_reports.json", cycle_reports)
        return cycle_reports
        
    def _generate_planning_data(self, cycle_reports, attributes):
        """Generate planning phase data"""
        # For brevity, just creating structure
        planning_attrs = []
        pde_mappings = []
        
        # Add some planning attributes
        for cr in cycle_reports[:2]:  # First 2 reports
            report_attrs = [a for a in attributes if a['report_id'] == cr['report_id']]
            for attr in report_attrs[:10]:  # First 10 attributes
                planning_attrs.append({
                    "planning_attr_id": len(planning_attrs) + 1,
                    "cycle_id": cr['cycle_id'],
                    "report_id": cr['report_id'],
                    "attribute_id": attr['attribute_id'],
                    "is_selected": True,
                    "created_at": self.now.isoformat()
                })
                
        self._save_json("cycle_report_planning_attributes.json", planning_attrs)
        return {"planning_attributes": planning_attrs, "pde_mappings": pde_mappings}
        
    def _generate_profiling_data(self, cycle_reports, attributes):
        """Generate data profiling rules"""
        rules = []
        rule_id = 1
        
        rule_templates = [
            ("Completeness Check", "not_null", "Completeness"),
            ("Range Validation", "range", "Validity"),
            ("Pattern Check", "pattern", "Accuracy"),
            ("Uniqueness Check", "unique", "Uniqueness")
        ]
        
        # Generate rules for first report's attributes
        for attr in attributes[:20]:
            for rule_name, rule_type, category in rule_templates:
                if random.random() > 0.5:  # 50% chance
                    rules.append({
                        "rule_id": rule_id,
                        "attribute_id": attr['attribute_id'],
                        "rule_name": f"{rule_name} - {attr['attribute_name']}",
                        "rule_type": rule_type,
                        "rule_category": category,
                        "rule_definition": json.dumps({"type": rule_type}),
                        "is_approved": random.choice([True, False]),
                        "created_at": self.now.isoformat()
                    })
                    rule_id += 1
                    
        self._save_json("cycle_report_data_profiling_rules.json", rules)
        return {"rules": rules}
        
    def _generate_scoping_data(self, cycle_reports, attributes):
        """Generate scoping decisions"""
        scoping_attrs = []
        
        for attr in attributes[:50]:
            scoping_attrs.append({
                "scoping_id": len(scoping_attrs) + 1,
                "attribute_id": attr['attribute_id'],
                "cycle_id": 1,
                "report_id": attr['report_id'],
                "tester_recommendation": random.choice(["Test", "Skip"]),
                "tester_decision": random.choice(["accept", "decline", "override"]),
                "is_scoped": random.choice([True, False]),
                "created_at": self.now.isoformat()
            })
            
        self._save_json("cycle_report_scoping_attributes.json", scoping_attrs)
        return {"scoping_attributes": scoping_attrs}
        
    def _generate_sample_data(self, cycle_reports):
        """Generate sample selection data"""
        samples = []
        sample_id = 1
        
        for cr in cycle_reports[:2]:
            for i in range(10):
                samples.append({
                    "sample_id": sample_id,
                    "cycle_id": cr['cycle_id'],
                    "report_id": cr['report_id'],
                    "sample_number": f"SAMP{sample_id:04d}",
                    "sample_category": random.choice(["normal", "anomaly", "high_risk"]),
                    "is_selected": True,
                    "created_at": self.now.isoformat()
                })
                sample_id += 1
                
        self._save_json("cycle_report_sample_selection_samples.json", samples)
        return {"samples": samples}
        
    def _generate_test_data(self, cycle_reports, attributes):
        """Generate test execution data"""
        test_cases = []
        test_results = []
        tc_id = 1
        tr_id = 1
        
        for cr in cycle_reports[:2]:
            report_attrs = [a for a in attributes if a['report_id'] == cr['report_id']][:5]
            
            for attr in report_attrs:
                # Create test case
                test_cases.append({
                    "test_case_id": tc_id,
                    "cycle_id": cr['cycle_id'],
                    "report_id": cr['report_id'],
                    "attribute_id": attr['attribute_id'],
                    "test_case_name": f"Test {attr['attribute_name']}",
                    "test_case_description": f"Validate {attr['attribute_name']} data quality",
                    "created_at": self.now.isoformat()
                })
                
                # Create test result
                test_results.append({
                    "result_id": tr_id,
                    "test_case_id": tc_id,
                    "execution_date": self.now.isoformat(),
                    "result": random.choice(["pass", "fail"]),
                    "executed_by_id": 1,  # Tester
                    "created_at": self.now.isoformat()
                })
                
                tc_id += 1
                tr_id += 1
                
        self._save_json("cycle_report_test_cases.json", test_cases)
        self._save_json("cycle_report_test_execution_results.json", test_results)
        return {"test_cases": test_cases, "test_results": test_results}
        
    def _generate_observation_data(self, cycle_reports, test_data):
        """Generate observations for failed tests"""
        observations = []
        obs_id = 1
        
        failed_tests = [r for r in test_data['test_results'] if r['result'] == 'fail']
        
        for result in failed_tests[:5]:
            test_case = next(tc for tc in test_data['test_cases'] 
                           if tc['test_case_id'] == result['test_case_id'])
            
            observations.append({
                "observation_id": obs_id,
                "cycle_id": test_case['cycle_id'],
                "report_id": test_case['report_id'],
                "test_case_id": test_case['test_case_id'],
                "observation_type": "data_quality",
                "title": f"Data Quality Issue - {test_case['test_case_name']}",
                "description": "Data validation failed for this attribute",
                "severity": random.choice(["low", "medium", "high"]),
                "status": "open",
                "created_by_id": 1,
                "created_at": self.now.isoformat()
            })
            obs_id += 1
            
        self._save_json("cycle_report_observation_mgmt_observation_records.json", observations)
        return {"observations": observations}
        
    def _save_json(self, filename, data):
        """Save data to JSON file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _generate_sql_file(self):
        """Generate combined SQL file"""
        sql_file = self.output_dir.parent / "04_enhanced_seeds.sql"
        
        with open(sql_file, 'w') as f:
            f.write("-- Enhanced Seed Data for SynapseDTE\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write("-- This file contains comprehensive seed data for full system functionality\n\n")
            
            # Order of insertion based on dependencies
            table_order = [
                'users',
                'lobs',
                'rbac_roles',
                'rbac_permissions',
                'rbac_role_permissions',
                'rbac_user_roles',
                'reports',
                'regulatory_data_dictionaries',
                'workflow_phases',
                'activity_definitions',
                'test_cycles',
                'cycle_reports',
                'cycle_report_planning_attributes',
                'cycle_report_data_profiling_rules',
                'cycle_report_scoping_attributes',
                'cycle_report_sample_selection_samples',
                'cycle_report_test_cases',
                'cycle_report_test_execution_results',
                'cycle_report_observation_mgmt_observation_records'
            ]
            
            for table in table_order:
                json_file = self.output_dir / f"{table}.json"
                if json_file.exists():
                    with open(json_file, 'r') as jf:
                        data = json.load(jf)
                        
                    if data:
                        f.write(f"\n-- {table}\n")
                        f.write(f"-- {len(data)} records\n\n")
                        
                        for record in data:
                            columns = list(record.keys())
                            values = []
                            
                            for col, val in record.items():
                                if val is None:
                                    values.append("NULL")
                                elif isinstance(val, bool):
                                    values.append("TRUE" if val else "FALSE")
                                elif isinstance(val, (int, float)):
                                    values.append(str(val))
                                else:
                                    val_str = str(val).replace("'", "''")
                                    values.append(f"'{val_str}'")
                                    
                            f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n")
                            f.write(f"  ({', '.join(values)});\n")
                            
        print(f"\nSQL file generated: {sql_file}")

if __name__ == "__main__":
    generator = EnhancedSeedGenerator()
    generator.generate_all_seeds()