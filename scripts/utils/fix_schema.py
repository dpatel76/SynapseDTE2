import asyncio
import asyncpg

async def fix_schema():
    conn = await asyncpg.connect('postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
    
    # Add the missing columns
    columns_to_add = [
        'validation_rules',
        'typical_source_documents', 
        'keywords_to_look_for',
        'testing_approach'
    ]
    
    print("Adding missing columns to report_attributes table...")
    
    for column in columns_to_add:
        try:
            await conn.execute(f'ALTER TABLE report_attributes ADD COLUMN {column} TEXT')
            print(f"✅ Added column: {column}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"⚠️  Column {column} already exists, skipping")
            else:
                print(f"❌ Failed to add column {column}: {e}")
    
    # Verify the changes
    result = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'report_attributes' 
        ORDER BY ordinal_position
    """)
    
    print("\nUpdated report_attributes table schema:")
    print("="*50)
    for row in result:
        print(f"{row['column_name']}: {row['data_type']}")
    
    await conn.close()
    print("\n✅ Schema fix completed!")

if __name__ == "__main__":
    asyncio.run(fix_schema()) 