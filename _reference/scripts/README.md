# Scripts Directory

This directory contains all utility scripts organized by function and purpose.

## Directory Structure

### `/infrastructure/` (18 files)
Scripts for starting, stopping, and managing services:
- Service start/stop/restart scripts
- Worker management scripts
- Environment setup scripts

### `/debug/` (89 files)
Scripts for debugging, checking, and verifying system state:
- Check and verify scripts
- Debug utilities
- System validation scripts
- Demo and example scripts

### `/testing/` (125 files)
Testing scripts and test utilities:
- Comprehensive test suites
- End-to-end testing scripts
- Unit test utilities
- Test data validation

### `/utils/` (69 files)
General utility and maintenance scripts:
- Fix and repair scripts
- Cleanup utilities
- Update and maintenance scripts
- Permission management scripts

### `/setup/` (21 files)
Setup and initialization scripts:
- User creation scripts
- Test data creation
- Database setup utilities
- Initial configuration scripts

### `/migration/` (23 files)
Database migration and architecture migration scripts:
- Alembic migration utilities
- Clean Architecture migration scripts
- RBAC migration scripts
- Permission setup scripts

## Usage Guidelines

1. **Infrastructure Scripts**: Use for managing the application lifecycle
2. **Debug Scripts**: Use for troubleshooting and system verification
3. **Testing Scripts**: Use for running comprehensive tests
4. **Utils Scripts**: Use for maintenance and cleanup operations
5. **Setup Scripts**: Use for initial setup and configuration
6. **Migration Scripts**: Use for database and architecture changes

## Key Infrastructure Scripts

- `start_all_services.sh` - Start all services
- `stop_all_services.sh` - Stop all services
- `restart_backend.sh` - Restart backend only
- `restart_frontend.sh` - Restart frontend only

## Important Setup Scripts

- `setup_database.py` - Initialize database
- `create_all_test_users.py` - Create test users
- `create_comprehensive_test_data.py` - Create test data

Total Scripts Organized: 345 files