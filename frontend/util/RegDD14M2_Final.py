import pandas as pd
import re
import csv
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import PyPDF2
import pdfplumber
import requests
from io import StringIO, BytesIO

class FRY14MAutomaticExtractor:
    """
    Final improved version that correctly extracts all FR Y-14M schedules with clean descriptions
    """
    
    def __init__(self):
        self.schedules = {
            'A': 'Domestic First Lien Closed-end 1-4 Family Residential Loan',
            'B': 'Domestic Home Equity Loan and Home Equity Line', 
            'C': 'Address Matching Loan Level',
            'D': 'Domestic Credit Card'
        }
        
        self.sub_schedules = {
            'A.1': 'Loan Level Table',
            'A.2': 'Portfolio Level Table', 
            'B.1': 'Loan/Line Level Table',
            'B.2': 'Portfolio Level Table',
            'C.1': 'Data Table',
            'D.1': 'Loan Level Table',
            'D.2': 'Portfolio Level Table'
        }
        
        self.all_data_elements = []
        self.schedule_counts = defaultdict(int)
        self.mdrm_data = {}
        
    def load_mdrm_csv(self, filepath: str) -> pd.DataFrame:
        """Load MDRM CSV from local file"""
        try:
            df = pd.read_csv(filepath, encoding='latin-1')
            # Create a dictionary for quick lookup
            for _, row in df.iterrows():
                if 'MDRM' in df.columns:
                    self.mdrm_data[row['MDRM']] = row.to_dict()
            return df
        except Exception as e:
            print(f"Error loading MDRM CSV: {e}")
            return pd.DataFrame()
    
    def extract_pdf_text_by_schedule(self, pdf_path: str) -> Dict[str, str]:
        """Extract text from PDF organized by sub-schedule with improved detection"""
        schedule_texts = defaultdict(str)
        current_schedule = None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Check if we're starting a new sub-schedule
                    new_schedule = self.detect_schedule_header(text)
                    if new_schedule:
                        current_schedule = new_schedule
                        print(f"Found {current_schedule} on page {page_num + 1}")
                    
                    # Add text to current schedule if we have one
                    if current_schedule:
                        schedule_texts[current_schedule] += text + "\n"
                        
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            
        return dict(schedule_texts)
    
    def detect_schedule_header(self, text: str) -> Optional[str]:
        """Detect which schedule header appears in the text"""
        # Look for explicit table headers like "A.1 Loan Level Table"
        for sub_schedule, table_name in self.sub_schedules.items():
            patterns = [
                rf'{re.escape(sub_schedule)}\s+{re.escape(table_name)}',
                rf'{re.escape(sub_schedule)}\s*{re.escape(table_name)}',
                rf'{re.escape(sub_schedule)}\.\s*{re.escape(table_name)}'
            ]
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return sub_schedule
        
        return None
    
    def clean_description(self, text: str) -> str:
        """Clean up description text by removing format examples and special characters"""
        if not text:
            return ""
        
        # Remove common format examples
        text = re.sub(r'e\.g\.?,?\s*\d+(?:,\d{3})*\s*for\s*\$?\d+(?:,\d{3})*(?:\.\d{2})?', '', text)
        text = re.sub(r'e\.g\.?\s*\$?\d+(?:,\d{3})*(?:\.\d{2})?', '', text)
        
        # Remove format specifications that got mixed in
        text = re.sub(r'Provide as a\s*(?:Numeric|Character|Whole|Text).*?(?:decimal|Number|character)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:Numeric|Character|Whole|Text)\s*(?:\(\d+\))?.*?(?:decimal|Number)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'fraction\.\s*E\.g\.?:\s*to\s*\d+\s*decimal', '', text, flags=re.IGNORECASE)
        
        # Remove specific unwanted patterns
        text = re.sub(r'Current unpaid balance at end of\s*', '', text)
        text = re.sub(r'Amount the funds disbursed.*?Number', '', text)
        text = re.sub(r'Two-letter postal\s*', '', text)
        text = re.sub(r'Five-digit,?\s*Include\s*', '', text)
        text = re.sub(r'RSSD ID of a national bank\s*', '', text)
        text = re.sub(r'Text String\s*', '', text)
        text = re.sub(r'Text line item\.?\s*', '', text)
        
        # Remove coding/value specifications
        text = re.sub(r'\d+\s*=\s*[A-Za-z\s]+(?:Character|Numeric|Whole)', '', text)
        text = re.sub(r'[A-Z]\s*=\s*[A-Za-z\s]+(?:Character|Numeric|Whole)', '', text)
        
        # Remove retired/outdated references
        text = re.sub(r'\(Retired[^)]*\)', '', text)
        
        # Clean up extra whitespace and punctuation
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\s*[-–—]\s*$', '', text)  # Remove trailing dashes
        text = re.sub(r'^\s*[-–—]\s*', '', text)  # Remove leading dashes
        text = text.strip()
        
        return text
    
    def parse_table_from_text(self, text: str, sub_schedule: str) -> List[Dict]:
        """Parse table data from PDF text for a specific sub-schedule"""
        elements = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Find the table start (after headers)
        table_started = False
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for table header pattern
            if re.search(r'Line\s+Line Item Name\s+MDRM\s+Detailed Description', line, re.IGNORECASE):
                table_started = True
                i += 1
                continue
            
            # Alternative header pattern
            if re.search(r'Item.*?MDRM.*?Description', line, re.IGNORECASE):
                table_started = True
                i += 1
                continue
            
            if not table_started:
                i += 1
                continue
            
            # Skip separator lines and empty lines
            if not line or line.startswith('---') or line.startswith('===') or len(line) < 5:
                i += 1
                continue
            
            # Try to parse a table row
            row_data = self.parse_table_row(lines, i)
            if row_data:
                # Add schedule information
                main_schedule = sub_schedule[0]  # A, B, C, or D
                schedule_name = f"Schedule {main_schedule}: {self.schedules[main_schedule]}"
                sub_schedule_name = f"{sub_schedule} {self.sub_schedules[sub_schedule]}"
                
                # Determine mandatory/optional status from description
                mandatory = "Mandatory"
                if any(word in row_data.get('description', '').lower() for word in ['optional', 'best effort']):
                    mandatory = "Optional"
                
                element = {
                    'Report Name': 'FR Y-14M',
                    'Schedule Name': f"{schedule_name} - {sub_schedule_name}",
                    'Line Item #': row_data.get('line_number', ''),
                    'Line Item Name': row_data.get('line_item_name', ''),
                    'Technical Line Item Name': row_data.get('line_item_name', ''),
                    'MDRM': row_data.get('mdrm', ''),
                    'Description': self.clean_description(row_data.get('description', '')),
                    'Static or Dynamic': 'Dynamic',  # Default, can be enhanced
                    'Mandatory or Optional': mandatory,
                    'Format': row_data.get('format', ''),
                    '# of reports or schedules used in': 1,
                    'Other Schedule Reference': ''
                }
                elements.append(element)
                i += row_data.get('lines_consumed', 1)
            else:
                i += 1
        
        return elements
    
    def parse_table_row(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a single table row that may span multiple lines"""
        if start_idx >= len(lines):
            return None
        
        # Look for line number at start of row
        first_line = lines[start_idx].strip()
        
        # Pattern: Line number at start
        line_match = re.match(r'^(\d+)\s+(.+)', first_line)
        if not line_match:
            return None
        
        line_number = int(line_match.group(1))
        rest_of_first_line = line_match.group(2)
        
        # Combine subsequent lines until we find the MDRM code
        combined_text = rest_of_first_line
        lines_consumed = 1
        
        # Look ahead for MDRM code in next few lines
        mdrm_pattern = r'\b(M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2}|\d{4})\b'
        
        for j in range(1, min(8, len(lines) - start_idx)):  # Look ahead up to 7 lines
            next_line = lines[start_idx + j].strip()
            if not next_line:
                break
                
            # Check if this line starts with a new line number (end of current row)
            if re.match(r'^\d+\s+', next_line):
                break
                
            combined_text += " " + next_line
            lines_consumed += 1
            
            # Stop if we found MDRM and have enough content
            if re.search(mdrm_pattern, combined_text) and len(combined_text) > 50:
                break
        
        # Now parse the combined text
        mdrm_match = re.search(mdrm_pattern, combined_text)
        if not mdrm_match:
            return None
        
        mdrm_code = mdrm_match.group(1)
        mdrm_start = mdrm_match.start()
        mdrm_end = mdrm_match.end()
        
        # Extract components
        line_item_name = combined_text[:mdrm_start].strip()
        description_and_format = combined_text[mdrm_end:].strip()
        
        # Try to separate description from format
        format_patterns = [
            r'Character\s*\(\s*\d+\s*\)',
            r'Whole\s+Number',
            r'YYYYMMDD',
            r'YYYYMM', 
            r'Numeric,?\s*(?:up\s+)?to\s+\d+\s+decimal',
            r'Numeric,?\s*to\s+\d+',
            r'Text\s*\(\s*\d+\s*\)',
            r'Character\s*\(\s*\d+\s*\)'
        ]
        
        format_info = ""
        description = description_and_format
        
        for pattern in format_patterns:
            format_match = re.search(pattern, description_and_format, re.IGNORECASE)
            if format_match:
                format_info = format_match.group(0)
                # Remove format from description
                description = description_and_format[:format_match.start()].strip()
                break
        
        return {
            'line_number': line_number,
            'line_item_name': line_item_name,
            'mdrm': mdrm_code,
            'description': description,
            'format': format_info,
            'lines_consumed': lines_consumed
        }
    
    def parse_pdf_instructions(self, pdf_path: str) -> List[Dict]:
        """Parse FR Y-14M instructions PDF to extract data elements"""
        print(f"Parsing PDF: {pdf_path}")
        
        # Extract text by sub-schedule
        schedule_texts = self.extract_pdf_text_by_schedule(pdf_path)
        
        all_elements = []
        
        # Process each sub-schedule
        for sub_schedule, schedule_text in schedule_texts.items():
            if schedule_text:
                print(f"Processing {sub_schedule} ({len(schedule_text)} characters)...")
                elements = self.parse_table_from_text(schedule_text, sub_schedule)
                all_elements.extend(elements)
                self.schedule_counts[sub_schedule] = len(elements)
        
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
                    element['Description'] = mdrm_info['Description']
    
    def create_master_dictionary(self, pdf_path: str, mdrm_csv_path: Optional[str] = None) -> pd.DataFrame:
        """Create the master data dictionary from PDF and optionally MDRM CSV"""
        
        # Load MDRM data if provided
        if mdrm_csv_path:
            print("Loading MDRM CSV...")
            self.load_mdrm_csv(mdrm_csv_path)
        
        # Parse PDF
        self.all_data_elements = self.parse_pdf_instructions(pdf_path)
        
        # Enhance with MDRM data
        if self.mdrm_data:
            self.enhance_with_mdrm_data()
        
        # Identify cross-references
        self.identify_cross_references()
        
        # Sort by schedule and line number
        self.all_data_elements.sort(key=lambda x: (x['Schedule Name'], x['Line Item #']))
        
        # Create DataFrame
        df = pd.DataFrame(self.all_data_elements)
        
        return df
    
    def save_to_pipe_delimited(self, df: pd.DataFrame, filename: str):
        """Save the dataframe to a pipe-delimited file"""
        df.to_csv(filename, sep='|', index=False, quoting=csv.QUOTE_MINIMAL)
    
    def print_summary_statistics(self):
        """Print summary statistics of the extracted data"""
        print("\n" + "="*80)
        print("FR Y-14M DATA DICTIONARY EXTRACTION SUMMARY (FINAL)")
        print("="*80)
        print(f"\nTotal data elements extracted: {len(self.all_data_elements)}")
        print("\nElements by Sub-Schedule:")
        print("-"*40)
        
        for schedule, count in sorted(self.schedule_counts.items()):
            print(f"  {schedule} {self.sub_schedules.get(schedule, '')}: {count} elements")
        
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
    """Main function to run the final FR Y-14M automatic dictionary extraction"""
    
    # File paths - updated to use the correct directories
    pdf_path = "_reference/regulations/14M/FR_Y-14M_Instructions.pdf"
    mdrm_csv_path = "_reference/regulations/MDRM_CSV.csv"
    output_dir = "_reference/regulations/output"
    
    # Initialize extractor
    extractor = FRY14MAutomaticExtractor()
    
    # Create master dictionary
    print("Creating FR Y-14M Master Data Dictionary (Final Version)...")
    print("This will extract all schedules with clean descriptions...")
    
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
        output_filename = os.path.join(output_dir, "FR_Y14M_Master_Data_Dictionary_Final.txt")
        extractor.save_to_pipe_delimited(df, output_filename)
        print(f"\nFinal data dictionary saved to: {output_filename}")
        
        # Print summary statistics
        extractor.print_summary_statistics()
        
        # Display sample records
        print("\nSample Records from Final Master Dictionary:")
        print("-"*80)
        if not df.empty:
            # Show a few records from each schedule
            for schedule in sorted(extractor.schedule_counts.keys()):
                schedule_df = df[df['Schedule Name'].str.contains(schedule)]
                if not schedule_df.empty:
                    print(f"\n{schedule} sample:")
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