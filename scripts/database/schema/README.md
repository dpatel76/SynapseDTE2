# SynapseDTE Database Deployment Package

Generated: 2025-07-06 23:25:53

## Contents

- `complete_schema.sql` - Complete database schema (all tables, constraints, indexes)
- `seed_data.sql` - Essential seed data (roles, permissions, test users)
- `README.md` - This file

## Deployment Instructions

### Prerequisites

1. PostgreSQL 12+ installed
2. PostgreSQL client tools (psql)
3. Database user with CREATEDB privilege

### Quick Start

1. **Create database**:
   ```bash
   createdb -U postgres synapse_dt
   ```

2. **Load schema**:
   ```bash
   psql -U postgres -d synapse_dt -f complete_schema.sql
   ```

3. **Load seed data**:
   ```bash
   psql -U postgres -d synapse_dt -f seed_data.sql
   ```

### Using the Automated Script

If Python is available, use the automated script:

```bash
python create_database_from_schema.py
```

### Test Users

After deployment, these test users are available:

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | password123 | Admin |
| tester1@example.com | password123 | Tester |
| tester2@example.com | password123 | Tester |
| test.manager@example.com | password123 | Test Executive |
| report.owner@example.com | password123 | Report Owner |
| data.owner@example.com | password123 | Data Owner |

### Verification

After deployment, verify:

```sql
-- Check tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
-- Should return 126

-- Check users
SELECT email, role FROM users;

-- Check roles
SELECT role_name FROM roles;
```

### Troubleshooting

1. **Permission errors**: Ensure database user has necessary privileges
2. **Foreign key errors**: The seed_data.sql disables checks during import
3. **Duplicate key errors**: Data already exists, can be ignored

### Support

For issues, check:
- PostgreSQL logs
- Ensure correct PostgreSQL version (12+)
- Verify all files are present
