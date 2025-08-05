# Regulatory Report-Specific Prompts Guide

## Overview

The SynapseDT platform now supports regulatory report-specific prompts for maximum precision and compliance accuracy. This system automatically detects regulatory reports from context and loads optimized prompts for each specific report and schedule.

## Supported Regulatory Reports

### FR Y-14M (Monthly)
- **Schedule A**: First Lien Closed-end 1-4 Family Residential Loan
- **Schedule B**: Home Equity
- **Schedule C**: Credit Card
- **Schedule D**: Other Consumer
- **Schedule E**: Small Business
- **Schedule F**: Corporate
- **Schedule G**: Commercial Real Estate
- **Schedule H**: International
- **Schedule I**: Advanced
- **Schedule J**: Retail Fair Lending
- **Schedule K**: Supplemental
- **Schedule L**: Counterparty

### FR Y-14Q (Quarterly) - Coming Soon
### FR Y-9C (Bank Holding Company) - Coming Soon
### Call Report - Coming Soon

## How It Works

### 1. Automatic Detection
The system automatically detects regulatory reports from:
- Regulatory context entered by users
- Report names and types
- Keywords like "Schedule A", "Credit Card", "First Lien"

### 2. Prompt Selection Hierarchy
```
1. Schedule-specific prompt (e.g., fr_y_14m/schedule_a/attribute_discovery.txt)
2. Report-level common prompt (e.g., fr_y_14m/common/attribute_discovery.txt)
3. Generic prompt (e.g., prompts/attribute_discovery.txt)
```

### 3. Precision Enhancements

Each regulatory prompt includes:
- **Exact Federal Reserve field names**
- **Schedule-specific validation rules**
- **Accurate field counts** (e.g., Schedule A: ~165 fields)
- **Regulatory-specific testing approaches**
- **Cross-reference requirements**

## Usage Examples

### Example 1: FR Y-14M Schedule A
```
User Input:
- Regulatory Context: "FR Y-14M Schedule A - First Lien Mortgage Portfolio Q4 2024"
- Report Type: "Residential Mortgage"

System Response:
- Detects: FR Y-14M, Schedule A
- Loads: fr_y_14m/schedule_a/attribute_discovery.txt
- Generates: 165 precise mortgage-specific attributes
```

### Example 2: FR Y-14M Schedule C
```
User Input:
- Regulatory Context: "Credit Card portfolio for FR Y-14M reporting"
- Report Type: "Credit Card Master Trust"

System Response:
- Detects: FR Y-14M, Schedule C
- Loads: fr_y_14m/schedule_c/attribute_discovery.txt
- Generates: 140 credit card-specific attributes
```

## Benefits of Regulatory-Specific Prompts

### 1. **Accuracy**
- Exact field names matching Federal Reserve specifications
- Correct data types and formats
- Proper validation rules

### 2. **Completeness**
- All mandatory fields included
- Conditional fields properly identified
- No missing critical attributes

### 3. **Efficiency**
- Reduced manual review time
- Fewer iterations needed
- Higher first-pass accuracy

### 4. **Compliance**
- Aligned with current regulatory instructions
- Includes all technical specification requirements
- Proper cross-schedule references

## Creating New Regulatory Prompts

### Directory Structure
```
prompts/regulatory/
├── [report_name]/
│   ├── common/
│   │   ├── attribute_discovery.txt
│   │   ├── attribute_batch_details.txt
│   │   ├── scoping_recommendations.txt
│   │   └── testing_approach.txt
│   └── [schedule_name]/
│       ├── attribute_discovery.txt
│       ├── attribute_details.txt
│       ├── scoping_recommendations.txt
│       └── testing_approach.txt
```

### Naming Conventions
- Report names: Lowercase, underscores (e.g., `fr_y_14m`)
- Schedule names: Lowercase, underscores (e.g., `schedule_a`)
- Prompt files: Same names as generic prompts

### Required Elements

1. **attribute_discovery.txt**
   - Complete field list
   - Exact Federal Reserve names
   - Systematic categorization
   - Target field count

2. **attribute_details.txt**
   - 8 mandatory fields per attribute
   - Schedule-specific validation rules
   - Regulatory references
   - Testing methodologies

3. **scoping_recommendations.txt**
   - Risk-based sampling
   - Regulatory focus areas
   - Schedule-specific risks
   - Stratification approach

4. **testing_approach.txt**
   - Data type-specific validations
   - Cross-field dependencies
   - Regulatory calculations
   - Common error patterns

## Best Practices

### 1. **Keep Prompts Current**
- Review against latest regulatory instructions
- Update for regulatory changes
- Version control changes

### 2. **Test Thoroughly**
- Validate against actual Y-14M submissions
- Check field completeness
- Verify calculation accuracy

### 3. **Document Changes**
- Note regulatory instruction versions
- Track field additions/removals
- Document validation rule changes

### 4. **Maintain Consistency**
- Use standard terminology
- Follow Federal Reserve naming
- Align with technical specifications

## Troubleshooting

### Issue: Generic prompt loaded instead of specific
**Solution**: Check regulatory context contains clear report/schedule identifiers

### Issue: Missing attributes in generation
**Solution**: Review prompt field count and categories for completeness

### Issue: Incorrect validation rules
**Solution**: Verify against latest Federal Reserve instructions

## Future Enhancements

1. **Additional Reports**
   - FR Y-14Q quarterly schedules
   - FR Y-9C schedules
   - Call Report schedules
   - FFIEC reports

2. **Advanced Features**
   - Cross-schedule validation prompts
   - Regulatory change detection
   - Version-specific prompts
   - Multi-language support

3. **Integration Improvements**
   - Direct Federal Reserve specification parsing
   - Automated prompt updates
   - Validation rule libraries
   - Testing script generation