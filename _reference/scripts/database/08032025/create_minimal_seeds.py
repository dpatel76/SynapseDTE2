#!/usr/bin/env python3
"""
Create Minimal Seed Data
This script creates the minimum required seed data for a functional application.
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import uuid

class MinimalSeedGenerator:
    """Generate minimal seed data for application startup"""
    
    def __init__(self):
        self.output_dir = Path(__file__).parent / "minimal_seeds"
        self.output_dir.mkdir(exist_ok=True)
        self.now = datetime.utcnow()
        
    def generate_uuid(self):
        """Generate a UUID"""
        return str(uuid.uuid4())
        
    def hash_password(self, password: str) -> str:
        """Simple password hashing (should use bcrypt in production)"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def create_users(self):
        """Create essential users"""
        users = [
            {
                "user_id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": self.hash_password("admin123"),
                "first_name": "System",
                "last_name": "Administrator",
                "is_active": True,
                "is_admin": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "user_id": 2,
                "username": "report_owner",
                "email": "report.owner@example.com",
                "password_hash": self.hash_password("password123"),
                "first_name": "Report",
                "last_name": "Owner",
                "is_active": True,
                "is_admin": False,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "user_id": 3,
                "username": "tester",
                "email": "tester@example.com",
                "password_hash": self.hash_password("password123"),
                "first_name": "Test",
                "last_name": "User",
                "is_active": True,
                "is_admin": False,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "user_id": 4,
                "username": "data_owner",
                "email": "data.owner@example.com",
                "password_hash": self.hash_password("password123"),
                "first_name": "Data",
                "last_name": "Owner",
                "is_active": True,
                "is_admin": False,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "user_id": 5,
                "username": "data_executive",
                "email": "data.executive@example.com",
                "password_hash": self.hash_password("password123"),
                "first_name": "Data",
                "last_name": "Executive",
                "is_active": True,
                "is_admin": False,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            }
        ]
        
        self._save_data("users", users)
        return users
        
    def create_roles(self):
        """Create essential roles"""
        roles = [
            {
                "role_id": 1,
                "role_name": "Admin",
                "description": "System administrator with full access",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "role_id": 2,
                "role_name": "Report Owner",
                "description": "Owns and manages reports",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "role_id": 3,
                "role_name": "Tester",
                "description": "Performs testing activities",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "role_id": 4,
                "role_name": "Data Owner",
                "description": "Owns and manages data sources",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "role_id": 5,
                "role_name": "Data Executive",
                "description": "Executive oversight of data",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "role_id": 6,
                "role_name": "Viewer",
                "description": "Read-only access",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            }
        ]
        
        self._save_data("roles", roles)
        return roles
        
    def create_permissions(self):
        """Create essential permissions"""
        resources = [
            "users", "roles", "reports", "test_cycles", 
            "test_execution", "observations", "data_sources"
        ]
        actions = ["create", "read", "update", "delete", "approve"]
        
        permissions = []
        permission_id = 1
        
        for resource in resources:
            for action in actions:
                permissions.append({
                    "permission_id": permission_id,
                    "resource": resource,
                    "action": action,
                    "description": f"{action.capitalize()} {resource}",
                    "created_at": self.now.isoformat(),
                    "updated_at": self.now.isoformat()
                })
                permission_id += 1
                
        self._save_data("permissions", permissions)
        return permissions
        
    def create_role_permissions(self):
        """Create role-permission mappings"""
        mappings = []
        
        # Admin gets all permissions (IDs 1-35)
        for perm_id in range(1, 36):
            mappings.append({
                "role_id": 1,
                "permission_id": perm_id,
                "created_at": self.now.isoformat()
            })
            
        # Report Owner permissions
        report_owner_perms = [7, 8, 9, 12, 13, 17, 18, 22, 23]  # Read/update reports, read test cycles
        for perm_id in report_owner_perms:
            mappings.append({
                "role_id": 2,
                "permission_id": perm_id,
                "created_at": self.now.isoformat()
            })
            
        # Tester permissions
        tester_perms = [7, 12, 17, 18, 19, 22, 23, 24, 27, 28]  # Read reports, CRUD test execution
        for perm_id in tester_perms:
            mappings.append({
                "role_id": 3,
                "permission_id": perm_id,
                "created_at": self.now.isoformat()
            })
            
        # Viewer gets all read permissions
        for perm_id in [2, 7, 12, 17, 22, 27, 32]:  # All read permissions
            mappings.append({
                "role_id": 6,
                "permission_id": perm_id,
                "created_at": self.now.isoformat()
            })
            
        self._save_data("role_permissions", mappings)
        return mappings
        
    def create_user_roles(self):
        """Create user-role assignments"""
        assignments = [
            {"user_id": 1, "role_id": 1, "created_at": self.now.isoformat()},  # admin -> Admin
            {"user_id": 2, "role_id": 2, "created_at": self.now.isoformat()},  # report_owner -> Report Owner
            {"user_id": 3, "role_id": 3, "created_at": self.now.isoformat()},  # tester -> Tester
            {"user_id": 4, "role_id": 4, "created_at": self.now.isoformat()},  # data_owner -> Data Owner
            {"user_id": 5, "role_id": 5, "created_at": self.now.isoformat()},  # data_executive -> Data Executive
        ]
        
        self._save_data("user_roles", assignments)
        return assignments
        
    def create_lobs(self):
        """Create Lines of Business"""
        lobs = [
            {
                "lob_id": 1,
                "lob_name": "Consumer Banking",
                "lob_code": "CB",
                "description": "Consumer banking operations",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "lob_id": 2,
                "lob_name": "Commercial Banking",
                "lob_code": "CMB",
                "description": "Commercial banking operations",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "lob_id": 3,
                "lob_name": "Investment Banking",
                "lob_code": "IB",
                "description": "Investment banking operations",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            }
        ]
        
        self._save_data("lobs", lobs)
        return lobs
        
    def create_reports(self):
        """Create sample reports"""
        reports = [
            {
                "report_id": 1,
                "report_name": "FR Y-14M Schedule D.1",
                "report_code": "FRY14M-D1",
                "description": "Commercial Real Estate Loans",
                "frequency": "Monthly",
                "regulatory_framework": "Federal Reserve",
                "lob_id": 2,
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            },
            {
                "report_id": 2,
                "report_name": "FR Y-14Q Schedule A",
                "report_code": "FRY14Q-A",
                "description": "Retail Exposures",
                "frequency": "Quarterly",
                "regulatory_framework": "Federal Reserve",
                "lob_id": 1,
                "is_active": True,
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            }
        ]
        
        self._save_data("reports", reports)
        return reports
        
    def create_report_attributes(self):
        """Create sample report attributes"""
        attributes = []
        
        # Attributes for Report 1
        attr_names = [
            ("Reference Number", "REF001", True, True, False),
            ("Loan ID", "LOAN001", False, True, False),
            ("Borrower Name", "BORR001", False, False, False),
            ("Loan Amount", "AMT001", True, False, False),
            ("Interest Rate", "RATE001", False, False, False),
            ("Maturity Date", "MAT001", False, False, False),
            ("Property Type", "PROP001", False, False, False),
            ("Property Value", "VAL001", False, False, True),
        ]
        
        for i, (name, code, is_cde, is_pk, has_issues) in enumerate(attr_names, 1):
            attributes.append({
                "attribute_id": i,
                "report_id": 1,
                "attribute_name": name,
                "attribute_code": code,
                "data_type": "VARCHAR(255)",
                "is_mandatory": True,
                "is_cde": is_cde,
                "is_primary_key": is_pk,
                "has_known_issues": has_issues,
                "line_item_number": str(i),
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat()
            })
            
        self._save_data("report_attributes", attributes)
        return attributes
        
    def create_test_cycle(self):
        """Create a sample test cycle"""
        cycles = [{
            "cycle_id": 1,
            "cycle_name": "Q1 2024 Testing",
            "cycle_year": 2024,
            "cycle_quarter": 1,
            "start_date": (self.now - timedelta(days=30)).isoformat(),
            "end_date": (self.now + timedelta(days=30)).isoformat(),
            "status": "in_progress",
            "created_by_id": 1,
            "created_at": self.now.isoformat(),
            "updated_at": self.now.isoformat()
        }]
        
        self._save_data("test_cycles", cycles)
        return cycles
        
    def create_workflow_phases(self):
        """Create workflow phases"""
        phases = [
            {
                "phase_id": self.generate_uuid(),
                "phase_name": "Planning",
                "phase_order": 1,
                "description": "Planning phase for test execution",
                "is_active": True,
                "created_at": self.now.isoformat()
            },
            {
                "phase_id": self.generate_uuid(),
                "phase_name": "Data Profiling",
                "phase_order": 2,
                "description": "Data profiling and rule generation",
                "is_active": True,
                "created_at": self.now.isoformat()
            },
            {
                "phase_id": self.generate_uuid(),
                "phase_name": "Scoping",
                "phase_order": 3,
                "description": "Attribute scoping and selection",
                "is_active": True,
                "created_at": self.now.isoformat()
            },
            {
                "phase_id": self.generate_uuid(),
                "phase_name": "Sample Selection",
                "phase_order": 4,
                "description": "Sample selection for testing",
                "is_active": True,
                "created_at": self.now.isoformat()
            },
            {
                "phase_id": self.generate_uuid(),
                "phase_name": "Request Info",
                "phase_order": 5,
                "description": "Request for information",
                "is_active": True,
                "created_at": self.now.isoformat()
            },
            {
                "phase_id": self.generate_uuid(),
                "phase_name": "Test Execution",
                "phase_order": 6,
                "description": "Execute test cases",
                "is_active": True,
                "created_at": self.now.isoformat()
            },
            {
                "phase_id": self.generate_uuid(),
                "phase_name": "Observation Management",
                "phase_order": 7,
                "description": "Manage test observations",
                "is_active": True,
                "created_at": self.now.isoformat()
            }
        ]
        
        self._save_data("workflow_phases", phases)
        return phases
        
    def _save_data(self, table_name: str, data: list):
        """Save data to JSON file"""
        output_file = self.output_dir / f"{table_name}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "table": table_name,
                "row_count": len(data),
                "extracted_at": self.now.isoformat(),
                "data": data
            }, f, indent=2)
        print(f"Created {table_name}.json with {len(data)} records")
        
    def generate_all(self):
        """Generate all minimal seed data"""
        print("Generating minimal seed data...")
        
        self.create_users()
        self.create_roles()
        self.create_permissions()
        self.create_role_permissions()
        self.create_user_roles()
        self.create_lobs()
        self.create_reports()
        self.create_report_attributes()
        self.create_test_cycle()
        self.create_workflow_phases()
        
        # Generate SQL file
        self.generate_sql()
        
        print(f"\nMinimal seed data generated in: {self.output_dir}")
        
    def generate_sql(self):
        """Generate combined SQL file from JSON seeds"""
        sql_file = self.output_dir.parent / "03_minimal_seeds.sql"
        
        with open(sql_file, 'w') as f:
            f.write("-- Minimal Seed Data for SynapseDTE\n")
            f.write(f"-- Generated: {self.now}\n")
            f.write("-- This file contains the minimum data needed for a functional application\n\n")
            
            # Define insert order
            insert_order = [
                "users", "roles", "permissions", "role_permissions", "user_roles",
                "lobs", "reports", "report_attributes", "test_cycles", "workflow_phases"
            ]
            
            for table_name in insert_order:
                json_file = self.output_dir / f"{table_name}.json"
                if not json_file.exists():
                    continue
                    
                with open(json_file, 'r') as jf:
                    data = json.load(jf)
                    
                f.write(f"\n-- {table_name}\n")
                f.write(f"-- {len(data['data'])} records\n\n")
                
                for record in data['data']:
                    columns = []
                    values = []
                    
                    for col, val in record.items():
                        columns.append(col)
                        
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, bool):
                            values.append("TRUE" if val else "FALSE")
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            # Escape single quotes
                            val_str = str(val).replace("'", "''")
                            values.append(f"'{val_str}'")
                            
                    f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES\n")
                    f.write(f"  ({', '.join(values)});\n")
                    
        print(f"\nSQL file generated: {sql_file}")
        
def main():
    """Main execution"""
    generator = MinimalSeedGenerator()
    generator.generate_all()
    
if __name__ == "__main__":
    main()