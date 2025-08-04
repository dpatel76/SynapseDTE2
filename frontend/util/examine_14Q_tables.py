#!/usr/bin/env python3

import pdfplumber
import re

def examine_14Q_tables():
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    
    print("Examining FR Y-14Q table structures in detail...")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Focus on pages that likely contain actual table data
        for page_num in range(15, 35):  # Pages 16-35 likely have table structures
            if page_num >= len(pdf.pages):
                break
                
            page = pdf.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
            
            # Look for pages with detailed table structures
            if any(indicator in text for indicator in [
                'Line Item', 'MDRM', 'Variable Name', 'Format', 
                'Schedule A', 'Item Name', 'Description'
            ]):
                print(f"\n=== PAGE {page_num + 1} - TABLE CONTENT ===")
                lines = text.split('\n')
                
                # Show table headers and structure
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if any(keyword in line_stripped for keyword in [
                        'Line Item', 'MDRM', 'Variable Name', 'Format',
                        'Description', 'Item Name', 'Summary Variable'
                    ]):
                        print(f"Header Line {i+1}: {line_stripped}")
                
                # Look for actual data rows
                print("\nData rows with MDRM codes:")
                mdrm_pattern = r'\b(M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2}|\d{4})\b'
                
                for i, line in enumerate(lines):
                    if re.search(mdrm_pattern, line):
                        # Show this line and context
                        start_context = max(0, i - 1)
                        end_context = min(len(lines), i + 2)
                        print(f"\nRow context around line {i+1}:")
                        for j in range(start_context, end_context):
                            marker = ">>> " if j == i else "    "
                            print(f"{marker}{j+1}: {lines[j].strip()}")
                        break  # Just show first example per page
                
                # Check for table structure patterns
                table_structures = []
                for line in lines:
                    # Look for specific table formatting
                    if re.search(r'\|\s*[A-Za-z]', line):  # Pipe-delimited
                        table_structures.append("Pipe-delimited")
                    if re.search(r'\d+\s+[A-Za-z].*\s+[A-Z]\d{3}', line):  # Number + text + MDRM
                        table_structures.append("Number-Text-MDRM format")
                    if re.search(r'Summary Variable\s*#?\d+', line):  # Summary variables
                        table_structures.append("Summary Variable format")
                
                if table_structures:
                    print(f"Table structures detected: {list(set(table_structures))}")
                
                # Stop after finding a few good examples
                if page_num > 25:
                    break

if __name__ == "__main__":
    examine_14Q_tables() 