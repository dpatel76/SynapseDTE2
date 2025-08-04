# SynapseDTE Comprehensive E2E Test Suite

## 🎯 **Overview**

This comprehensive End-to-End test suite validates the complete 9-phase testing workflow in SynapseDTE, covering all user roles and system interactions. The test simulates real-world usage from test cycle creation through final approval.

## 📋 **Test Coverage**

### **9 Testing Phases Covered:**
1. **Planning** - Tester creates comprehensive test plan
2. **Scoping** - Tester defines test scope and selects attributes
3. **Sample Selection** - Tester generates and approves test samples
4. **Data Owner Assignment** - CDO assigns data owners to attributes
5. **Request Information** - Data Provider submits source information
6. **Test Execution** - Tester performs actual testing with LLM assistance
7. **Observation Management** - Tester creates and submits observations
8. **Generate Test Report** - System generates comprehensive report
9. **Final Review** - Report Owner reviews and approves

### **5 User Roles Tested:**
- **Test Executive** (`test.manager@example.com`) - Creates cycles, assigns reports
- **Tester** (`tester@example.com`) - Executes testing workflow
- **Report Owner** (`report.owner@example.com`) - Reviews and approves
- **Data Executive** (`cdo@example.com`) - Manages data owner assignments
- **Data Owner** (`data.provider@example.com`) - Provides source information

### **System Components Validated:**
- ✅ User authentication and RBAC
- ✅ Workflow state transitions
- ✅ Background job processing (LLM, report generation)
- ✅ Database state changes
- ✅ API performance and error handling
- ✅ Real-time monitoring and logging

## 🚀 **Quick Start**

### **Prerequisites**
1. **Backend running**: `uvicorn app.main:app --reload`
2. **Database accessible**: PostgreSQL with all tables
3. **Python dependencies**: `aiohttp`, `sqlalchemy`, `bcrypt`

### **One-Command Execution**
```bash
# Setup test users and run complete E2E test with monitoring
python test/setup_e2e_test_users.py && python test/run_e2e_with_monitoring.py
```

## 📚 **Detailed Execution Guide**

### **Step 1: Environment Setup**
```bash
# Create test users (one-time setup)
python test/setup_e2e_test_users.py
```

**What this creates:**
- 5 test users with role assignments
- Test Report 156 (if not exists)
- Verifies database connectivity

### **Step 2: Run Complete Test Suite**
```bash
# Run E2E test with comprehensive monitoring
python test/run_e2e_with_monitoring.py
```

**What this includes:**
- System health verification
- Real-time monitoring (logs, API, database)
- Complete 9-phase workflow execution
- Performance tracking
- Final comprehensive report

### **Step 3: Individual Component Testing** *(Optional)*

#### **Run E2E Test Only:**
```bash
python test/comprehensive_e2e_workflow_test.py
```

#### **Run Monitoring Only:**
```bash
python test/test_monitor.py
```

#### **Database Status Check:**
```bash
python test/current_vs_migration_comparison.md
```

## 📊 **Monitoring & Validation**

### **Real-Time Monitoring Includes:**
- 📄 **Backend Log Analysis** - Errors, warnings, workflow events
- 🌐 **API Health Monitoring** - Response times, error rates
- 🗄️ **Database State Tracking** - Table row changes, transactions
- ⚙️ **Background Job Progress** - LLM processing, report generation
- 📈 **Performance Metrics** - Response times, system health

### **State Transition Validation:**
The test validates proper state transitions through all phases:
```
Planning: not_started → in_progress → completed
Scoping: not_started → in_progress → pending_review → completed
Sample Selection: not_started → in_progress → completed
...and so on for all 9 phases
```

### **Background Job Monitoring:**
- ✅ LLM attribute generation jobs
- ✅ Sample generation processing
- ✅ Test case creation
- ✅ Report generation tasks
- ✅ Email notification jobs

## 📋 **Test Data & Scenarios**

### **Reference Data Used:**
- **Test Cycle**: Dynamically created with timestamp
- **Report**: 156 (FR Y-14M Schedule D1)
- **Attributes**: First 10 from Report 156
- **Samples**: 50 records with stratified sampling
- **Test Cases**: Completeness, accuracy, validity, consistency

### **Realistic Test Scenarios:**
- ✅ **Happy Path**: All phases complete successfully
- ✅ **Failure Handling**: Test failures create observations
- ✅ **Approval Workflows**: Multi-level approvals
- ✅ **Background Processing**: Long-running jobs
- ✅ **State Management**: Complex workflow transitions

## 📄 **Output & Reports**

### **Generated Files:**
```
test/
├── e2e_test_execution.log          # Detailed test execution log
├── e2e_execution_report.json       # Comprehensive test report
├── current_vs_migration_comparison.md  # Database analysis
└── monitoring output (console)     # Real-time monitoring data
```

### **Final Report Includes:**
- ✅ Test execution summary (pass/fail)
- ✅ Duration and timing analysis
- ✅ Phase completion status
- ✅ API performance metrics
- ✅ Error count and details
- ✅ Background job tracking
- ✅ Database state changes

## 🔧 **Troubleshooting**

### **Common Issues & Solutions:**

#### **"Backend not accessible"**
```bash
# Start the backend
uvicorn app.main:app --reload --port 8000
```

#### **"Test users not found"**
```bash
# Create test users
python test/setup_e2e_test_users.py
```

#### **"Report 156 not found"**
```bash
# The setup script creates Report 156 automatically
python test/setup_e2e_test_users.py
```

#### **"Database connection failed"**
```bash
# Check database configuration in .env
DATABASE_URL=postgresql://user:pass@localhost:5432/synapse_dt

# Verify database is running
pg_isready -h localhost -p 5432
```

#### **"Permission denied errors"**
```bash
# Ensure log directory is writable
chmod 755 test/
```

### **Debug Mode:**
For detailed debugging, monitor the log files in real-time:
```bash
# In separate terminals:
tail -f test/e2e_test_execution.log
tail -f backend.log
```

## 📈 **Performance Expectations**

### **Typical Execution Times:**
- **System Health Check**: 10-15 seconds
- **User Authentication**: 2-3 seconds per user
- **Each Phase Execution**: 5-30 seconds
- **Background Jobs**: 30-180 seconds (LLM processing)
- **Total Test Duration**: 10-20 minutes

### **Resource Usage:**
- **CPU**: Moderate during LLM processing
- **Memory**: ~500MB for test execution
- **Network**: API calls every 3-15 seconds
- **Database**: 100+ insert/update operations

### **Success Criteria:**
- ✅ All 9 phases complete successfully
- ✅ Zero critical errors in logs
- ✅ All state transitions valid
- ✅ Background jobs complete
- ✅ Final approval recorded

## 🎉 **Success Validation**

The test is considered **SUCCESSFUL** when:

1. **All 9 phases complete** with proper state transitions
2. **No critical errors** in backend logs
3. **All background jobs finish** successfully
4. **Final workflow status** = "completed"
5. **Test report generated** and approved
6. **Observations created and approved** for any failures

## 🔬 **Test Architecture**

### **Core Components:**
```
run_e2e_with_monitoring.py     # Main orchestrator
├── comprehensive_e2e_workflow_test.py  # E2E test logic
├── test_monitor.py            # System monitoring
├── setup_e2e_test_users.py    # User setup
└── Supporting files           # Database analysis, etc.
```

### **Test Flow:**
```
System Health Check → User Setup → Start Monitoring → 
Execute 9 Phases → Background Job Tracking → 
State Validation → Final Report Generation
```

This comprehensive test suite provides complete validation of the SynapseDTE system's core functionality, ensuring all components work together correctly in real-world scenarios.