#!/usr/bin/env python3

import pdfplumber
import re

def find_14Q_content():
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    
    print("Finding actual data content in FR Y-14Q PDF...")
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        # Search through all pages for data content
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Look for actual data tables with MDRM codes
            mdrm_pattern = r'\b(M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2})\b'
            matches = list(re.finditer(mdrm_pattern, text))
            
            # Look for table-like structures
            lines = text.split('\n')
            has_table_structure = False
            
            for line in lines:
                if any(keyword in line.lower() for keyword in [
                    'summary variable', 'line item', 'variable name', 'item name'
                ]) and len(line.strip()) > 10:
                    has_table_structure = True
                    break
            
            # If we found MDRM codes AND table structure
            if matches and has_table_structure:
                print(f"\n=== PAGE {page_num + 1} - FOUND DATA CONTENT ===")
                
                # Show the structure
                for i, line in enumerate(lines[:30]):  # First 30 lines
                    line_stripped = line.strip()
                    if line_stripped and (
                        'summary variable' in line_stripped.lower() or
                        'line item' in line_stripped.lower() or
                        'variable name' in line_stripped.lower() or
                        'mdrm' in line_stripped.lower() or
                        re.search(mdrm_pattern, line_stripped)
                    ):
                        print(f"Line {i+1}: {line_stripped}")
                
                # Show first few MDRM examples
                print(f"\nFound {len(matches)} MDRM codes on this page:")
                for j, match in enumerate(matches[:5]):  # First 5 matches
                    start = max(0, match.start() - 40)
                    end = min(len(text), match.end() + 40)
                    context = text[start:end].replace('\n', ' ')
                    print(f"  {j+1}. MDRM {match.group()}: ...{context}...")
                
                # Check if this looks like a real data table
                data_indicators = 0
                for line in lines:
                    if re.search(r'Summary Variable\s*#?\d+', line, re.IGNORECASE):
                        data_indicators += 1
                    if re.search(r'\d+\s+\w+.*[A-Z]\d{3}', line):
                        data_indicators += 1
                    if '|' in line and len(line.split('|')) > 2:
                        data_indicators += 1
                
                print(f"Data table indicators: {data_indicators}")
                
                # Stop after finding several good examples
                if page_num > 100:  # Don't search the entire document
                    break

if __name__ == "__main__":
    find_14Q_content() 