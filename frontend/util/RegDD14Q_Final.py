import pandas as pd
import re
import csv
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import pdfplumber

class FRY14QFinalExtractor:
    """
    Final targeted extractor based on actual FR Y-14Q PDF structure analysis
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
        
        self.all_data_elements = []
        self.schedule_counts = defaultdict(int)
        self.mdrm_data = {}
        
        # Pages that actually contain field definition tables (from debugging)
        self.field_definition_pages = {
            'H': list(range(170, 270)),  # Schedule H spans many pages
            'L': list(range(270, 310)),  # Schedule L counterparty  
            'C': list(range(60, 75)),    # Schedule C regulatory capital
            'B': list(range(52, 65)),    # Schedule B securities
            'F': list(range(85, 125)),   # Schedule F trading
            'G': list(range(125, 160)),  # Schedule G PPNR
        }
        
    def find_data_definition_pages(self, pdf_path: str) -> Dict[str, List[int]]:
        """Find pages that actually contain field definition tables"""
        field_pages = defaultdict(list)
        
        with pdfplumber.open(pdf_path) as pdf:
            current_schedule = None
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                # Detect schedule changes
                new_schedule = self.detect_schedule(text)
                if new_schedule:
                    current_schedule = new_schedule
                
                # Check if this page has field definitions
                if self.has_field_definitions(text, page):
                    if current_schedule:
                        field_pages[current_schedule].append(page_num)
                        print(f"📋 Found field definitions for Schedule {current_schedule} on page {page_num + 1}")
        
        return dict(field_pages)
    
    def detect_schedule(self, text: str) -> Optional[str]:
        """Detect which schedule this page belongs to"""
        lines = text.split('\n')[:10]  # Check first 10 lines
        
        for line in lines:
            # Look for explicit schedule headers
            if re.search(r'Schedule\s+([A-L])\s*[–—-]', line):
                match = re.search(r'Schedule\s+([A-L])\s*[–—-]', line)
                return match.group(1).upper()
            
            if re.search(r'([A-L])\.\d+\s*[–—-]', line):
                match = re.search(r'([A-L])\.\d+\s*[–—-]', line)
                return match.group(1).upper()
        
        return None
    
    def has_field_definitions(self, text: str, page) -> bool:
        """Check if page contains actual field definition tables"""
        # Must have both field structure indicators AND MDRM codes
        has_field_structure = (
            'Field Name' in text and 
            ('MDRM' in text or 'Technical Field' in text)
        )
        
        # Check for MDRM code patterns
        mdrm_patterns = [
            r'\b[A-Z]{3,5}\d{3,4}\b',
            r'\bCLC[A-Z]\d{4}\b',
            r'\bBHCK\d{4}\b',
            r'\bCAC[A-Z]\d{4}\b',
        ]
        
        has_mdrm_codes = any(re.search(pattern, text) for pattern in mdrm_patterns)
        
        # Check for tables
        tables = page.extract_tables()
        has_structured_table = len(tables) > 0
        
        return has_field_structure and (has_mdrm_codes or has_structured_table)
    
    def extract_from_field_definition_page(self, page, page_num: int, schedule: str) -> List[Dict]:
        """Extract field definitions from a confirmed field definition page"""
        elements = []
        text = page.extract_text()
        
        if not text:
            return elements
        
        # Try table extraction first
        tables = page.extract_tables()
        if tables:
            for table in tables:
                table_elements = self.extract_from_table_structure(table, page_num, schedule)
                elements.extend(table_elements)
        
        # If no table results, try text extraction
        if not elements:
            text_elements = self.extract_from_text_structure(text, page_num, schedule)
            elements.extend(text_elements)
        
        return elements
    
    def extract_from_table_structure(self, table: List[List], page_num: int, schedule: str) -> List[Dict]:
        """Extract from actual table structure"""
        elements = []
        
        if not table or len(table) < 2:
            return elements
        
        # Identify columns
        header_row = table[0] if table else []
        column_map = {}
        
        for col_idx, header in enumerate(header_row):
            if not header:
                continue
            
            header_text = str(header).lower().strip()
            
            if 'field no' in header_text or 'no.' in header_text:
                column_map['field_number'] = col_idx
            elif 'field name' in header_text or 'technical' in header_text:
                column_map['field_name'] = col_idx
            elif 'mdrm' in header_text:
                column_map['mdrm'] = col_idx
            elif 'description' in header_text:
                column_map['description'] = col_idx
            elif 'allowable' in header_text or 'values' in header_text:
                column_map['format'] = col_idx
            elif 'mandatory' in header_text or 'optional' in header_text:
                column_map['mandatory'] = col_idx
        
        print(f"   📊 Table columns identified: {list(column_map.keys())}")
        
        # Process data rows
        for row_idx, row in enumerate(table[1:], 1):
            if not row or all(not cell or str(cell).strip() == '' for cell in row):
                continue
            
            element = self.extract_element_from_row(row, column_map, page_num, schedule, row_idx)
            if element:
                elements.append(element)
        
        return elements
    
    def extract_element_from_row(self, row: List, column_map: Dict, page_num: int, 
                                schedule: str, row_idx: int) -> Optional[Dict]:
        """Extract a data element from a table row"""
        if not row:
            return None
        
        # Convert row to strings
        row_data = [str(cell).strip() if cell else '' for cell in row]
        
        # Extract data using column mapping
        field_number = ''
        field_name = ''
        mdrm_code = ''
        description = ''
        format_info = ''
        mandatory = 'Mandatory'
        
        # Get data from mapped columns
        if 'field_number' in column_map and column_map['field_number'] < len(row_data):
            field_number = row_data[column_map['field_number']]
        
        if 'field_name' in column_map and column_map['field_name'] < len(row_data):
            field_name = row_data[column_map['field_name']]
        
        if 'mdrm' in column_map and column_map['mdrm'] < len(row_data):
            mdrm_code = row_data[column_map['mdrm']]
        
        if 'description' in column_map and column_map['description'] < len(row_data):
            description = row_data[column_map['description']]
        
        if 'format' in column_map and column_map['format'] < len(row_data):
            format_info = row_data[column_map['format']]
        
        if 'mandatory' in column_map and column_map['mandatory'] < len(row_data):
            mandatory_text = row_data[column_map['mandatory']].lower()
            mandatory = 'Optional' if 'optional' in mandatory_text else 'Mandatory'
        
        # If no MDRM from column, try to find it in any cell
        if not mdrm_code:
            combined_text = ' '.join(row_data)
            mdrm_patterns = [
                r'\b([A-Z]{3,5}\d{3,4})\b',
                r'\b(CLC[A-Z]\d{4})\b',
                r'\b(BHCK\d{4})\b',
                r'\b(CAC[A-Z]\d{4})\b',
            ]
            
            for pattern in mdrm_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    mdrm_code = match.group(1)
                    break
        
        # Skip if no MDRM code found
        if not mdrm_code or mdrm_code.lower() in ['mdrm', 'cred']:
            return None
        
        # Clean and format data
        field_name = self.clean_text(field_name)
        description = self.clean_text(description)
        format_info = self.clean_text(format_info)
        
        # Extract technical name from field name if it has parentheses
        technical_name = field_name
        if '(' in field_name and ')' in field_name:
            paren_match = re.search(r'\(([^)]+)\)', field_name)
            if paren_match:
                technical_name = paren_match.group(1)
                field_name = re.sub(r'\([^)]+\)', '', field_name).strip()
        
        return {
            'Report Name': 'FR Y-14Q',
            'Schedule Name': f"Schedule {schedule}: {self.schedules.get(schedule, schedule)}",
            'Line Item #': field_number,
            'Line Item Name': field_name,
            'Technical Line Item Name': technical_name,
            'MDRM': mdrm_code,
            'Description': description,
            'Static or Dynamic': 'Dynamic',
            'Mandatory or Optional': mandatory,
            'Format': format_info,
            '# of reports or schedules used in': 1,
            'Other Schedule Reference': '',
            'Source Page': page_num + 1,
            'Table Row': row_idx
        }
    
    def extract_from_text_structure(self, text: str, page_num: int, schedule: str) -> List[Dict]:
        """Extract from text when table extraction fails"""
        elements = []
        lines = text.split('\n')
        
        current_field = {}
        field_buffer = []
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Look for field number at start of line
            field_match = re.match(r'^(\d+)\s+(.+)', line)
            if field_match:
                # Process previous field
                if current_field and field_buffer:
                    element = self.create_element_from_text_field(current_field, field_buffer, page_num, schedule)
                    if element:
                        elements.append(element)
                
                # Start new field
                current_field = {
                    'number': field_match.group(1),
                    'start_line': line_num
                }
                field_buffer = [line]
            elif current_field:
                # Continue current field
                field_buffer.append(line)
                
                # Check if we've gone too far (empty lines or new section)
                if not line and len(field_buffer) > 10:
                    element = self.create_element_from_text_field(current_field, field_buffer, page_num, schedule)
                    if element:
                        elements.append(element)
                    current_field = {}
                    field_buffer = []
        
        # Process final field
        if current_field and field_buffer:
            element = self.create_element_from_text_field(current_field, field_buffer, page_num, schedule)
            if element:
                elements.append(element)
        
        return elements
    
    def create_element_from_text_field(self, field_info: Dict, field_lines: List[str], 
                                     page_num: int, schedule: str) -> Optional[Dict]:
        """Create element from text field definition"""
        combined_text = ' '.join(field_lines)
        
        # Find MDRM code
        mdrm_patterns = [
            r'\b([A-Z]{3,5}\d{3,4})\b',
            r'\b(CLC[A-Z]\d{4})\b',
            r'\b(BHCK\d{4})\b',
            r'\b(CAC[A-Z]\d{4})\b',
        ]
        
        mdrm_code = ''
        for pattern in mdrm_patterns:
            match = re.search(pattern, combined_text)
            if match:
                mdrm_code = match.group(1)
                break
        
        if not mdrm_code:
            return None
        
        # Extract field name (usually right after field number)
        first_line = field_lines[0] if field_lines else ''
        field_name_match = re.match(r'^\d+\s+([^A-Z]{2,50})', first_line)
        field_name = field_name_match.group(1).strip() if field_name_match else ''
        
        # Description is everything after MDRM
        mdrm_pos = combined_text.find(mdrm_code)
        description = ''
        if mdrm_pos > 0:
            description = combined_text[mdrm_pos + len(mdrm_code):].strip()
        
        # Clean data
        field_name = self.clean_text(field_name)
        description = self.clean_text(description)
        
        return {
            'Report Name': 'FR Y-14Q',
            'Schedule Name': f"Schedule {schedule}: {self.schedules.get(schedule, schedule)}",
            'Line Item #': field_info.get('number', ''),
            'Line Item Name': field_name,
            'Technical Line Item Name': field_name,
            'MDRM': mdrm_code,
            'Description': description,
            'Static or Dynamic': 'Dynamic',
            'Mandatory or Optional': 'Optional' if 'optional' in description.lower() else 'Mandatory',
            'Format': self.extract_format_from_description(description),
            '# of reports or schedules used in': 1,
            'Other Schedule Reference': '',
            'Source Page': page_num + 1,
            'Extraction Method': 'text'
        }
    
    def extract_format_from_description(self, description: str) -> str:
        """Extract format information from description"""
        format_patterns = [
            r'Rounded whole dollar amount[^.]*',
            r'Must be in yyyy-mm-dd format[^.]*',
            r'Free text[^.]*',
            r'Provide as a decimal[^.]*',
            r'Express as a decimal[^.]*',
        ]
        
        for pattern in format_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return ''
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove line break artifacts
        text = re.sub(r'\n+', ' ', text)
        
        # Truncate if too long
        if len(text) > 300:
            text = text[:297] + "..."
        
        return text
    
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
    
    def create_master_dictionary(self, pdf_path: str, mdrm_csv_path: Optional[str] = None) -> pd.DataFrame:
        """Create the final FR Y-14Q master dictionary"""
        print("🎯 Starting Final FR Y-14Q Extraction (Targeted Approach)")
        print("=" * 60)
        
        # Load MDRM data
        if mdrm_csv_path:
            self.load_mdrm_csv(mdrm_csv_path)
        
        # Find actual field definition pages
        field_pages = self.find_data_definition_pages(pdf_path)
        
        # Extract from each schedule's field definition pages
        with pdfplumber.open(pdf_path) as pdf:
            for schedule, page_numbers in field_pages.items():
                print(f"\n📋 Processing Schedule {schedule} ({len(page_numbers)} pages)")
                
                for page_num in page_numbers:
                    if page_num >= len(pdf.pages):
                        continue
                    
                    page = pdf.pages[page_num]
                    elements = self.extract_from_field_definition_page(page, page_num, schedule)
                    
                    if elements:
                        print(f"   ✅ Page {page_num + 1}: {len(elements)} elements")
                        self.all_data_elements.extend(elements)
                        self.schedule_counts[schedule] += len(elements)
                    else:
                        print(f"   ⚠️ Page {page_num + 1}: No elements extracted")
        
        # Post-processing
        self.identify_cross_references()
        self.deduplicate_elements()
        
        # Sort by schedule and field number
        self.all_data_elements.sort(key=lambda x: (
            x['Schedule Name'],
            int(x['Line Item #']) if x['Line Item #'].isdigit() else 999
        ))
        
        return pd.DataFrame(self.all_data_elements)
    
    def identify_cross_references(self):
        """Identify MDRM codes used across schedules"""
        mdrm_schedule_map = defaultdict(set)
        
        for element in self.all_data_elements:
            if element['MDRM']:
                mdrm_schedule_map[element['MDRM']].add(element['Schedule Name'])
        
        for element in self.all_data_elements:
            mdrm_code = element['MDRM']
            if mdrm_code in mdrm_schedule_map:
                schedules = list(mdrm_schedule_map[mdrm_code])
                element['# of reports or schedules used in'] = len(schedules)
                
                current_schedule = element['Schedule Name']
                other_schedules = [s for s in schedules if s != current_schedule]
                element['Other Schedule Reference'] = ', '.join(other_schedules)
    
    def deduplicate_elements(self):
        """Remove duplicate elements"""
        seen = set()
        deduplicated = []
        
        for element in self.all_data_elements:
            # Create key for deduplication
            key = (element['MDRM'], element['Schedule Name'], element['Line Item #'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(element)
        
        removed = len(self.all_data_elements) - len(deduplicated)
        if removed > 0:
            print(f"🗑️ Removed {removed} duplicate elements")
        
        self.all_data_elements = deduplicated
    
    def save_to_pipe_delimited(self, df: pd.DataFrame, filename: str):
        """Save to pipe-delimited file"""
        df.to_csv(filename, sep='|', index=False, quoting=csv.QUOTE_MINIMAL)
    
    def print_final_summary(self):
        """Print comprehensive final summary"""
        print("\n" + "="*70)
        print("FR Y-14Q FINAL EXTRACTION SUMMARY")
        print("="*70)
        
        print(f"\n🎯 TOTAL ELEMENTS EXTRACTED: {len(self.all_data_elements)}")
        
        print(f"\n📊 SCHEDULE BREAKDOWN:")
        print("-" * 40)
        for schedule in sorted(self.schedule_counts.keys()):
            count = self.schedule_counts[schedule]
            schedule_name = self.schedules.get(schedule, schedule)
            print(f"  Schedule {schedule} ({schedule_name}): {count} elements")
        
        print(f"\n✅ QUALITY METRICS:")
        print("-" * 40)
        missing_mdrm = sum(1 for e in self.all_data_elements if not e['MDRM'])
        missing_names = sum(1 for e in self.all_data_elements if not e['Line Item Name'])
        with_format = sum(1 for e in self.all_data_elements if e['Format'])
        cross_ref = sum(1 for e in self.all_data_elements if e['# of reports or schedules used in'] > 1)
        
        print(f"  Elements with MDRM codes: {len(self.all_data_elements) - missing_mdrm}")
        print(f"  Elements with field names: {len(self.all_data_elements) - missing_names}")
        print(f"  Elements with format info: {with_format}")
        print(f"  Cross-referenced elements: {cross_ref}")
        
        print("\n" + "="*70)


def main():
    """Main function for final FR Y-14Q extraction"""
    
    # File paths
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    mdrm_csv_path = "_reference/regulations/MDRM_CSV.csv"
    output_dir = "_reference/regulations/output"
    
    try:
        import os
        
        # Verify files
        if not os.path.exists(pdf_path):
            print(f"❌ Error: PDF file not found at {pdf_path}")
            return pd.DataFrame()
        
        if not os.path.exists(mdrm_csv_path):
            print(f"⚠️ Note: MDRM CSV not found at {mdrm_csv_path}")
            mdrm_csv_path = None
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Initialize final extractor
        extractor = FRY14QFinalExtractor()
        
        # Create master dictionary
        df = extractor.create_master_dictionary(pdf_path, mdrm_csv_path)
        
        # Save results
        output_filename = os.path.join(output_dir, "FR_Y14Q_Master_Data_Dictionary_Final.txt")
        extractor.save_to_pipe_delimited(df, output_filename)
        
        print(f"\n💾 Final 14Q dictionary saved to: {output_filename}")
        
        # Print summary
        extractor.print_final_summary()
        
        # Show sample records
        if not df.empty:
            print(f"\n📋 SAMPLE RECORDS:")
            print("-" * 70)
            for _, row in df.head(5).iterrows():
                print(f"\nField {row['Line Item #']}: {row['Line Item Name']}")
                print(f"Schedule: {row['Schedule Name']}")
                print(f"MDRM: {row['MDRM']}")
                print(f"Description: {row['Description'][:80]}...")
                print(f"Format: {row['Format']}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


if __name__ == "__main__":
    df = main() 