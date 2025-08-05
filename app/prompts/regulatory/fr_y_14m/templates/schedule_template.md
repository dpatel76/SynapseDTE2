# FR Y-14M Schedule Template Structure

This template provides the foundation for creating schedule-specific prompts. Each schedule should customize these templates based on their unique regulatory requirements.

## Core Components for Each Schedule

### 1. attribute_discovery.txt
- **Purpose**: Generate complete list of attributes for the schedule
- **Key Elements**:
  - Exact Federal Reserve field names
  - All mandatory and conditional fields
  - Schedule-specific field count (varies by schedule)
  - Systematic categorization approach

### 2. attribute_details.txt
- **Purpose**: Provide detailed specifications for each attribute
- **Key Elements**:
  - Federal Reserve data dictionary definitions
  - Schedule-specific validation rules
  - Source system mapping
  - Testing methodology

### 3. scoping_recommendations.txt
- **Purpose**: Risk-based testing scope determination
- **Key Elements**:
  - Schedule-specific risk factors
  - Regulatory focus areas
  - Sampling methodology
  - Stratification approach

### 4. testing_approach.txt
- **Purpose**: Detailed testing procedures
- **Key Elements**:
  - Validation steps by data type
  - Cross-field validations
  - Regulatory compliance checks
  - Common error patterns

## Schedule-Specific Customization Guide

### Data Elements to Customize:
1. **Field Count**: Each schedule has different number of attributes
   - Schedule A: ~165 attributes
   - Schedule C: ~140 attributes
   - Schedule G: ~185 attributes

2. **Risk Factors**: Unique to each product type
   - Mortgage schedules: LTV, DTI, delinquency
   - Card schedules: Utilization, payment patterns
   - Commercial schedules: DSCR, occupancy rates

3. **Validation Rules**: Product-specific requirements
   - Interest rate validations vary by product
   - Date field requirements differ
   - Amount field precision varies

4. **Source Systems**: Different for each product
   - Mortgage: LOS, servicing platforms
   - Cards: Card management systems
   - Commercial: Commercial loan systems

## Template Variables

All templates should support these variables:
- `${report_name}` - Institution/report identifier
- `${regulatory_context}` - Additional context provided
- `${attribute_name}` - Specific attribute being analyzed
- `${data_type}` - Attribute data type
- `${historical_issues}` - Past problems identified
- `${portfolio_size}` - Size of portfolio being tested

## Quality Standards

1. **Precision**: Use exact Federal Reserve terminology
2. **Completeness**: Include all required elements
3. **Clarity**: Clear, actionable instructions
4. **Compliance**: Align with current Y-14M instructions
5. **Maintainability**: Easy to update for regulatory changes