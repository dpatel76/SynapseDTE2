#!/usr/bin/env python3
"""
Populate RBAC resources table
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import get_db
from app.models.rbac_resource import Resource
from app.core.rbac_config import RESOURCES
from app.core.logging import get_logger

logger = get_logger(__name__)


async def populate_resources():
    """Populate resources table from configuration"""
    async for db in get_db():
        try:
            print("\nPopulating RBAC Resources Table")
            print("=" * 50)
            
            created_count = 0
            
            for resource_name, config in RESOURCES.items():
                # Check if resource already exists
                existing = await db.execute(
                    select(Resource).where(Resource.resource_name == resource_name)
                )
                
                if not existing.scalar_one_or_none():
                    # Create resource
                    resource = Resource(
                        resource_name=resource_name,
                        display_name=config["display_name"],
                        description=config["description"],
                        resource_type=config["type"].value
                    )
                    db.add(resource)
                    created_count += 1
                    print(f"  Created: {resource_name} ({config['type'].value})")
                else:
                    print(f"  Exists: {resource_name}")
            
            await db.commit()
            
            print(f"\nCreated {created_count} new resources")
            
            # Show total resources
            result = await db.execute(select(Resource))
            all_resources = result.scalars().all()
            
            print(f"\nTotal resources in database: {len(all_resources)}")
            
            # Display resources by type
            by_type = {}
            for res in all_resources:
                if res.resource_type not in by_type:
                    by_type[res.resource_type] = []
                by_type[res.resource_type].append(res)
            
            print("\nResources by Type:")
            print("=" * 50)
            for res_type, resources in sorted(by_type.items()):
                print(f"\n{res_type.upper()}:")
                for res in sorted(resources, key=lambda x: x.resource_name):
                    print(f"  - {res.resource_name}: {res.display_name}")
            
            break
            
        except Exception as e:
            logger.error(f"Error populating resources: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(populate_resources())