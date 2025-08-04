import pandas as pd
import re
import csv
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import PyPDF2
import pdfplumber
import requests
from io import StringIO, BytesIO

class FRY14QAutomaticExtractor:
    """
    Specialized extractor for FR Y-14Q data dictionary - different structure than 14M
    """
    
    def __init__(self):
        self.schedules = {
            'A': 'Retail',
            'B': 'Securities',
            'C': 'Regulatory Capital Instruments',
            'D': 'Regulatory Capital',
            'E': 'MSR Valuation',
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
        """Load MDRM CSV from local file with enhanced matching for 14Q"""
        try:
            df = pd.read_csv(filepath, encoding='latin-1')
            # Create a dictionary for quick lookup
            for _, row in df.iterrows():
                # Try different possible MDRM column names
                mdrm_columns = ['MDRM', 'MDRM_CODE', 'Code', 'ITEM_CODE']
                mdrm_value = None
                
                for col in mdrm_columns:
                    if col in df.columns and pd.notna(row[col]):
                        mdrm_value = str(row[col]).strip()
                        break
                
                if mdrm_value:
                    self.mdrm_data[mdrm_value] = row.to_dict()
                    
            print(f"Loaded {len(self.mdrm_data)} MDRM entries for 14Q matching")
            return df
        except Exception as e:
            print(f"Error loading MDRM CSV: {e}")
            return pd.DataFrame()
    
    def extract_pdf_text_by_schedule(self, pdf_path: str) -> Dict[str, str]:
        """Extract text from PDF organized by schedule for 14Q format"""
        schedule_texts = defaultdict(str)
        current_schedule = None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Look for schedule headers in 14Q format
                    new_schedule = self.detect_14Q_schedule_header(text)
                    if new_schedule:
                        current_schedule = new_schedule
                        print(f"Found Schedule {current_schedule} on page {page_num + 1}")
                    
                    # Add text to current schedule if we have one
                    if current_schedule:
                        schedule_texts[current_schedule] += text + "\n"
                        
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            
        return dict(schedule_texts)
    
    def detect_14Q_schedule_header(self, text: str) -> Optional[str]:
        """Detect FR Y-14Q schedule headers - different format than 14M"""
        # Look for schedule patterns specific to 14Q
        patterns = [
            r'Schedule\s+([A-L])\s*[–-]\s*(.+?)(?:\s*\.{3,}|\n)',
            r'Schedule\s+([A-L])\s*[–-]\s*(.+)',
            r'([A-L])\.\d+\s*[–-]\s*(.+)',  # e.g., "A.1 - DOMESTIC FIRST LIEN"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                schedule_id = match.group(1).upper()
                if schedule_id in self.schedules:
                    return schedule_id
        
        return None
    
    def clean_description(self, text: str) -> str:
        """Clean up description text for 14Q format"""
        if not text:
            return ""
        
        # Remove format examples specific to 14Q
        text = re.sub(r'e\.g\.?,?\s*\d+(?:,\d{3})*(?:\.\d{2})?', '', text)
        text = re.sub(r'Rounded whole dollar amount,?\s*', '', text)
        text = re.sub(r'Supply numeric values without any non-numeric formatting', '', text)
        text = re.sub(r'\(no dollar sign, commas or decimal\)', '', text)
        text = re.sub(r'For negative values use a negative sign.*?\)', '', text)
        
        # Remove format specifications
        text = re.sub(r'Format:\s*[A-Za-z0-9\(\)\s,]+', '', text)
        text = re.sub(r'Allowable Values:\s*[^\.]+\.', '', text)
        
        # Clean up extra whitespace and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*[-–—]\s*$', '', text)
        text = re.sub(r'^\s*[-–—]\s*', '', text)
        text = text.strip()
        
        return text
    
    def parse_14Q_table_format(self, text: str, schedule: str) -> List[Dict]:
        """Parse 14Q-specific table format which differs from 14M"""
        elements = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for 14Q table headers
            if any(header in line for header in [
                'Field Name', 'Field No.', 'Technical Field', 'MDRM', 'Description'
            ]):
                i += 1
                continue
            
            # Skip empty lines and separators
            if not line or len(line) < 10:
                i += 1
                continue
            
            # Try to parse 14Q format row
            row_data = self.parse_14Q_row(lines, i)
            if row_data:
                # Create element for 14Q
                element = {
                    'Report Name': 'FR Y-14Q',
                    'Schedule Name': f"Schedule {schedule}: {self.schedules.get(schedule, schedule)}",
                    'Line Item #': row_data.get('field_number', ''),
                    'Line Item Name': row_data.get('field_name', ''),
                    'Technical Line Item Name': row_data.get('technical_name', ''),
                    'MDRM': row_data.get('mdrm', ''),
                    'Description': self.clean_description(row_data.get('description', '')),
                    'Static or Dynamic': 'Dynamic',  # Default for 14Q
                    'Mandatory or Optional': row_data.get('mandatory', 'Mandatory'),
                    'Format': row_data.get('format', ''),
                    '# of reports or schedules used in': 1,
                    'Other Schedule Reference': ''
                }
                elements.append(element)
                i += row_data.get('lines_consumed', 1)
            else:
                i += 1
        
        return elements
    
    def parse_14Q_row(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a single 14Q table row - different format than 14M"""
        if start_idx >= len(lines):
            return None
        
        combined_text = ""
        lines_consumed = 1
        
        # Combine lines until we have enough content
        for j in range(start_idx, min(start_idx + 8, len(lines))):
            line = lines[j].strip()
            if not line:
                break
            combined_text += " " + line
            if j > start_idx:
                lines_consumed += 1
            
            # Stop if we hit what looks like a new field
            if j > start_idx and re.match(r'^\d+\s+', line):
                lines_consumed -= 1
                break
        
        combined_text = combined_text.strip()
        
        # Look for MDRM pattern
        mdrm_pattern = r'\b([A-Z]{2,4}\d{3,4}|M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2})\b'
        mdrm_match = re.search(mdrm_pattern, combined_text)
        
        if not mdrm_match:
            return None
        
        mdrm_code = mdrm_match.group(1)
        
        # Try to extract field number at the beginning
        field_num_match = re.match(r'^(\d+)\s+(.+)', combined_text)
        field_number = ""
        field_content = combined_text
        
        if field_num_match:
            field_number = field_num_match.group(1)
            field_content = field_num_match.group(2)
        
        # Extract field name (usually before MDRM)
        mdrm_start = mdrm_match.start()
        field_name_part = combined_text[:mdrm_start].strip()
        
        # Remove field number from field name if present
        if field_number and field_name_part.startswith(field_number):
            field_name_part = field_name_part[len(field_number):].strip()
        
        # Split field name part - sometimes has technical name in parentheses
        field_name = field_name_part
        technical_name = ""
        
        paren_match = re.search(r'\(([^)]+)\)', field_name_part)
        if paren_match:
            technical_name = paren_match.group(1)
            field_name = re.sub(r'\([^)]+\)', '', field_name_part).strip()
        
        # Extract description (after MDRM)
        description = combined_text[mdrm_match.end():].strip()
        
        # Look for mandatory/optional
        mandatory = "Mandatory"
        if "optional" in description.lower():
            mandatory = "Optional"
        
        # Extract format information
        format_patterns = [
            r'Rounded whole dollar amount',
            r'Character\s*\(\s*\d+\s*\)',
            r'Numeric\s*\(\s*\d+(?:,\d+)?\s*\)',
            r'Date\s*\(YYYYMMDD\)',
            r'Text\s*\(\s*\d+\s*\)'
        ]
        
        format_info = ""
        for pattern in format_patterns:
            format_match = re.search(pattern, description, re.IGNORECASE)
            if format_match:
                format_info = format_match.group(0)
                break
        
        return {
            'field_number': field_number,
            'field_name': field_name,
            'technical_name': technical_name or field_name,
            'mdrm': mdrm_code,
            'description': description,
            'mandatory': mandatory,
            'format': format_info,
            'lines_consumed': lines_consumed
        }
    
    def parse_pdf_instructions(self, pdf_path: str) -> List[Dict]:
        """Parse FR Y-14Q instructions PDF to extract data elements"""
        print(f"Parsing 14Q PDF: {pdf_path}")
        
        # Extract text by schedule
        schedule_texts = self.extract_pdf_text_by_schedule(pdf_path)
        
        all_elements = []
        
        # Process each schedule
        for schedule, schedule_text in schedule_texts.items():
            if schedule_text:
                print(f"Processing Schedule {schedule} ({len(schedule_text)} characters)...")
                elements = self.parse_14Q_table_format(schedule_text, schedule)
                all_elements.extend(elements)
                self.schedule_counts[schedule] = len(elements)
        
        return all_elements
    
    def identify_cross_references(self):
        """Identify MDRM codes that appear in multiple schedules"""
        mdrm_schedule_map = defaultdict(list)
        
        # Build map of MDRM to schedules
        for element in self.all_data_elements:
            if element['MDRM']:
                mdrm_schedule_map[element['MDRM']].append(element['Schedule Name'])
        
        # Update elements with cross-references
        for element in self.all_data_elements:
            if element['MDRM'] in mdrm_schedule_map:
                schedules = list(set(mdrm_schedule_map[element['MDRM']]))
                element['# of reports or schedules used in'] = len(schedules)
                
                # Generate other schedule references
                current_schedule = element['Schedule Name']
                other_schedules = [s for s in schedules if s != current_schedule]
                element['Other Schedule Reference'] = ', '.join(other_schedules) if other_schedules else ''
    
    def enhance_with_mdrm_data(self):
        """Enhance extracted elements with MDRM metadata"""
        for element in self.all_data_elements:
            mdrm_code = element['MDRM']
            if mdrm_code in self.mdrm_data:
                mdrm_info = self.mdrm_data[mdrm_code]
                # Add additional metadata from MDRM if available
                if 'Description' in mdrm_info and not element['Description']:
                    element['Description'] = str(mdrm_info['Description'])
    
    def create_master_dictionary(self, pdf_path: str, mdrm_csv_path: Optional[str] = None) -> pd.DataFrame:
        """Create the master data dictionary for FR Y-14Q"""
        
        # Load MDRM data if provided
        if mdrm_csv_path:
            print("Loading MDRM CSV for 14Q...")
            self.load_mdrm_csv(mdrm_csv_path)
        
        # Parse PDF
        self.all_data_elements = self.parse_pdf_instructions(pdf_path)
        
        # Enhance with MDRM data
        if self.mdrm_data:
            self.enhance_with_mdrm_data()
        
        # Identify cross-references
        self.identify_cross_references()
        
        # Sort by schedule and line number
        self.all_data_elements.sort(key=lambda x: (x['Schedule Name'], 
                                                  int(x['Line Item #']) if x['Line Item #'].isdigit() else 999))
        
        # Create DataFrame
        df = pd.DataFrame(self.all_data_elements)
        
        return df
    
    def save_to_pipe_delimited(self, df: pd.DataFrame, filename: str):
        """Save the dataframe to a pipe-delimited file"""
        df.to_csv(filename, sep='|', index=False, quoting=csv.QUOTE_MINIMAL)
    
    def print_summary_statistics(self):
        """Print summary statistics of the extracted data"""
        print("\n" + "="*80)
        print("FR Y-14Q DATA DICTIONARY EXTRACTION SUMMARY")
        print("="*80)
        print(f"\nTotal data elements extracted: {len(self.all_data_elements)}")
        print("\nElements by Schedule:")
        print("-"*40)
        
        for schedule, count in sorted(self.schedule_counts.items()):
            schedule_name = self.schedules.get(schedule, schedule)
            print(f"  Schedule {schedule} ({schedule_name}): {count} elements")
        
        print("\nData Quality Checks:")
        print("-"*40)
        
        # Check for missing MDRM codes
        missing_mdrm = sum(1 for e in self.all_data_elements if not e['MDRM'])
        print(f"  Elements without MDRM codes: {missing_mdrm}")
        
        # Check for cross-referenced elements
        cross_ref_count = sum(1 for e in self.all_data_elements if e['# of reports or schedules used in'] > 1)
        print(f"  Elements used in multiple schedules: {cross_ref_count}")
        
        # Check format information
        with_format = sum(1 for e in self.all_data_elements if e['Format'])
        print(f"  Elements with format information: {with_format}")
        
        # Check clean descriptions
        clean_desc = sum(1 for e in self.all_data_elements if e['Description'] and len(e['Description']) > 10)
        print(f"  Elements with meaningful descriptions: {clean_desc}")
        
        print("\n" + "="*80)


def main():
    """Main function to run the FR Y-14Q automatic dictionary extraction"""
    
    # File paths
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    mdrm_csv_path = "_reference/regulations/MDRM_CSV.csv"
    output_dir = "_reference/regulations/output"
    
    # Initialize extractor
    extractor = FRY14QAutomaticExtractor()
    
    # Create master dictionary
    print("Creating FR Y-14Q Master Data Dictionary...")
    print("This will extract data elements from the 14Q format...")
    
    try:
        # Check if MDRM CSV exists
        import os
        if not os.path.exists(mdrm_csv_path):
            print(f"\nNote: MDRM CSV not found at {mdrm_csv_path}")
            print("Proceeding with PDF extraction only...")
            mdrm_csv_path = None
        
        # Check if PDF exists
        if not os.path.exists(pdf_path):
            print(f"\nError: PDF file not found at {pdf_path}")
            return pd.DataFrame()
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
        # Create dictionary
        df = extractor.create_master_dictionary(pdf_path, mdrm_csv_path)
        
        # Save to pipe-delimited file in output directory
        output_filename = os.path.join(output_dir, "FR_Y14Q_Master_Data_Dictionary.txt")
        extractor.save_to_pipe_delimited(df, output_filename)
        print(f"\n14Q data dictionary saved to: {output_filename}")
        
        # Print summary statistics
        extractor.print_summary_statistics()
        
        # Display sample records
        print("\nSample Records from 14Q Master Dictionary:")
        print("-"*80)
        if not df.empty:
            # Show a few records from each schedule
            for schedule in sorted(extractor.schedule_counts.keys()):
                schedule_df = df[df['Schedule Name'].str.contains(f'Schedule {schedule}')]
                if not schedule_df.empty:
                    print(f"\nSchedule {schedule} sample:")
                    print(schedule_df.head(3)[['Line Item #', 'Line Item Name', 'MDRM', 'Description']].to_string(index=False))
        else:
            print("No data elements extracted. Please check the PDF format.")
        
        return df
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print(f"Please ensure the required files exist:")
        print(f"  PDF: {pdf_path}")
        print(f"  MDRM CSV: {mdrm_csv_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"\nError during extraction: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    df = main() 