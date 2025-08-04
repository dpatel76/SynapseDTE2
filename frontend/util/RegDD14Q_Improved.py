import pandas as pd
import re
import csv
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import PyPDF2
import pdfplumber
import requests
from io import StringIO, BytesIO

class FRY14QImprovedExtractor:
    """
    Improved extractor for FR Y-14Q that better handles the complex table structure
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
        
    def load_mdrm_csv(self, filepath: str) -> pd.DataFrame:
        """Load MDRM CSV with better matching for 14Q"""
        try:
            df = pd.read_csv(filepath, encoding='latin-1')
            # Create lookup dictionary for MDRM codes
            for _, row in df.iterrows():
                # Try different column names for MDRM codes
                mdrm_columns = ['MDRM', 'MDRM_CODE', 'Code', 'ITEM_CODE', 'Item Code']
                mdrm_value = None
                
                for col in mdrm_columns:
                    if col in df.columns and pd.notna(row[col]):
                        mdrm_value = str(row[col]).strip()
                        break
                
                if mdrm_value:
                    self.mdrm_data[mdrm_value] = row.to_dict()
                    
            print(f"Loaded {len(self.mdrm_data)} MDRM entries")
            return df
        except Exception as e:
            print(f"Error loading MDRM CSV: {e}")
            return pd.DataFrame()
    
    def extract_structured_tables(self, pdf_path: str) -> Dict[str, List[Dict]]:
        """Extract structured table data from FR Y-14Q using table detection"""
        schedule_data = defaultdict(list)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                current_schedule = None
                
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Detect schedule headers
                    new_schedule = self.detect_schedule_header(text, page_num)
                    if new_schedule:
                        current_schedule = new_schedule
                        print(f"Found Schedule {current_schedule} on page {page_num + 1}")
                    
                    # Try to extract tables from the page
                    tables = page.extract_tables()
                    if tables and current_schedule:
                        for table in tables:
                            processed_table = self.process_table_data(table, current_schedule, page_num)
                            if processed_table:
                                schedule_data[current_schedule].extend(processed_table)
                    
                    # Also try text-based extraction for complex layouts
                    if current_schedule and not tables:
                        text_elements = self.extract_from_text_layout(text, current_schedule, page_num)
                        if text_elements:
                            schedule_data[current_schedule].extend(text_elements)
                            
        except Exception as e:
            print(f"Error extracting structured tables: {e}")
            
        return dict(schedule_data)
    
    def detect_schedule_header(self, text: str, page_num: int) -> Optional[str]:
        """Detect schedule headers in FR Y-14Q format"""
        lines = text.split('\n')
        
        for line in lines[:10]:  # Check first 10 lines of page
            # Look for main schedule patterns
            schedule_patterns = [
                r'Schedule\s+([A-L])\s*[–-]',
                r'([A-L])\.\d+\s*[–-]',
                r'Schedule\s+([A-L])—',
                r'^\s*([A-L])\s*[–-]'
            ]
            
            for pattern in schedule_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    schedule_id = match.group(1).upper()
                    if schedule_id in self.schedules:
                        return schedule_id
        
        return None
    
    def process_table_data(self, table: List[List], schedule: str, page_num: int) -> List[Dict]:
        """Process extracted table data into structured format"""
        elements = []
        
        if not table or len(table) < 2:
            return elements
        
        # Look for table headers
        headers = []
        data_start_row = 0
        
        for i, row in enumerate(table[:5]):  # Check first 5 rows for headers
            if row and any(header in str(cell).lower() for cell in row if cell for header in [
                'field', 'mdrm', 'description', 'line item', 'variable'
            ]):
                headers = [str(cell).strip() if cell else '' for cell in row]
                data_start_row = i + 1
                break
        
        # Process data rows
        for i in range(data_start_row, len(table)):
            row = table[i]
            if not row or all(not cell or str(cell).strip() == '' for cell in row):
                continue
            
            # Try to extract structured data from row
            element = self.parse_table_row(row, headers, schedule, page_num)
            if element:
                elements.append(element)
        
        return elements
    
    def parse_table_row(self, row: List, headers: List[str], schedule: str, page_num: int) -> Optional[Dict]:
        """Parse a single table row into a structured element"""
        if not row:
            return None
        
        # Convert row to string values
        row_data = [str(cell).strip() if cell else '' for cell in row]
        combined_text = ' '.join(row_data)
        
        # Look for MDRM codes
        mdrm_pattern = r'\b([A-Z]{2,5}\d{3,4}|M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2}|\d{4})\b'
        mdrm_matches = re.findall(mdrm_pattern, combined_text)
        
        if not mdrm_matches:
            return None
        
        mdrm_code = mdrm_matches[0]
        
        # Try to extract field number
        field_num_pattern = r'^\s*(\d+)\s+'
        field_num_match = re.search(field_num_pattern, combined_text)
        field_number = field_num_match.group(1) if field_num_match else ''
        
        # Extract field name and description
        field_name = ""
        description = ""
        technical_name = ""
        format_info = ""
        
        # Try to map to table headers if available
        if headers and len(row_data) >= len(headers):
            for j, header in enumerate(headers):
                if j < len(row_data):
                    cell_value = row_data[j]
                    header_lower = header.lower()
                    
                    if 'field name' in header_lower or 'name' in header_lower:
                        field_name = cell_value
                    elif 'technical' in header_lower:
                        technical_name = cell_value
                    elif 'description' in header_lower:
                        description = cell_value
                    elif 'format' in header_lower or 'allowable' in header_lower:
                        format_info = cell_value
        else:
            # Fallback: extract from combined text
            # Split around MDRM code to get name and description
            mdrm_pos = combined_text.find(mdrm_code)
            if mdrm_pos > 0:
                before_mdrm = combined_text[:mdrm_pos].strip()
                after_mdrm = combined_text[mdrm_pos + len(mdrm_code):].strip()
                
                # Remove field number from field name
                if field_number and before_mdrm.startswith(field_number):
                    before_mdrm = before_mdrm[len(field_number):].strip()
                
                field_name = before_mdrm[:50] if before_mdrm else ""
                description = after_mdrm[:200] if after_mdrm else ""
        
        # Clean up extracted data
        field_name = self.clean_field_text(field_name)
        description = self.clean_field_text(description)
        technical_name = technical_name or field_name
        
        # Determine mandatory/optional
        mandatory = "Mandatory"
        if "optional" in description.lower():
            mandatory = "Optional"
        
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
            'Other Schedule Reference': ''
        }
    
    def extract_from_text_layout(self, text: str, schedule: str, page_num: int) -> List[Dict]:
        """Extract data from text layout when table extraction fails"""
        elements = []
        lines = text.split('\n')
        
        # Look for field definitions in text
        current_field = {}
        field_buffer = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Look for field number pattern
            field_pattern = r'^(\d+)\s+(.+)'
            field_match = re.match(field_pattern, line_stripped)
            
            if field_match:
                # Save previous field if complete
                if current_field and 'mdrm' in current_field:
                    element = self.create_element_from_field_data(current_field, schedule)
                    if element:
                        elements.append(element)
                
                # Start new field
                current_field = {
                    'number': field_match.group(1),
                    'content': field_match.group(2),
                    'full_text': line_stripped
                }
                field_buffer = [line_stripped]
            else:
                # Continue current field
                if current_field:
                    field_buffer.append(line_stripped)
                    current_field['full_text'] = ' '.join(field_buffer)
            
            # Look for MDRM codes in current field
            if current_field and 'mdrm' not in current_field:
                mdrm_pattern = r'\b([A-Z]{2,5}\d{3,4}|M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2})\b'
                mdrm_match = re.search(mdrm_pattern, current_field['full_text'])
                if mdrm_match:
                    current_field['mdrm'] = mdrm_match.group(1)
        
        # Process final field
        if current_field and 'mdrm' in current_field:
            element = self.create_element_from_field_data(current_field, schedule)
            if element:
                elements.append(element)
        
        return elements
    
    def create_element_from_field_data(self, field_data: Dict, schedule: str) -> Optional[Dict]:
        """Create a data element from extracted field data"""
        if not field_data.get('mdrm'):
            return None
        
        full_text = field_data.get('full_text', '')
        mdrm_code = field_data['mdrm']
        
        # Extract field name (between field number and MDRM)
        field_name = ""
        description = ""
        
        mdrm_pos = full_text.find(mdrm_code)
        if mdrm_pos > 0:
            before_mdrm = full_text[:mdrm_pos].strip()
            after_mdrm = full_text[mdrm_pos + len(mdrm_code):].strip()
            
            # Remove field number
            field_number = field_data.get('number', '')
            if field_number and before_mdrm.startswith(field_number):
                before_mdrm = before_mdrm[len(field_number):].strip()
            
            # Field name is the cleaned text before MDRM
            field_name = self.clean_field_text(before_mdrm)
            description = self.clean_field_text(after_mdrm)
        
        # Determine format from description
        format_info = ""
        format_patterns = [
            r'Rounded whole dollar amount',
            r'Must be in yyyy-mm-dd format',
            r'Free text',
            r'Numeric\s*\(\s*\d+(?:,\d+)?\s*\)',
            r'Character\s*\(\s*\d+\s*\)'
        ]
        
        for pattern in format_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                format_info = re.search(pattern, description, re.IGNORECASE).group(0)
                break
        
        return {
            'Report Name': 'FR Y-14Q',
            'Schedule Name': f"Schedule {schedule}: {self.schedules.get(schedule, schedule)}",
            'Line Item #': field_data.get('number', ''),
            'Line Item Name': field_name,
            'Technical Line Item Name': field_name,
            'MDRM': mdrm_code,
            'Description': description,
            'Static or Dynamic': 'Dynamic',
            'Mandatory or Optional': 'Optional' if 'optional' in description.lower() else 'Mandatory',
            'Format': format_info,
            '# of reports or schedules used in': 1,
            'Other Schedule Reference': ''
        }
    
    def clean_field_text(self, text: str) -> str:
        """Clean up field text"""
        if not text:
            return ""
        
        # Remove common formatting artifacts
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'^[-–—]\s*', '', text)
        text = re.sub(r'\s*[-–—]\s*$', '', text)
        text = text.strip()
        
        # Truncate if too long
        if len(text) > 100:
            text = text[:97] + "..."
        
        return text
    
    def create_master_dictionary(self, pdf_path: str, mdrm_csv_path: Optional[str] = None) -> pd.DataFrame:
        """Create the master data dictionary for FR Y-14Q"""
        
        # Load MDRM data if provided
        if mdrm_csv_path:
            print("Loading MDRM CSV...")
            self.load_mdrm_csv(mdrm_csv_path)
        
        # Extract structured data
        print("Extracting structured table data...")
        schedule_data = self.extract_structured_tables(pdf_path)
        
        # Combine all elements
        for schedule, elements in schedule_data.items():
            self.all_data_elements.extend(elements)
            self.schedule_counts[schedule] = len(elements)
        
        # Enhance with MDRM data
        if self.mdrm_data:
            self.enhance_with_mdrm_data()
        
        # Identify cross-references
        self.identify_cross_references()
        
        # Sort by schedule and line number
        self.all_data_elements.sort(key=lambda x: (
            x['Schedule Name'], 
            int(x['Line Item #']) if x['Line Item #'].isdigit() else 999
        ))
        
        return pd.DataFrame(self.all_data_elements)
    
    def enhance_with_mdrm_data(self):
        """Enhance extracted elements with MDRM metadata"""
        for element in self.all_data_elements:
            mdrm_code = element['MDRM']
            if mdrm_code in self.mdrm_data:
                mdrm_info = self.mdrm_data[mdrm_code]
                # Add additional metadata if missing
                if not element['Description'] and 'Description' in mdrm_info:
                    element['Description'] = str(mdrm_info['Description'])
    
    def identify_cross_references(self):
        """Identify MDRM codes used in multiple schedules"""
        mdrm_schedule_map = defaultdict(list)
        
        for element in self.all_data_elements:
            if element['MDRM']:
                mdrm_schedule_map[element['MDRM']].append(element['Schedule Name'])
        
        for element in self.all_data_elements:
            if element['MDRM'] in mdrm_schedule_map:
                schedules = list(set(mdrm_schedule_map[element['MDRM']]))
                element['# of reports or schedules used in'] = len(schedules)
                
                current_schedule = element['Schedule Name']
                other_schedules = [s for s in schedules if s != current_schedule]
                element['Other Schedule Reference'] = ', '.join(other_schedules) if other_schedules else ''
    
    def save_to_pipe_delimited(self, df: pd.DataFrame, filename: str):
        """Save the dataframe to a pipe-delimited file"""
        df.to_csv(filename, sep='|', index=False, quoting=csv.QUOTE_MINIMAL)
    
    def print_summary_statistics(self):
        """Print summary statistics"""
        print("\n" + "="*80)
        print("FR Y-14Q IMPROVED DATA DICTIONARY EXTRACTION SUMMARY")
        print("="*80)
        print(f"\nTotal data elements extracted: {len(self.all_data_elements)}")
        print("\nElements by Schedule:")
        print("-"*40)
        
        for schedule, count in sorted(self.schedule_counts.items()):
            schedule_name = self.schedules.get(schedule, schedule)
            print(f"  Schedule {schedule} ({schedule_name}): {count} elements")
        
        print("\nData Quality Metrics:")
        print("-"*40)
        
        # Quality checks
        missing_mdrm = sum(1 for e in self.all_data_elements if not e['MDRM'])
        missing_desc = sum(1 for e in self.all_data_elements if not e['Description'])
        with_format = sum(1 for e in self.all_data_elements if e['Format'])
        cross_ref = sum(1 for e in self.all_data_elements if e['# of reports or schedules used in'] > 1)
        
        print(f"  Elements without MDRM codes: {missing_mdrm}")
        print(f"  Elements without descriptions: {missing_desc}")
        print(f"  Elements with format info: {with_format}")
        print(f"  Elements used across schedules: {cross_ref}")
        
        print("\n" + "="*80)


def main():
    """Main function to run the improved FR Y-14Q extraction"""
    
    # File paths
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    mdrm_csv_path = "_reference/regulations/MDRM_CSV.csv"
    output_dir = "_reference/regulations/output"
    
    # Initialize extractor
    extractor = FRY14QImprovedExtractor()
    
    print("Creating Improved FR Y-14Q Master Data Dictionary...")
    print("Using enhanced table extraction and text parsing...")
    
    try:
        import os
        
        # Check files
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found at {pdf_path}")
            return pd.DataFrame()
        
        if not os.path.exists(mdrm_csv_path):
            print(f"Note: MDRM CSV not found at {mdrm_csv_path}")
            mdrm_csv_path = None
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create dictionary
        df = extractor.create_master_dictionary(pdf_path, mdrm_csv_path)
        
        # Save results
        output_filename = os.path.join(output_dir, "FR_Y14Q_Master_Data_Dictionary_Improved.txt")
        extractor.save_to_pipe_delimited(df, output_filename)
        print(f"\nImproved 14Q data dictionary saved to: {output_filename}")
        
        # Print summary
        extractor.print_summary_statistics()
        
        # Show sample records
        print("\nSample Records from Improved Dictionary:")
        print("-"*80)
        if not df.empty:
            sample_df = df.head(10)
            for _, row in sample_df.iterrows():
                print(f"\nSchedule: {row['Schedule Name']}")
                print(f"Field {row['Line Item #']}: {row['Line Item Name']}")
                print(f"MDRM: {row['MDRM']}")
                print(f"Description: {row['Description'][:100]}...")
                print("-" * 50)
        
        return df
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    df = main() 