#!/usr/bin/env python3

import pdfplumber
import re

def analyze_14Q_structure():
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    
    print("Analyzing FR Y-14Q PDF structure...")
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        # Look at first several pages to understand structure
        for page_num, page in enumerate(pdf.pages[:15]):  # First 15 pages
            text = page.extract_text()
            if not text:
                continue
                
            print(f"\n=== PAGE {page_num + 1} ===")
            
            # Look for schedule headers and table structure
            lines = text.split('\n')
            for i, line in enumerate(lines[:25]):  # First 25 lines of each page
                line_stripped = line.strip()
                if any(keyword in line_stripped.upper() for keyword in [
                    'SCHEDULE', 'TABLE', 'ITEM', 'MDRM', 'DESCRIPTION', 
                    'FORMAT', 'QUARTER', 'REGULATORY', 'CAPITAL'
                ]):
                    print(f"Line {i+1}: {line_stripped}")
            
            # Look for MDRM codes
            mdrm_pattern = r'\b(M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2}|\d{4})\b'
            matches = list(re.finditer(mdrm_pattern, text))
            if matches:
                print(f"\nFound {len(matches)} potential MDRM codes on page {page_num + 1}")
                
                # Show context around first few MDRM codes
                for j, match in enumerate(matches[:3]):  # First 3 matches
                    start = max(0, match.start() - 60)
                    end = min(len(text), match.end() + 60)
                    context = text[start:end].replace('\n', ' ')
                    print(f"  MDRM {match.group()}: ...{context}...")
            
            # Look for table patterns
            table_patterns = [
                r'Line\s+Item\s+Name',
                r'Item\s+Number',
                r'Schedule\s+[A-Z]',
                r'Table\s+\d+',
                r'\|\s*\d+\s*\|',  # Pipe-delimited table
                r'\d+\.\d+',  # Decimal numbering
            ]
            
            table_indicators = []
            for pattern in table_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    table_indicators.append(pattern)
            
            if table_indicators:
                print(f"Table patterns found: {table_indicators}")

if __name__ == "__main__":
    analyze_14Q_structure() 