# Planning Phase to Sample Generation Connection

## Overview
The connection between the Planning phase and Sample Generation is currently **partially implemented**. The system has the infrastructure for data sources and table configurations in the planning phase, but these are not being passed through to the sample generation process.

## Current State

### Planning Phase Components

1. **Data Sources Model** (`app/models/cycle_report_data_source.py`)
   - Stores data source configurations (PostgreSQL, MySQL, Oracle, etc.)
   - Contains connection details, authentication, and schema information
   - Linked to workflow phases via `phase_id`

2. **PDE Mappings** (`app/models/planning.py`)
   - Maps attributes to data sources and specific table/column combinations
   - Stores source field information in format: `schema.table.column`
   - Includes data_source_id reference

3. **Report Attributes** (`app/models/report_attribute.py`)
   - Defines the attributes that need to be sampled
   - Contains data types, validation rules, and scoping information

### Sample Generation Components

1. **Sample Selection Endpoint** (`app/api/v1/endpoints/sample_selection.py`)
   - `/cycles/{cycle_id}/reports/{report_id}/samples/generate` endpoint
   - Currently only receives:
     - `sample_size`
     - `sample_type`
     - `regulatory_context`
     - `scoped_attributes` (basic attribute info)

2. **Sample Generation Prompt** (`prompts/regulatory/fr_y_14m/schedule_d_1/sample_generation.txt`)
   - Expects scoped attributes but no data source information
   - Uses generic placeholders for data values

## Missing Connections

### 1. Data Source Information Not Passed
The sample generation endpoint does not:
- Query for data sources from the planning phase
- Include table/column mappings in the generation context
- Pass schema information to the LLM

### 2. Upload Functionality Missing Data Context
The upload endpoint (`/samples/upload`) doesn't:
- Validate against data source schemas
- Reference PDE mappings for field validation
- Use table configurations from planning

### 3. No Schema Validation
Sample generation doesn't:
- Validate generated data against actual database schemas
- Use data type information from source tables
- Apply constraints from the data sources

## Implementation Requirements

### 1. Enhance Sample Generation Request

```python
class SampleGenerationRequest(BaseModel):
    sample_size: int
    sample_type: str = "Population"
    regulatory_context: Optional[str] = None
    scoped_attributes: Optional[List[Dict[str, Any]]] = None
    # Add these fields:
    include_data_sources: bool = True
    use_pde_mappings: bool = True
```

### 2. Query Data Sources in Generate Endpoint

```python
# In generate_samples function, after getting scoped attributes:

# Get PDE mappings for the attributes
pde_mappings_query = select(PlanningPDEMapping).where(
    PlanningPDEMapping.phase_id == phase.phase_id
)
pde_mappings = await db.execute(pde_mappings_query)

# Get data sources
data_sources_query = select(CycleReportDataSource).where(
    CycleReportDataSource.phase_id == phase.phase_id
)
data_sources = await db.execute(data_sources_query)

# Build enhanced context for LLM
enhanced_attributes = []
for attr in scoped_attributes:
    # Find PDE mapping for this attribute
    mapping = next((m for m in pde_mappings if m.attribute_id == attr['id']), None)
    if mapping:
        attr['source_table'] = mapping.source_table
        attr['source_column'] = mapping.source_column
        attr['data_source_name'] = mapping.data_source_name
    enhanced_attributes.append(attr)
```

### 3. Update Sample Generation Prompt

Add a new section to the prompt template:

```
## Data Source Context
{if data_sources}
Available Data Sources:
{data_sources_list}

Attribute Mappings:
{attribute_mappings}
{/if}
```

### 4. Enhance Upload Validation

```python
# In upload_samples function:

# Get PDE mappings for validation
pde_mappings = await get_pde_mappings_for_phase(phase_id)

# Validate each uploaded sample
for sample_data in request.samples:
    for attr_name, value in sample_data.items():
        mapping = find_mapping_for_attribute(attr_name, pde_mappings)
        if mapping:
            # Validate against source data type
            validate_value_against_source(value, mapping.column_data_type)
```

## Benefits of Implementation

1. **More Realistic Sample Data**: LLM can generate data that matches actual database schemas
2. **Better Validation**: Uploaded samples can be validated against source schemas
3. **Traceability**: Clear connection between planning decisions and generated samples
4. **Compliance**: Ensures samples align with documented data sources
5. **Testing Accuracy**: Samples reflect real data structures for more accurate testing

## Next Steps

1. Update the `SampleGenerationRequest` model to include data source flags
2. Modify the generate_samples endpoint to query planning phase data
3. Create helper functions to fetch and format data source information
4. Update the sample generation prompts to include data source context
5. Enhance upload validation to use PDE mappings
6. Add frontend support to display data source information during sample selection