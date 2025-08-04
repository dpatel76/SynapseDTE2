# Async Pattern Enforcement Strategy

## How to Ensure All Agents Review These Learnings

### 1. Documentation Hierarchy
```
🚨 CRITICAL DOCS (Must Read)
├── /docs/TROUBLESHOOTING_PLANNING_JOBS.md (4+ hours of debugging lessons)
├── /AGENT_REVIEW_CHECKLIST.md (Quick reference)
└── /CLAUDE.md (Section: Background Jobs & Async Operations)

📚 SUPPORTING DOCS
├── /docs/README.md (Documentation index with critical section at top)
└── /scripts/check_async_patterns.py (Automated checker)
```

### 2. Multiple Touchpoints for Discovery

#### A. CLAUDE.md Integration ✅
- Added dedicated section "Background Jobs & Async Operations"
- Placed after main content for visibility
- Includes quick patterns and references to detailed docs

#### B. Documentation Index ✅
- `/docs/README.md` now has CRITICAL section at the very top
- Highlighted with emojis and bold text
- Shows time saved (4+ hours) to emphasize importance

#### C. Agent Review Checklist ✅
- Standalone checklist at project root
- Quick reference format
- Pre-implementation and code review checklists

#### D. Automated Pattern Checker ✅
- `scripts/check_async_patterns.py`
- Can be integrated into pre-commit hooks
- Catches common mistakes automatically

### 3. Enforcement Mechanisms

#### Immediate Actions
1. **For AI Agents (Claude, etc.)**
   - CLAUDE.md is automatically loaded
   - Critical section prominently placed
   - Direct references to detailed docs

2. **For Human Developers**
   - Documentation index shows critical docs first
   - Time saved metric (4+ hours) creates urgency
   - Checklist provides quick validation

#### Future Integration Options
1. **Pre-commit Hook**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: local
       hooks:
         - id: check-async-patterns
           name: Check Async Patterns
           entry: python scripts/check_async_patterns.py
           language: python
           files: '\.py$'
   ```

2. **CI/CD Pipeline**
   ```yaml
   # .github/workflows/async-check.yml
   - name: Check Async Patterns
     run: python scripts/check_async_patterns.py
   ```

3. **Code Review Template**
   ```markdown
   ## Async Pattern Checklist
   - [ ] Reviewed /docs/TROUBLESHOOTING_PLANNING_JOBS.md?
   - [ ] Followed patterns in AGENT_REVIEW_CHECKLIST.md?
   - [ ] Ran check_async_patterns.py?
   - [ ] DB objects loaded in async task session?
   - [ ] Job status updated to "running"?
   - [ ] Timestamps updated?
   ```

### 4. Key Learnings Summary

#### Top 5 Issues (By Time Spent)
1. **SQLAlchemy Session Management** (2+ hours)
   - Objects loaded outside async task are detached
   - Must reload in task session

2. **Job Status Not Updating** (1 hour)
   - Jobs stuck on "pending"
   - Must update to "running" immediately

3. **Wrong Job Manager Method** (30 min)
   - `update_job_status` doesn't exist
   - Use `update_job_progress` with status param

4. **Missing Timestamps** (30 min)
   - `updated_at` not set
   - Must explicitly update on modifications

5. **Phase ID Construction** (20 min)
   - Don't construct phase_id
   - Always query from database

### 5. Metrics for Success

Track adoption through:
- Reduction in async-related bugs
- Faster PR reviews (checklist compliance)
- Fewer debugging sessions for similar issues
- Pattern checker warnings decreasing over time

### 6. Communication Plan

1. **Immediate**
   - This document serves as the communication
   - All critical docs are updated and linked

2. **Ongoing**
   - Include in onboarding materials
   - Reference in PR reviews
   - Update patterns as new issues discovered

### 7. Maintenance

- Review and update quarterly
- Add new patterns as discovered
- Remove obsolete patterns
- Track which patterns prevent most issues

## Conclusion

The strategy ensures multiple discovery paths:
- AI agents see it in CLAUDE.md
- Developers see it in docs/README.md
- Automated tools catch violations
- Checklists provide quick validation

Time investment in reading: ~30 minutes
Time saved per developer: ~4+ hours
ROI: 8x minimum