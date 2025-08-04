"""
Load FR Y-14M regulatory data dictionary from RegDD14M.py
"""

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.data_dictionary import RegulatoryDataDictionary
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_fr_y14m_data_elements():
    """Get all FR Y-14M data elements from RegDD14M.py"""
    try:
        # Add the frontend/util directory to Python path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        regdd_path = os.path.join(project_root, 'frontend', 'util')
        
        if regdd_path not in sys.path:
            sys.path.insert(0, regdd_path)
        
        # Import and use the RegDD14M module
        from RegDD14M import FRY14MDictionaryExtractor
        
        extractor = FRY14MDictionaryExtractor()
        elements = extractor.create_master_dictionary()
        
        logger.info(f"Loaded {len(elements)} elements from RegDD14M.py")
        return elements
        
    except ImportError as e:
        logger.error(f"Could not import RegDD14M module: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading data from RegDD14M.py: {e}")
        return []


async def load_fr_y14m_data_dictionary(clear_existing: bool = False, session: AsyncSession = None):
    """
    Load FR Y-14M regulatory data dictionary from RegDD14M.py data elements
    
    Args:
        clear_existing: Whether to clear existing entries before loading
        session: Optional database session. If not provided, creates a new one.
    """
    # Use provided session or create new one
    if session:
        # Use provided session - don't commit/rollback
        try:
            if clear_existing:
                await session.execute(text("DELETE FROM regulatory_data_dictionary"))
                logger.info("Cleared existing regulatory data dictionary entries")
            
            # Get all data elements from RegDD14M.py
            all_elements = get_fr_y14m_data_elements()
            
            if not all_elements:
                logger.error("No data elements loaded from RegDD14M.py")
                return {"total_loaded": 0, "schedules_loaded": []}
            
            total_loaded = 0
            schedules_loaded = set()
            
            for element_data in all_elements:
                # Extract data from the RegDD14M format
                report_name = element_data.get('Report Name', 'FR Y-14M')
                schedule_name = element_data.get('Schedule Name', '')
                line_item_number = str(element_data.get('Line Item #', ''))
                line_item_name = element_data.get('Line Item Name', '')
                technical_line_item_name = element_data.get('Technical Line Item Name', '')
                mdrm = element_data.get('MDRM', '')
                description = element_data.get('Description', '')
                static_or_dynamic = element_data.get('Static or Dynamic', '')
                mandatory_or_optional = element_data.get('Mandatory or Optional', '')
                format_specification = element_data.get('Format', '')
                num_reports_schedules = str(element_data.get('# of reports or schedules used in', '1'))
                other_schedule_reference = element_data.get('Other Schedule Reference', '')
                
                # Create regulatory data dictionary entry
                entry = RegulatoryDataDictionary(
                    report_name=report_name[:100] if report_name else None,
                    schedule_name=schedule_name[:200] if schedule_name else None,
                    line_item_number=line_item_number[:20] if line_item_number else None,
                    line_item_name=line_item_name[:255] if line_item_name else None,
                    technical_line_item_name=technical_line_item_name[:255] if technical_line_item_name else None,
                    mdrm=mdrm[:50] if mdrm else None,
                    description=description[:500] if description else None,
                    static_or_dynamic=static_or_dynamic[:20] if static_or_dynamic else None,
                    mandatory_or_optional=mandatory_or_optional[:20] if mandatory_or_optional else None,
                    format_specification=format_specification[:100] if format_specification else None,
                    num_reports_schedules_used=num_reports_schedules[:10] if num_reports_schedules else None,
                    other_schedule_reference=other_schedule_reference[:200] if other_schedule_reference else None,
                    is_active=True
                )
                
                session.add(entry)
                total_loaded += 1
                schedules_loaded.add(schedule_name)
            
            # No commit - let the endpoint/get_db handle it
            logger.info(f"Successfully loaded {total_loaded} FR Y-14M data dictionary entries")
            
            return {
                "total_loaded": total_loaded,
                "schedules_loaded": list(schedules_loaded)
            }
            
        except Exception as e:
            # No rollback - let the endpoint/get_db handle it
            logger.error(f"Error loading FR Y-14M data dictionary: {e}")
            raise
    else:
        # Create our own session and handle everything
        async with AsyncSessionLocal() as new_session:
            try:
                if clear_existing:
                    await new_session.execute(text("DELETE FROM regulatory_data_dictionary"))
                    logger.info("Cleared existing regulatory data dictionary entries")
                
                # Get all data elements from RegDD14M.py
                all_elements = get_fr_y14m_data_elements()
                
                if not all_elements:
                    logger.error("No data elements loaded from RegDD14M.py")
                    return {"total_loaded": 0, "schedules_loaded": []}
                
                total_loaded = 0
                schedules_loaded = set()
                
                for element_data in all_elements:
                    # Extract data from the RegDD14M format
                    report_name = element_data.get('Report Name', 'FR Y-14M')
                    schedule_name = element_data.get('Schedule Name', '')
                    line_item_number = str(element_data.get('Line Item #', ''))
                    line_item_name = element_data.get('Line Item Name', '')
                    technical_line_item_name = element_data.get('Technical Line Item Name', '')
                    mdrm = element_data.get('MDRM', '')
                    description = element_data.get('Description', '')
                    static_or_dynamic = element_data.get('Static or Dynamic', '')
                    mandatory_or_optional = element_data.get('Mandatory or Optional', '')
                    format_specification = element_data.get('Format', '')
                    num_reports_schedules = str(element_data.get('# of reports or schedules used in', '1'))
                    other_schedule_reference = element_data.get('Other Schedule Reference', '')
                    
                    # Create regulatory data dictionary entry
                    entry = RegulatoryDataDictionary(
                        report_name=report_name[:100] if report_name else None,
                        schedule_name=schedule_name[:200] if schedule_name else None,
                        line_item_number=line_item_number[:20] if line_item_number else None,
                        line_item_name=line_item_name[:255] if line_item_name else None,
                        technical_line_item_name=technical_line_item_name[:255] if technical_line_item_name else None,
                        mdrm=mdrm[:50] if mdrm else None,
                        description=description[:500] if description else None,
                        static_or_dynamic=static_or_dynamic[:20] if static_or_dynamic else None,
                        mandatory_or_optional=mandatory_or_optional[:20] if mandatory_or_optional else None,
                        format_specification=format_specification[:100] if format_specification else None,
                        num_reports_schedules_used=num_reports_schedules[:10] if num_reports_schedules else None,
                        other_schedule_reference=other_schedule_reference[:200] if other_schedule_reference else None,
                        is_active=True
                    )
                    
                    new_session.add(entry)
                    total_loaded += 1
                    schedules_loaded.add(schedule_name)
                
                # Commit our own session
                await new_session.commit()
                logger.info(f"Successfully loaded {total_loaded} FR Y-14M data dictionary entries")
                
                return {
                    "total_loaded": total_loaded,
                    "schedules_loaded": list(schedules_loaded)
                }
                
            except Exception as e:
                await new_session.rollback()
                logger.error(f"Error loading FR Y-14M data dictionary: {e}")
                raise


def load_fr_y14m_data_dictionary_sync(clear_existing: bool = False):
    """Synchronous wrapper for loading data dictionary"""
    return asyncio.run(load_fr_y14m_data_dictionary(clear_existing, session=None)) 