# Data Owner Test Case Management Capabilities

## Overview
Yes, Data Owners can now specify and validate queries for each individual test case within their assignment using the data source they've configured.

## Implemented Capabilities

### 1. Individual Test Case Query Management

#### Get All Test Cases for Assignment
```
GET /api/v1/rfi/assignments/{assignment_id}/test-cases
```
- Returns all test cases for the Data Owner's assignment
- Shows sample identifiers, attributes, and current status
- Includes existing queries if any

#### Update Query for Specific Test Case
```
PUT /api/v1/rfi/test-cases/{test_case_id}/query
```
- Update the SQL query for an individual test case
- Each test case can have its own custom query
- Queries can use sample-specific identifiers

#### Validate Query for Test Case
```
POST /api/v1/rfi/test-cases/{test_case_id}/validate-query
```
- Validates the query using the configured data source
- Checks syntax and column availability
- Returns sample data for verification
- Uses the sample identifier for that specific test case

#### Execute Query for Test Case
```
POST /api/v1/rfi/test-cases/{test_case_id}/execute-query
```
- Executes the query and retrieves actual values
- Stores results for the test case
- Updates test case status

### 2. Batch Operations

#### Update Multiple Test Case Queries
```
POST /api/v1/rfi/test-cases/update-queries
```
- Update queries for multiple test cases in one request
- Efficient for handling many test cases
- Returns success/error status for each update

## Example Workflow

### Step 1: Data Owner Gets Their Test Cases
```json
GET /api/v1/rfi/assignments/{assignment_id}/test-cases

Response:
[
  {
    "id": "1",
    "test_case_number": "TC-001",
    "sample_id": "b67361a9-f452-4881-b332-47c6d68bdb56",
    "sample_identifier": "60YGHQ2RZ3FSH6OQMW",
    "attribute_name": "Current Credit limit",
    "status": "Not Started",
    "query_text": null
  },
  {
    "id": "2",
    "test_case_number": "TC-002",
    "sample_id": "c46182f1-7bd7-4ff2-9277-7f579b5d800e",
    "sample_identifier": "E4LZGN2AUHCTISS7O9",
    "attribute_name": "Current Credit limit",
    "status": "Not Started",
    "query_text": null
  }
]
```

### Step 2: Data Owner Writes Query for Test Case
```json
PUT /api/v1/rfi/test-cases/1/query
{
  "query_text": "SELECT customer_id, current_credit_limit FROM public.fry14m_scheduled1_data WHERE customer_id = '60YGHQ2RZ3FSH6OQMW'"
}
```

### Step 3: Data Owner Validates Query
```json
POST /api/v1/rfi/test-cases/1/validate-query

Response:
{
  "is_valid": true,
  "columns": ["customer_id", "current_credit_limit"],
  "sample_data": {
    "customer_id": "60YGHQ2RZ3FSH6OQMW",
    "current_credit_limit": 5000.00
  }
}
```

### Step 4: Data Owner Executes Query
```json
POST /api/v1/rfi/test-cases/1/execute-query

Response:
{
  "success": true,
  "test_case_id": "1",
  "actual_value": 5000.00,
  "data": {
    "customer_id": "60YGHQ2RZ3FSH6OQMW",
    "current_credit_limit": 5000.00
  }
}
```

## Key Features

1. **Individual Query Control**: Each test case can have its own custom query
2. **Data Source Integration**: Queries are validated against the configured data source
3. **Sample-Specific Queries**: Queries can use the specific sample identifier for each test case
4. **Validation Before Execution**: Ensures queries are valid before running them
5. **Result Storage**: Execution results are stored with the test case
6. **Batch Operations**: Update multiple test case queries efficiently

## Benefits

1. **Flexibility**: Data Owners can write custom queries tailored to each test case
2. **Accuracy**: Validation ensures queries will work before execution
3. **Efficiency**: Batch operations allow updating many test cases at once
4. **Traceability**: Each test case maintains its own query and results
5. **Self-Service**: Data Owners can manage their test cases independently

## Technical Implementation

- **Models**: Uses `CycleReportTestCase` for test case storage
- **Authentication**: Requires valid Data Owner authentication
- **Authorization**: Checks assignment ownership
- **Data Source**: Uses the data source configured for the assignment
- **Query Execution**: Validates and executes against configured database

This implementation provides complete control over test case queries, allowing Data Owners to efficiently manage their RFI test cases with custom queries validated against their configured data sources.