#!/usr/bin/env python3
"""
E2E Test User Setup Script

Creates all required test users for the comprehensive E2E workflow test:
- test.manager@example.com (Test Executive)
- tester@example.com (Tester)
- report.owner@example.com (Report Owner)
- cdo@example.com (Data Executive)
- data.provider@example.com (Data Owner)

All users get password: password123
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
import bcrypt

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


class E2ETestUserSetup:
    """Setup test users for E2E testing"""
    
    def __init__(self):
        try:
            db_url = settings.database_url.replace('+asyncpg', '')
            self.engine = create_engine(db_url)
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.engine = None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def get_lob_id(self, conn) -> int:
        """Get first available LOB ID"""
        try:
            result = conn.execute(text("SELECT lob_id FROM lobs LIMIT 1"))
            lob_row = result.fetchone()
            return lob_row[0] if lob_row else 1
        except:
            return 1
    
    def create_test_users(self) -> bool:
        """Create all test users"""
        if not self.engine:
            return False
        
        print("👥 CREATING E2E TEST USERS")
        print("="*40)
        
        # Test users to create
        test_users = [
            {
                "first_name": "Test",
                "last_name": "Manager",
                "email": "test.manager@example.com",
                "role": "Test Executive",
                "phone": "555-0101"
            },
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "tester@example.com", 
                "role": "Tester",
                "phone": "555-0102"
            },
            {
                "first_name": "Report",
                "last_name": "Owner",
                "email": "report.owner@example.com",
                "role": "Report Owner",
                "phone": "555-0103"
            },
            {
                "first_name": "Chief Data",
                "last_name": "Officer",
                "email": "cdo@example.com",
                "role": "Data Executive",
                "phone": "555-0104"
            },
            {
                "first_name": "Data",
                "last_name": "Provider",
                "email": "data.provider@example.com",
                "role": "Data Owner",
                "phone": "555-0105"
            }
        ]
        
        password = "password123"
        hashed_password = self.hash_password(password)
        
        try:
            with self.engine.connect() as conn:
                # Get LOB ID
                lob_id = self.get_lob_id(conn)
                
                for user in test_users:
                    # Check if user already exists
                    check_result = conn.execute(
                        text("SELECT user_id FROM users WHERE email = :email"),
                        {"email": user["email"]}
                    )
                    
                    if check_result.fetchone():
                        print(f"✅ {user['email']} already exists")
                        continue
                    
                    # Create user
                    insert_query = text("""
                        INSERT INTO users (first_name, last_name, email, phone, role, lob_id, is_active, hashed_password, created_at, updated_at)
                        VALUES (:first_name, :last_name, :email, :phone, :role, :lob_id, :is_active, :hashed_password, :created_at, :updated_at)
                    """)
                    
                    conn.execute(insert_query, {
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "email": user["email"],
                        "phone": user["phone"],
                        "role": user["role"],
                        "lob_id": lob_id,
                        "is_active": True,
                        "hashed_password": hashed_password,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                    
                    print(f"✅ Created {user['email']} ({user['role']})")
                
                conn.commit()
                
                print(f"\n📋 Test User Summary:")
                print(f"   Password for all users: {password}")
                print(f"   LOB ID assigned: {lob_id}")
                
                return True
                
        except Exception as e:
            print(f"❌ Failed to create test users: {e}")
            return False
    
    def verify_test_users(self) -> bool:
        """Verify all test users exist and can authenticate"""
        if not self.engine:
            return False
        
        print("\n🔍 VERIFYING TEST USERS")
        print("-"*30)
        
        test_emails = [
            "test.manager@example.com",
            "tester@example.com", 
            "report.owner@example.com",
            "cdo@example.com",
            "data.provider@example.com"
        ]
        
        try:
            with self.engine.connect() as conn:
                for email in test_emails:
                    result = conn.execute(
                        text("SELECT user_id, first_name, last_name, role, is_active FROM users WHERE email = :email"),
                        {"email": email}
                    )
                    
                    user = result.fetchone()
                    if user:
                        user_id, first_name, last_name, role, is_active = user
                        status = "Active" if is_active else "Inactive"
                        print(f"✅ {email}: {first_name} {last_name} ({role}) - {status}")
                    else:
                        print(f"❌ {email}: Not found")
                        return False
                
                print("\n✅ All test users verified successfully")
                return True
                
        except Exception as e:
            print(f"❌ User verification failed: {e}")
            return False
    
    def setup_test_report_156(self) -> bool:
        """Ensure report 156 exists for testing"""
        if not self.engine:
            return False
        
        print("\n📊 VERIFYING TEST REPORT 156")
        print("-"*35)
        
        try:
            with self.engine.connect() as conn:
                # Check if report 156 exists
                result = conn.execute(
                    text("SELECT report_id, report_name, regulation FROM reports WHERE report_id = 156")
                )
                
                report = result.fetchone()
                if report:
                    report_id, report_name, regulation = report
                    print(f"✅ Report 156 exists: {report_name} ({regulation})")
                    return True
                else:
                    print("⚠️ Report 156 not found - creating test report...")
                    
                    # Create test report 156
                    insert_query = text("""
                        INSERT INTO reports (report_id, report_name, regulation, description, created_at, updated_at)
                        VALUES (:report_id, :report_name, :regulation, :description, :created_at, :updated_at)
                    """)
                    
                    conn.execute(insert_query, {
                        "report_id": 156,
                        "report_name": "FR Y-14M Schedule D1",
                        "regulation": "FR Y-14M",
                        "description": "Test report for E2E workflow testing",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                    
                    conn.commit()
                    print("✅ Created test report 156")
                    return True
                    
        except Exception as e:
            print(f"❌ Report 156 setup failed: {e}")
            return False


async def main():
    """Main setup function"""
    print("🏗️ E2E TEST ENVIRONMENT SETUP")
    print("="*50)
    print("Setting up test users and data for comprehensive E2E testing")
    print("="*50)
    
    setup = E2ETestUserSetup()
    
    # Create test users
    users_created = setup.create_test_users()
    if not users_created:
        print("❌ Failed to create test users")
        return False
    
    # Verify test users
    users_verified = setup.verify_test_users()
    if not users_verified:
        print("❌ Failed to verify test users")
        return False
    
    # Setup test report
    report_ready = setup.setup_test_report_156()
    if not report_ready:
        print("❌ Failed to setup test report")
        return False
    
    print("\n🎉 E2E TEST ENVIRONMENT SETUP COMPLETE!")
    print("\n📋 Ready for testing:")
    print("   • 5 test users created/verified")
    print("   • Report 156 available")
    print("   • Password: password123")
    print("\n🚀 Run E2E test with:")
    print("   python test/run_e2e_with_monitoring.py")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)