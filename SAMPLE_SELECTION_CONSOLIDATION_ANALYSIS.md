# Sample Selection Service Consolidation Analysis

## Current Services (7 files - THIS IS SPRAWL!)

1. **sample_selection_service.py** - Original service
2. **sample_selection_intelligent_service.py** - Intelligent sampling 
3. **sample_selection_intelligent_v2_service.py** - V2 of intelligent sampling
4. **enhanced_sample_selection_service.py** - Enhanced version
5. **sample_selection_enhanced_service.py** - Another enhanced version (duplicate?)
6. **sample_selection_phase_handler.py** - Phase status handler
7. **sample_set_versioning_service.py** - Versioning service

## Consolidation Plan

### Keep ONE Service: `sample_selection_service.py`
- Update it to use the new version tables
- Merge intelligent sampling features
- Include phase handling
- Remove all others

### What Each Service Does:
- **intelligent_service**: Distribution-based sampling
- **intelligent_v2_service**: Advanced sampling with data sources
- **enhanced_service**: More sampling features
- **phase_handler**: Updates phase status
- **versioning_service**: Version management

### Action Items:
1. Update main service to use version tables
2. Delete redundant services
3. Update endpoints to use consolidated service