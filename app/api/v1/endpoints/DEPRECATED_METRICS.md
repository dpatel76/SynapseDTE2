# Metrics Endpoints Consolidation

## Overview

All metrics endpoints have been consolidated into `metrics_clean.py` following clean architecture patterns.

## Deprecated Files

The following files are now deprecated and should not be used for new development:

1. **metrics.py** - Original metrics implementation
2. **metrics_simple.py** - Simplified metrics for frontend compatibility
3. **metrics_v2.py** - Enhanced metrics with role-specific calculators

## Migration to metrics_clean.py

The consolidated `metrics_clean.py` provides:

### Clean Architecture Implementation
- Proper use cases in `app/application/use_cases/metrics.py`
- DTOs in `app/application/dtos/metrics.py`
- Separation of concerns between API, business logic, and data access

### All Required Endpoints
- `/dashboard/current-user` - Current user dashboard metrics
- `/dashboard/{role}` - Role-based dashboard metrics
- `/dashboard/{user_id}` - User-specific dashboard metrics (frontend compatibility)
- `/tester/{user_id}` - Tester-specific metrics
- `/report-owner/{user_id}` - Report owner metrics
- `/data-provider/{user_id}` - Data provider metrics
- `/phases/{phase_name}` - Phase-specific metrics
- `/analytics/system-wide` - System-wide analytics
- `/kpis/operational` - Operational KPIs
- `/kpis/quality` - Quality KPIs
- `/trends/performance` - Performance trends
- `/benchmarks/industry` - Industry benchmarks
- `/benchmarks/peers` - Peer comparison
- `/benchmarks/regulatory` - Regulatory benchmarks
- `/benchmarks/trends` - Benchmark trends
- `/reports/executive-summary` - Executive summary report
- `/health/benchmarking-service` - Benchmarking service health
- `/health/metrics-service` - Metrics service health

### Mock Data
Currently using mock data for all endpoints. Real implementation will be added when the full metrics service is implemented.

## Frontend Compatibility

The clean implementation maintains full compatibility with existing frontend code by providing the same endpoint paths and response structures.

## Next Steps

1. Implement real metrics calculations in the use cases
2. Connect to actual database queries
3. Add caching for performance optimization
4. Implement real-time metrics updates
5. Add metrics aggregation and historical tracking

## Removal Timeline

The deprecated files can be removed after:
1. All frontend code is verified to work with metrics_clean.py
2. All tests are updated
3. A full regression test is completed

Target removal date: End of current sprint