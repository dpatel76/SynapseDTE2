#!/usr/bin/env python3
"""Create scoping enum types in the database"""

import asyncio
from app.core.database import engine
from sqlalchemy import text

async def create_enums():
    async with engine.begin() as conn:
        # Create enum types
        enums_to_create = [
            ("scoping_tester_decision_enum", ["accept", "decline", "override"]),
            ("scoping_attribute_status_enum", ["pending", "submitted", "approved", "rejected", "needs_revision"]),
            ("scoping_report_owner_decision_enum", ["approved", "rejected", "pending", "needs_revision"]),
            ("scoping_version_status_enum", ["draft", "pending_approval", "approved", "rejected", "superseded"]),
        ]
        
        for enum_name, enum_values in enums_to_create:
            try:
                # Check if enum exists
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type 
                        WHERE typname = :enum_name
                    )
                """), {"enum_name": enum_name})
                exists = result.scalar()
                
                if not exists:
                    # Create enum
                    values_str = ", ".join([f"'{val}'" for val in enum_values])
                    await conn.execute(text(f"""
                        CREATE TYPE {enum_name} AS ENUM ({values_str})
                    """))
                    print(f"✅ Created enum: {enum_name}")
                else:
                    print(f"ℹ️  Enum already exists: {enum_name}")
            except Exception as e:
                print(f"❌ Error creating {enum_name}: {e}")
        
        print("\nEnum creation completed!")

if __name__ == "__main__":
    asyncio.run(create_enums())