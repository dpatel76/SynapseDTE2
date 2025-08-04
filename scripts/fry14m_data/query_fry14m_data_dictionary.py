"""Query regulatory data dictionary for FR Y-14M Schedule D.1 to get column definitions"""

import asyncio
from sqlalchemy import select, and_
from app.core.database import SessionLocal
from app.models.data_dictionary import RegulatoryDataDictionary
from typing import List, Dict

async def get_fry14m_schedule_d1_attributes() -> List[Dict]:
    """Fetch FR Y-14M Schedule D.1 attributes from regulatory_data_dictionaries table"""
    async with SessionLocal() as session:
        # Query for FR Y-14M Schedule D.1 attributes
        result = await session.execute(
            select(RegulatoryDataDictionary)
            .where(
                and_(
                    RegulatoryDataDictionary.form_name == "FR Y-14M",
                    RegulatoryDataDictionary.schedule_name == "Schedule D.1 - Loan Level Table"
                )
            )
            .order_by(RegulatoryDataDictionary.field_order)
        )
        
        attributes = result.scalars().all()
        
        # Convert to dictionary format for easier processing
        attribute_list = []
        for attr in attributes:
            attribute_list.append({
                'field_name': attr.field_name,
                'data_type': attr.data_type,
                'max_length': attr.max_length,
                'is_nullable': attr.is_nullable,
                'field_order': attr.field_order,
                'description': attr.description,
                'validation_rule': attr.validation_rule
            })
        
        return attribute_list

async def main():
    """Main function to query and display data dictionary"""
    attributes = await get_fry14m_schedule_d1_attributes()
    
    print(f"Found {len(attributes)} attributes for FR Y-14M Schedule D.1")
    print("\nAttribute Details:")
    print("-" * 100)
    
    for attr in attributes:
        print(f"Field: {attr['field_name']:<40} Type: {attr['data_type']:<15} "
              f"MaxLen: {attr['max_length'] or 'N/A':<10} Nullable: {attr['is_nullable']}")
    
    return attributes

if __name__ == "__main__":
    asyncio.run(main())