# FR Y-14M Report-Specific Prompts

This directory contains precision-focused prompt templates for each FR Y-14M schedule, designed to ensure maximum accuracy and regulatory compliance.

## FR Y-14M Schedule Structure

### Schedule A - First Lien Closed-end 1-4 Family Residential Loan
- Focus: First lien residential mortgages
- Key Attributes: Loan characteristics, borrower information, collateral details
- Special Requirements: LTV ratios, FICO scores, property values

### Schedule B - Home Equity
- Focus: Home equity lines of credit (HELOC) and closed-end home equity loans
- Key Attributes: Draw period details, credit limits, utilization rates
- Special Requirements: Combined LTV calculations, payment structures

### Schedule C - Credit Card
- Focus: Credit card accounts and portfolios
- Key Attributes: Account details, transaction volumes, payment patterns
- Special Requirements: Utilization rates, fee structures, rewards programs

### Schedule D - Other Consumer
- Focus: Auto loans, student loans, other consumer credit
- Key Attributes: Loan purpose, terms, collateral (if applicable)
- Special Requirements: Product-specific fields vary by loan type

### Schedule E - Small Business
- Focus: Small business loans and lines of credit
- Key Attributes: Business characteristics, revenue, industry codes
- Special Requirements: NAICS codes, business structure, guarantees

### Schedule F - Corporate
- Focus: Corporate loans and credit facilities
- Key Attributes: Facility types, commitment amounts, utilization
- Special Requirements: Syndication details, covenant information

### Schedule G - Commercial Real Estate
- Focus: Commercial real estate loans
- Key Attributes: Property types, occupancy rates, debt service coverage
- Special Requirements: Property valuations, tenant information

### Schedule H - International
- Focus: International exposures and cross-border lending
- Key Attributes: Country exposure, currency, sovereign ratings
- Special Requirements: Country risk classifications, FX considerations

### Schedule I - Advanced
- Focus: Advanced modeling and projections
- Key Attributes: Model parameters, assumptions, projections
- Special Requirements: Statistical validations, scenario analysis

### Schedule J - Retail Fair Lending
- Focus: Fair lending data for retail products
- Key Attributes: Demographic data, pricing, underwriting decisions
- Special Requirements: HMDA alignment, fair lending indicators

### Schedule K - Supplemental
- Focus: Additional data supporting other schedules
- Key Attributes: Varies based on supplemental requirements
- Special Requirements: Cross-reference integrity

### Schedule L - Counterparty
- Focus: Counterparty credit risk
- Key Attributes: Counterparty details, exposure types, netting
- Special Requirements: Master agreement details, collateral

## Directory Structure

```
fr_y_14m/
├── common/                   # Shared templates across schedules
│   ├── attribute_discovery.txt
│   ├── attribute_batch_details.txt
│   ├── scoping_recommendations.txt
│   └── testing_approach.txt
├── templates/               # Base templates for customization
├── schedule_a/             # First Lien Residential
├── schedule_b/             # Home Equity
├── schedule_c/             # Credit Card
├── schedule_d/             # Other Consumer
├── schedule_e/             # Small Business
├── schedule_f/             # Corporate
├── schedule_g/             # Commercial Real Estate
├── schedule_h/             # International
├── schedule_i/             # Advanced
├── schedule_j/             # Retail Fair Lending
├── schedule_k/             # Supplemental
└── schedule_l/             # Counterparty
```

## Prompt Design Principles

1. **Precision First**: Every prompt must be specific to the schedule's regulatory requirements
2. **Attribute Completeness**: Include ALL required and conditional fields per Federal Reserve instructions
3. **Validation Rules**: Incorporate specific validation requirements from technical specifications
4. **Cross-Reference Accuracy**: Ensure consistency across related schedules
5. **Testing Specificity**: Testing approaches must align with data types and regulatory expectations

## Usage

Each schedule directory contains phase-specific prompts:
- `attribute_discovery.txt` - Complete attribute list generation
- `attribute_details.txt` - Detailed attribute specifications
- `scoping_recommendations.txt` - Risk-based scoping guidance
- `testing_approach.txt` - Schedule-specific testing methodologies
- `validation_rules.txt` - Comprehensive validation requirements