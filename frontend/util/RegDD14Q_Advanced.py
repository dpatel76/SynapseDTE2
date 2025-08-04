import pandas as pd
import re
import csv
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, OrderedDict
import pdfplumber
import json

class FRY14QAdvancedExtractor:
    """
    Advanced extractor specifically designed for FR Y-14Q's complex PDF structure
    """
    
    def __init__(self):
        self.schedules = {
            'A': 'Retail',
            'B': 'Securities', 
            'C': 'Regulatory Capital Instruments',
            'D': 'Regulatory Capital',
            'E': 'Operational Risk',
            'F': 'Trading',
            'G': 'PPNR',
            'H': 'Wholesale Risk',
            'J': 'Retail Fair Value Option/Held for Sale (FVO/HFS)',
            'K': 'Supplemental',
            'L': 'Counterparty'
        }
        
        # Track extraction patterns for different schedules
        self.schedule_patterns = {}
        self.all_data_elements = []
        self.schedule_counts = defaultdict(int)
        self.mdrm_data = {}
        
        # Enhanced MDRM patterns for 14Q
        self.mdrm_patterns = [
            r'\b([A-Z]{3,5}\d{3,4})\b',  # Standard MDRM codes
            r'\b(M\d{3})\b',              # M-series codes
            r'\b(BHCK\d{4})\b',           # BHCK codes
            r'\b(CLCO[A-Z0-9]{4})\b',     # CLCO codes
            r'\b(CAC[A-Z]\d{4})\b',       # CAC codes
            r'\b(ASC\d{3})\b',            # ASC codes
        ]
    
    def analyze_pdf_structure(self, pdf_path: str) -> Dict:
        """Deep analysis of PDF structure to understand content organization"""
        print("🔍 Analyzing FR Y-14Q PDF structure...")
        
        structure_info = {
            'page_types': {},
            'schedule_locations': {},
            'table_patterns': {},
            'field_patterns': {},
            'total_pages': 0
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            structure_info['total_pages'] = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                # Analyze page content type
                page_type = self.classify_page_type(text, page_num)
                structure_info['page_types'][page_num] = page_type
                
                # Track schedule locations
                schedule = self.detect_schedule_in_page(text)
                if schedule:
                    if schedule not in structure_info['schedule_locations']:
                        structure_info['schedule_locations'][schedule] = []
                    structure_info['schedule_locations'][schedule].append(page_num)
                
                # Analyze table structures
                tables = page.extract_tables()
                if tables:
                    structure_info['table_patterns'][page_num] = len(tables)
                
                # Look for field definition patterns
                field_patterns = self.identify_field_patterns(text)
                if field_patterns:
                    structure_info['field_patterns'][page_num] = field_patterns
        
        print(f"📊 Found {len(structure_info['schedule_locations'])} schedules across {structure_info['total_pages']} pages")
        return structure_info
    
    def classify_page_type(self, text: str, page_num: int) -> str:
        """Classify what type of content is on each page"""
        if any(keyword in text.lower() for keyword in ['table of contents', 'schedule a –', 'schedule b –']):
            return 'table_of_contents'
        elif any(keyword in text for keyword in ['Field Name', 'MDRM', 'Technical Field']):
            return 'field_definition_table'
        elif re.search(r'\d+\s+[A-Za-z][^.]*[A-Z]{3,5}\d{3,4}', text):
            return 'field_list'
        elif any(keyword in text.lower() for keyword in ['general instructions', 'general guidance']):
            return 'instructions'
        else:
            return 'content'
    
    def detect_schedule_in_page(self, text: str) -> Optional[str]:
        """Detect which schedule this page belongs to"""
        # Look for explicit schedule headers
        schedule_patterns = [
            r'Schedule\s+([A-L])\s*[–-]',
            r'([A-L]\.\d+)\s*[–-]',
            r'Schedule\s+([A-L])—',
            r'^([A-L])\s*[–-]'
        ]
        
        lines = text.split('\n')[:10]  # Check first 10 lines
        
        for line in lines:
            for pattern in schedule_patterns:
                match = re.search(pattern, line.strip())
                if match:
                    schedule_id = match.group(1)[0].upper()  # Get first letter
                    if schedule_id in self.schedules:
                        return schedule_id
        
        return None
    
    def identify_field_patterns(self, text: str) -> List[str]:
        """Identify different field definition patterns in the text"""
        patterns = []
        
        # Pattern 1: Field Number | Field Name | MDRM | Description
        if re.search(r'\d+\s+[A-Za-z][^|]*\|[^|]*\|[A-Z]{3,5}\d{3,4}', text):
            patterns.append('pipe_delimited_table')
        
        # Pattern 2: Field Number Field Name MDRM Description (space separated)
        if re.search(r'^\s*\d+\s+[A-Za-z][^(]*\([^)]*\)\s+[A-Z]{3,5}\d{3,4}', text, re.MULTILINE):
            patterns.append('space_separated_fields')
        
        # Pattern 3: Multi-line field definitions
        if re.search(r'Field\s+Name[;:]\s*Field', text):
            patterns.append('multi_line_definitions')
        
        # Pattern 4: Numbered list format
        if re.search(r'^\s*\d+\.\s+[A-Za-z]', text, re.MULTILINE):
            patterns.append('numbered_list')
        
        return patterns
    
    def extract_schedule_data(self, pdf_path: str, schedule: str, page_numbers: List[int]) -> List[Dict]:
        """Extract data for a specific schedule using targeted parsing"""
        print(f"📋 Extracting Schedule {schedule} from pages {page_numbers[:5]}{'...' if len(page_numbers) > 5 else ''}")
        
        elements = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in page_numbers:
                if page_num >= len(pdf.pages):
                    continue
                
                page = pdf.pages[page_num]
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Try different extraction methods based on page content
                page_elements = []
                
                # Method 1: Table extraction
                tables = page.extract_tables()
                if tables:
                    page_elements.extend(self.extract_from_tables(tables, schedule, page_num))
                
                # Method 2: Structured text parsing
                if not page_elements:
                    page_elements.extend(self.extract_from_structured_text(text, schedule, page_num))
                
                # Method 3: Field definition parsing
                if not page_elements:
                    page_elements.extend(self.extract_field_definitions(text, schedule, page_num))
                
                elements.extend(page_elements)
        
        print(f"✅ Extracted {len(elements)} elements from Schedule {schedule}")
        return elements
    
    def extract_from_tables(self, tables: List, schedule: str, page_num: int) -> List[Dict]:
        """Extract data from PDF tables with enhanced processing"""
        elements = []
        
        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue
            
            # Identify table structure
            headers = self.identify_table_headers(table)
            if not headers:
                continue
            
            # Process each data row
            for row_idx, row in enumerate(table[1:], 1):  # Skip header row
                if not row or all(not cell or str(cell).strip() == '' for cell in row):
                    continue
                
                element = self.parse_table_row_advanced(row, headers, schedule, page_num, table_idx, row_idx)
                if element:
                    elements.append(element)
        
        return elements
    
    def identify_table_headers(self, table: List) -> Optional[Dict[str, int]]:
        """Identify and map table headers to column indices"""
        if not table:
            return None
        
        header_map = {}
        
        # Check first few rows for headers
        for row_idx, row in enumerate(table[:3]):
            if not row:
                continue
            
            for col_idx, cell in enumerate(row):
                if not cell:
                    continue
                
                cell_text = str(cell).strip().lower()
                
                # Map common header patterns
                if any(pattern in cell_text for pattern in ['field name', 'name']):
                    header_map['field_name'] = col_idx
                elif any(pattern in cell_text for pattern in ['field no', 'no.', 'number']):
                    header_map['field_number'] = col_idx
                elif 'mdrm' in cell_text:
                    header_map['mdrm'] = col_idx
                elif any(pattern in cell_text for pattern in ['description', 'desc']):
                    header_map['description'] = col_idx
                elif any(pattern in cell_text for pattern in ['technical', 'tech']):
                    header_map['technical_name'] = col_idx
                elif any(pattern in cell_text for pattern in ['allowable', 'format', 'values']):
                    header_map['format'] = col_idx
                elif any(pattern in cell_text for pattern in ['mandatory', 'optional']):
                    header_map['mandatory'] = col_idx
        
        return header_map if header_map else None
    
    def parse_table_row_advanced(self, row: List, headers: Dict[str, int], schedule: str, 
                                page_num: int, table_idx: int, row_idx: int) -> Optional[Dict]:
        """Advanced parsing of table rows with multiple fallback strategies"""
        if not row:
            return None
        
        # Convert row to clean text
        row_data = [str(cell).strip() if cell else '' for cell in row]
        combined_text = ' '.join(row_data)
        
        # Look for MDRM codes using multiple patterns
        mdrm_code = self.find_mdrm_code(combined_text)
        if not mdrm_code:
            return None
        
        # Extract data using header mapping
        field_data = {}
        
        if headers:
            # Use header positions
            field_data['field_number'] = row_data[headers.get('field_number', 0)] if headers.get('field_number', 0) < len(row_data) else ''
            field_data['field_name'] = row_data[headers.get('field_name', 1)] if headers.get('field_name', 1) < len(row_data) else ''
            field_data['technical_name'] = row_data[headers.get('technical_name', -1)] if headers.get('technical_name', -1) < len(row_data) and headers.get('technical_name', -1) >= 0 else ''
            field_data['description'] = row_data[headers.get('description', -1)] if headers.get('description', -1) < len(row_data) and headers.get('description', -1) >= 0 else ''
            field_data['format_info'] = row_data[headers.get('format', -1)] if headers.get('format', -1) < len(row_data) and headers.get('format', -1) >= 0 else ''
        else:
            # Fallback: parse from combined text
            field_data = self.parse_text_for_field_data(combined_text, mdrm_code)
        
        # Clean and validate data
        field_data = self.clean_field_data(field_data)
        
        # Create data element
        return {
            'Report Name': 'FR Y-14Q',
            'Schedule Name': f"Schedule {schedule}: {self.schedules.get(schedule, schedule)}",
            'Line Item #': field_data.get('field_number', ''),
            'Line Item Name': field_data.get('field_name', ''),
            'Technical Line Item Name': field_data.get('technical_name') or field_data.get('field_name', ''),
            'MDRM': mdrm_code,
            'Description': field_data.get('description', ''),
            'Static or Dynamic': 'Dynamic',
            'Mandatory or Optional': 'Optional' if 'optional' in field_data.get('description', '').lower() else 'Mandatory',
            'Format': field_data.get('format_info', ''),
            '# of reports or schedules used in': 1,
            'Other Schedule Reference': '',
            'Source Page': page_num + 1,
            'Extraction Method': 'table'
        }
    
    def find_mdrm_code(self, text: str) -> Optional[str]:
        """Find MDRM codes using multiple pattern matching"""
        for pattern in self.mdrm_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None
    
    def parse_text_for_field_data(self, text: str, mdrm_code: str) -> Dict:
        """Parse field data from raw text when header mapping fails"""
        data = {}
        
        # Try to extract field number from beginning
        field_num_match = re.match(r'^\s*(\d+)\s+', text)
        if field_num_match:
            data['field_number'] = field_num_match.group(1)
            text = text[field_num_match.end():]
        
        # Split around MDRM code
        mdrm_pos = text.find(mdrm_code)
        if mdrm_pos > 0:
            before_mdrm = text[:mdrm_pos].strip()
            after_mdrm = text[mdrm_pos + len(mdrm_code):].strip()
            
            # Extract field name (before MDRM)
            # Look for technical name in parentheses
            paren_match = re.search(r'\(([^)]+)\)', before_mdrm)
            if paren_match:
                data['technical_name'] = paren_match.group(1)
                data['field_name'] = re.sub(r'\([^)]+\)', '', before_mdrm).strip()
            else:
                data['field_name'] = before_mdrm
            
            # Description is after MDRM
            data['description'] = after_mdrm
        
        return data
    
    def extract_from_structured_text(self, text: str, schedule: str, page_num: int) -> List[Dict]:
        """Extract from structured text layouts (non-table format)"""
        elements = []
        lines = text.split('\n')
        
        current_field = {}
        field_lines = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                # Empty line might signal end of field
                if current_field and self.find_mdrm_code(' '.join(field_lines)):
                    element = self.create_element_from_field_lines(field_lines, schedule, page_num)
                    if element:
                        elements.append(element)
                    current_field = {}
                    field_lines = []
                continue
            
            # Look for field number at start of line
            field_start_match = re.match(r'^(\d+)\s+(.+)', line)
            if field_start_match:
                # Save previous field
                if current_field and self.find_mdrm_code(' '.join(field_lines)):
                    element = self.create_element_from_field_lines(field_lines, schedule, page_num)
                    if element:
                        elements.append(element)
                
                # Start new field
                current_field = {'number': field_start_match.group(1)}
                field_lines = [line]
            else:
                # Continue current field
                if current_field:
                    field_lines.append(line)
        
        # Process final field
        if current_field and self.find_mdrm_code(' '.join(field_lines)):
            element = self.create_element_from_field_lines(field_lines, schedule, page_num)
            if element:
                elements.append(element)
        
        return elements
    
    def create_element_from_field_lines(self, field_lines: List[str], schedule: str, page_num: int) -> Optional[Dict]:
        """Create data element from multi-line field definition"""
        if not field_lines:
            return None
        
        combined_text = ' '.join(field_lines)
        mdrm_code = self.find_mdrm_code(combined_text)
        
        if not mdrm_code:
            return None
        
        field_data = self.parse_text_for_field_data(combined_text, mdrm_code)
        field_data = self.clean_field_data(field_data)
        
        return {
            'Report Name': 'FR Y-14Q',
            'Schedule Name': f"Schedule {schedule}: {self.schedules.get(schedule, schedule)}",
            'Line Item #': field_data.get('field_number', ''),
            'Line Item Name': field_data.get('field_name', ''),
            'Technical Line Item Name': field_data.get('technical_name') or field_data.get('field_name', ''),
            'MDRM': mdrm_code,
            'Description': field_data.get('description', ''),
            'Static or Dynamic': 'Dynamic',
            'Mandatory or Optional': 'Optional' if 'optional' in field_data.get('description', '').lower() else 'Mandatory',
            'Format': self.extract_format_info(field_data.get('description', '')),
            '# of reports or schedules used in': 1,
            'Other Schedule Reference': '',
            'Source Page': page_num + 1,
            'Extraction Method': 'text'
        }
    
    def extract_field_definitions(self, text: str, schedule: str, page_num: int) -> List[Dict]:
        """Extract field definitions from complex layouts"""
        elements = []
        
        # Look for "Field Name; Field" pattern (common in 14Q)
        field_pattern = r'Field\s+Name[;:]\s*Field\s*\(Technical\s+Field\s+MDRM\s+Description\s+Allowable\s+Values\s+(?:Mandatory/)?\s*No\.\s+Name\)\s*(.*?)(?=Field\s+Name[;:]|$)'
        
        matches = re.findall(field_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            # Process each field definition block
            field_element = self.parse_field_definition_block(match, schedule, page_num)
            if field_element:
                elements.append(field_element)
        
        return elements
    
    def parse_field_definition_block(self, text_block: str, schedule: str, page_num: int) -> Optional[Dict]:
        """Parse a field definition block"""
        mdrm_code = self.find_mdrm_code(text_block)
        if not mdrm_code:
            return None
        
        # Try to extract structured information
        lines = text_block.split('\n')
        field_data = {'description': text_block.strip()}
        
        # Look for field number and name patterns
        for line in lines[:3]:  # Check first few lines
            line = line.strip()
            if re.match(r'^\d+', line):
                parts = line.split()
                if parts:
                    field_data['field_number'] = parts[0]
                    field_data['field_name'] = ' '.join(parts[1:]).split(mdrm_code)[0].strip()
                break
        
        field_data = self.clean_field_data(field_data)
        
        return {
            'Report Name': 'FR Y-14Q',
            'Schedule Name': f"Schedule {schedule}: {self.schedules.get(schedule, schedule)}",
            'Line Item #': field_data.get('field_number', ''),
            'Line Item Name': field_data.get('field_name', ''),
            'Technical Line Item Name': field_data.get('field_name', ''),
            'MDRM': mdrm_code,
            'Description': field_data.get('description', ''),
            'Static or Dynamic': 'Dynamic',
            'Mandatory or Optional': 'Mandatory',
            'Format': self.extract_format_info(field_data.get('description', '')),
            '# of reports or schedules used in': 1,
            'Other Schedule Reference': '',
            'Source Page': page_num + 1,
            'Extraction Method': 'definition_block'
        }
    
    def extract_format_info(self, description: str) -> str:
        """Extract format information from description"""
        format_patterns = [
            r'Rounded whole dollar amount[^.]*',
            r'Must be in yyyy-mm-dd format[^.]*',
            r'Free text[^.]*',
            r'Provide as a decimal[^.]*',
            r'Character\s*\(\s*\d+\s*\)[^.]*',
            r'Numeric\s*\(\s*\d+(?:,\d+)?\s*\)[^.]*'
        ]
        
        for pattern in format_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return ''
    
    def clean_field_data(self, field_data: Dict) -> Dict:
        """Clean and normalize field data"""
        cleaned = {}
        
        for key, value in field_data.items():
            if not value:
                cleaned[key] = ''
                continue
            
            # Clean text
            cleaned_value = str(value).strip()
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
            cleaned_value = re.sub(r'^[-–—]\s*', '', cleaned_value)
            cleaned_value = re.sub(r'\s*[-–—]\s*$', '', cleaned_value)
            
            # Truncate if too long
            if key in ['field_name', 'technical_name'] and len(cleaned_value) > 100:
                cleaned_value = cleaned_value[:97] + "..."
            elif key == 'description' and len(cleaned_value) > 500:
                cleaned_value = cleaned_value[:497] + "..."
            
            cleaned[key] = cleaned_value
        
        return cleaned
    
    def create_master_dictionary(self, pdf_path: str, mdrm_csv_path: Optional[str] = None) -> pd.DataFrame:
        """Create comprehensive FR Y-14Q master dictionary"""
        print("🚀 Starting Advanced FR Y-14Q Extraction...")
        
        # Load MDRM data if available
        if mdrm_csv_path:
            self.load_mdrm_csv(mdrm_csv_path)
        
        # Analyze PDF structure
        structure_info = self.analyze_pdf_structure(pdf_path)
        
        # Extract data for each schedule
        for schedule, page_numbers in structure_info['schedule_locations'].items():
            schedule_elements = self.extract_schedule_data(pdf_path, schedule, page_numbers)
            self.all_data_elements.extend(schedule_elements)
            self.schedule_counts[schedule] = len(schedule_elements)
        
        # Post-processing
        self.enhance_with_mdrm_data()
        self.identify_cross_references()
        self.deduplicate_elements()
        
        # Sort results
        self.all_data_elements.sort(key=lambda x: (
            x['Schedule Name'],
            int(x['Line Item #']) if x['Line Item #'].isdigit() else 999,
            x['Line Item Name']
        ))
        
        return pd.DataFrame(self.all_data_elements)
    
    def load_mdrm_csv(self, filepath: str):
        """Load MDRM CSV data"""
        try:
            df = pd.read_csv(filepath, encoding='latin-1')
            for _, row in df.iterrows():
                mdrm_columns = ['MDRM', 'MDRM_CODE', 'Code', 'ITEM_CODE']
                for col in mdrm_columns:
                    if col in df.columns and pd.notna(row[col]):
                        mdrm_value = str(row[col]).strip()
                        self.mdrm_data[mdrm_value] = row.to_dict()
                        break
            print(f"📚 Loaded {len(self.mdrm_data)} MDRM entries")
        except Exception as e:
            print(f"⚠️ Error loading MDRM CSV: {e}")
    
    def enhance_with_mdrm_data(self):
        """Enhance elements with MDRM metadata"""
        enhanced_count = 0
        for element in self.all_data_elements:
            mdrm_code = element['MDRM']
            if mdrm_code in self.mdrm_data:
                mdrm_info = self.mdrm_data[mdrm_code]
                if not element['Description'] and 'Description' in mdrm_info:
                    element['Description'] = str(mdrm_info['Description'])
                    enhanced_count += 1
        print(f"🔗 Enhanced {enhanced_count} elements with MDRM data")
    
    def identify_cross_references(self):
        """Identify cross-references between schedules"""
        mdrm_schedule_map = defaultdict(set)
        
        for element in self.all_data_elements:
            if element['MDRM']:
                mdrm_schedule_map[element['MDRM']].add(element['Schedule Name'])
        
        cross_ref_count = 0
        for element in self.all_data_elements:
            mdrm_code = element['MDRM']
            if mdrm_code in mdrm_schedule_map:
                schedules = list(mdrm_schedule_map[mdrm_code])
                element['# of reports or schedules used in'] = len(schedules)
                
                current_schedule = element['Schedule Name']
                other_schedules = [s for s in schedules if s != current_schedule]
                element['Other Schedule Reference'] = ', '.join(other_schedules)
                
                if len(schedules) > 1:
                    cross_ref_count += 1
        
        print(f"🔗 Identified {cross_ref_count} cross-referenced elements")
    
    def deduplicate_elements(self):
        """Remove duplicate elements based on MDRM code and schedule"""
        seen = set()
        deduplicated = []
        
        for element in self.all_data_elements:
            key = (element['MDRM'], element['Schedule Name'], element['Line Item #'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(element)
        
        removed_count = len(self.all_data_elements) - len(deduplicated)
        self.all_data_elements = deduplicated
        
        if removed_count > 0:
            print(f"🗑️ Removed {removed_count} duplicate elements")
    
    def save_to_pipe_delimited(self, df: pd.DataFrame, filename: str):
        """Save results to pipe-delimited file"""
        df.to_csv(filename, sep='|', index=False, quoting=csv.QUOTE_MINIMAL)
    
    def print_comprehensive_summary(self):
        """Print detailed extraction summary"""
        print("\n" + "="*80)
        print("FR Y-14Q ADVANCED EXTRACTION SUMMARY")
        print("="*80)
        
        print(f"\n📊 TOTAL ELEMENTS EXTRACTED: {len(self.all_data_elements)}")
        
        print(f"\n📋 SCHEDULE BREAKDOWN:")
        print("-" * 50)
        total_by_schedule = 0
        for schedule in sorted(self.schedule_counts.keys()):
            count = self.schedule_counts[schedule]
            schedule_name = self.schedules.get(schedule, schedule)
            print(f"  Schedule {schedule} ({schedule_name}): {count} elements")
            total_by_schedule += count
        
        print(f"\n🔍 QUALITY METRICS:")
        print("-" * 50)
        
        # Quality checks
        missing_mdrm = sum(1 for e in self.all_data_elements if not e['MDRM'])
        missing_names = sum(1 for e in self.all_data_elements if not e['Line Item Name'])
        missing_desc = sum(1 for e in self.all_data_elements if not e['Description'])
        with_format = sum(1 for e in self.all_data_elements if e['Format'])
        cross_ref = sum(1 for e in self.all_data_elements if e['# of reports or schedules used in'] > 1)
        
        print(f"  ✅ Elements with MDRM codes: {len(self.all_data_elements) - missing_mdrm}")
        print(f"  ✅ Elements with field names: {len(self.all_data_elements) - missing_names}")
        print(f"  ✅ Elements with descriptions: {len(self.all_data_elements) - missing_desc}")
        print(f"  ✅ Elements with format info: {with_format}")
        print(f"  🔗 Cross-referenced elements: {cross_ref}")
        
        print(f"\n📈 EXTRACTION METHODS:")
        print("-" * 50)
        method_counts = defaultdict(int)
        for element in self.all_data_elements:
            method = element.get('Extraction Method', 'unknown')
            method_counts[method] += 1
        
        for method, count in sorted(method_counts.items()):
            print(f"  {method}: {count} elements")
        
        print("\n" + "="*80)


def main():
    """Main function for advanced FR Y-14Q extraction"""
    
    # File paths
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    mdrm_csv_path = "_reference/regulations/MDRM_CSV.csv"
    output_dir = "_reference/regulations/output"
    
    print("🚀 FR Y-14Q Advanced Data Dictionary Extractor")
    print("=" * 60)
    
    try:
        import os
        
        # Verify files exist
        if not os.path.exists(pdf_path):
            print(f"❌ Error: PDF file not found at {pdf_path}")
            return pd.DataFrame()
        
        if not os.path.exists(mdrm_csv_path):
            print(f"⚠️ Note: MDRM CSV not found at {mdrm_csv_path}")
            mdrm_csv_path = None
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Initialize advanced extractor
        extractor = FRY14QAdvancedExtractor()
        
        # Create comprehensive dictionary
        df = extractor.create_master_dictionary(pdf_path, mdrm_csv_path)
        
        # Save results
        output_filename = os.path.join(output_dir, "FR_Y14Q_Master_Data_Dictionary_Advanced.txt")
        extractor.save_to_pipe_delimited(df, output_filename)
        
        print(f"\n💾 Advanced 14Q dictionary saved to: {output_filename}")
        
        # Print comprehensive summary
        extractor.print_comprehensive_summary()
        
        # Show sample records
        print(f"\n📋 SAMPLE RECORDS:")
        print("-" * 80)
        if not df.empty:
            for schedule in sorted(extractor.schedule_counts.keys())[:3]:  # First 3 schedules
                schedule_df = df[df['Schedule Name'].str.contains(f'Schedule {schedule}')]
                if not schedule_df.empty:
                    print(f"\n🔸 Schedule {schedule} samples:")
                    for _, row in schedule_df.head(2).iterrows():
                        print(f"   Field {row['Line Item #']}: {row['Line Item Name']}")
                        print(f"   MDRM: {row['MDRM']}")
                        print(f"   Description: {row['Description'][:80]}...")
                        print()
        
        return df
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


if __name__ == "__main__":
    df = main() 