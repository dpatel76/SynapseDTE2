# UUID Migration Implementation Checklist

## Pre-Migration Checklist

### Environment Setup
- [ ] Production database backup completed
- [ ] Test environment mirrors production
- [ ] Migration framework deployed
- [ ] Monitoring enhanced for migration metrics
- [ ] Rollback scripts tested in staging
- [ ] Team trained on procedures
- [ ] Communication plan activated

### Technical Prerequisites
- [ ] All PostgreSQL extensions installed (`uuid-ossp`)
- [ ] Database permissions verified
- [ ] Application feature flags configured
- [ ] Load balancer ready for maintenance mode
- [ ] Backup storage verified (3x current size)

## Phase 1: Foundation & Infrastructure (Week 1)

### Database Preparation
- [ ] Create `uuid_migration_mapping` table
- [ ] Create `uuid_migration_fk_backup` table
- [ ] Deploy UUID generation functions
- [ ] Create migration stored procedures
- [ ] Set up migration logging

### Application Preparation
- [ ] Deploy migration framework code
- [ ] Add feature flag support
- [ ] Create compatibility layer
- [ ] Update monitoring dashboards
- [ ] Deploy validation scripts

### Validation
- [ ] Framework installation verified
- [ ] Backup procedures tested
- [ ] Rollback procedures tested
- [ ] Team access verified
- [ ] Documentation updated

**Hold Point**: Review and approve before proceeding to Phase 2

## Phase 2: Leaf Tables Migration (Week 2)

### Target Tables
- [ ] `audit_logs`
- [ ] `llm_audit_logs`
- [ ] `configuration`
- [ ] `error_logs`
- [ ] Other standalone tables

### Migration Steps
- [ ] Backup target tables
- [ ] Add UUID columns
- [ ] Generate UUIDs for existing rows
- [ ] Store mappings
- [ ] Create UUID indexes
- [ ] Update primary keys
- [ ] Verify data integrity

### Code Updates
- [ ] Update model files
- [ ] Update service files
- [ ] Deploy compatibility code
- [ ] Update API endpoints
- [ ] Update tests

### Validation
- [ ] Row counts match
- [ ] No orphaned records
- [ ] Application functions normally
- [ ] Performance acceptable
- [ ] Rollback tested

**Hold Point**: Validate leaf table migration success

## Phase 3: User System Migration (Week 3-4) 🚨 CRITICAL

### Pre-Migration
- [ ] Schedule maintenance window
- [ ] Notify all stakeholders
- [ ] Disable user registrations
- [ ] Document active sessions
- [ ] Full system backup

### User Table Migration
- [ ] Add `uuid_id` column to users
- [ ] Generate UUIDs for all users
- [ ] Store user ID mappings
- [ ] Update all foreign keys (~50 tables)
- [ ] Verify constraint integrity

### Authentication Updates
- [ ] Update JWT token generation
- [ ] Update session management
- [ ] Update password reset flow
- [ ] Update API authentication
- [ ] Update frontend auth handling

### Dependent Systems
- [ ] Update RBAC tables
- [ ] Update assignment tables
- [ ] Update audit references
- [ ] Update activity logs
- [ ] Update all user foreign keys

### Critical Validation
- [ ] All users can login
- [ ] JWT tokens validate
- [ ] Sessions persist correctly
- [ ] Password reset works
- [ ] API authentication works
- [ ] No orphaned user references

**🚨 CRITICAL HOLD POINT**: Do not proceed without 100% authentication success

## Phase 4: Workflow Core Migration (Week 5-6)

### Core Tables
- [ ] `test_cycles`
- [ ] `reports`
- [ ] `workflow_phases`
- [ ] `cycle_reports` (composite key)
- [ ] `workflow_activities`

### Migration Steps
- [ ] Backup workflow tables
- [ ] Add UUID columns
- [ ] Resolve composite keys
- [ ] Update phase relationships
- [ ] Migrate temporal workflow IDs

### Workflow Validation
- [ ] Can create new cycles
- [ ] Can create new reports
- [ ] Phase transitions work
- [ ] Temporal workflows continue
- [ ] Historical data intact

**Hold Point**: Workflow functionality verified

## Phase 5: Attribute System & Consolidation (Week 7-8)

### Planning/Scoping Consolidation
- [ ] Add UUIDs to planning attributes
- [ ] Update scoping to use planning UUIDs
- [ ] Remove redundant scoping keys
- [ ] Update all attribute references
- [ ] Consolidate duplicate logic

### Attribute Migration
- [ ] `cycle_report_planning_attributes`
- [ ] `cycle_report_scoping_attributes`
- [ ] `planning_pde_mappings`
- [ ] `attribute_lob_assignments`
- [ ] Related mapping tables

### Code Consolidation
- [ ] Remove mapping services
- [ ] Simplify query logic
- [ ] Update frontend references
- [ ] Remove redundant APIs
- [ ] Update documentation

### Validation
- [ ] Planning phase works
- [ ] Scoping uses planning IDs
- [ ] No duplicate keys remain
- [ ] All workflows function
- [ ] Performance improved

**Hold Point**: Consolidation success verified

## Phase 6: Dependent Systems (Week 9)

### Remaining Tables
- [ ] Test execution tables
- [ ] Observation tables
- [ ] Sample selection tables
- [ ] RFI tables
- [ ] Data profiling tables

### System Integration
- [ ] External integrations updated
- [ ] Reporting systems updated
- [ ] Analytics queries updated
- [ ] Export functions updated
- [ ] Import functions updated

## Phase 7: Cleanup & Optimization (Week 10)

### Column Removal
- [ ] Drop all `legacy_*_id` columns
- [ ] Drop old integer ID columns
- [ ] Drop mapping tables (after backup)
- [ ] Remove compatibility code
- [ ] Remove feature flags

### Optimization
- [ ] Rebuild all indexes
- [ ] Update table statistics
- [ ] Vacuum all tables
- [ ] Optimize query plans
- [ ] Update connection pooling

### Final Validation
- [ ] Full system test
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Documentation complete
- [ ] Training complete

## Post-Migration Checklist

### Technical Tasks
- [ ] Remove migration framework
- [ ] Archive mapping data
- [ ] Update all documentation
- [ ] Close feature branches
- [ ] Update CI/CD pipelines

### Business Tasks
- [ ] Notify stakeholders of completion
- [ ] Document lessons learned
- [ ] Update disaster recovery plans
- [ ] Schedule retrospective
- [ ] Plan celebration! 🎉

## Emergency Contacts

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| Database Lead | TBD | email/phone | 24/7 during migration |
| Application Lead | TBD | email/phone | 24/7 during critical phases |
| DevOps Lead | TBD | email/phone | On-call |
| Business Sponsor | TBD | email/phone | Business hours |

## Critical Metrics to Monitor

### During Migration
- Database connection count
- Query execution time (p95)
- Error rate per minute
- Active user sessions
- API response time
- Memory usage
- Disk I/O

### Success Criteria
- Zero data loss
- <10% performance degradation
- 100% feature compatibility
- All tests passing
- No security vulnerabilities

## Rollback Triggers

Immediate rollback if:
- [ ] Data corruption detected
- [ ] >20% queries failing
- [ ] Authentication system failure
- [ ] Unrecoverable error in migration
- [ ] Performance degradation >50%

## Final Sign-offs

### Phase Completion Approvals
- [ ] Phase 1: Infrastructure ready - DBA Lead
- [ ] Phase 2: Leaf tables complete - Tech Lead
- [ ] Phase 3: User system migrated - CTO
- [ ] Phase 4: Workflow core done - Product Owner
- [ ] Phase 5: Consolidation complete - Architecture Lead
- [ ] Phase 6: All systems migrated - Tech Lead
- [ ] Phase 7: Cleanup complete - DBA Lead

### Final Project Approval
- [ ] Technical acceptance - CTO
- [ ] Business acceptance - Product Owner
- [ ] Go-live approval - Executive Sponsor

---

**Remember**: This is a critical system migration. Take time, validate thoroughly, and don't hesitate to rollback if issues arise. The goal is zero disruption to business operations.