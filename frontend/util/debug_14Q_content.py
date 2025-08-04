#!/usr/bin/env python3

import pdfplumber
import re
from collections import defaultdict

def debug_14Q_content():
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    
    print("🔍 DEEP DEBUGGING FR Y-14Q CONTENT STRUCTURE")
    print("=" * 70)
    
    # Focus on pages we know have schedules
    target_pages = [
        161,  # Schedule H start
        162,  # Schedule H content
        163,  # Schedule H content
        200,  # Mid Schedule H
        250,  # Near end Schedule H
    ]
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in target_pages:
            if page_num >= len(pdf.pages):
                continue
                
            print(f"\n{'='*50}")
            print(f"PAGE {page_num + 1} ANALYSIS")
            print(f"{'='*50}")
            
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            if not text:
                print("❌ No text found on this page")
                continue
            
            # Show raw text structure
            lines = text.split('\n')
            print(f"\n📄 RAW TEXT STRUCTURE ({len(lines)} lines):")
            print("-" * 30)
            
            for i, line in enumerate(lines[:25]):  # First 25 lines
                line_clean = line.strip()
                if line_clean:
                    print(f"{i+1:2d}: {line_clean}")
            
            if len(lines) > 25:
                print(f"... and {len(lines) - 25} more lines")
            
            # Look for MDRM patterns
            mdrm_patterns = [
                r'\b([A-Z]{3,5}\d{3,4})\b',
                r'\b(CLCO[A-Z0-9]{4})\b',
                r'\b(BHCK\d{4})\b',
                r'\b(CAC[A-Z]\d{4})\b',
                r'\b(M\d{3})\b',
            ]
            
            print(f"\n🔍 MDRM CODE ANALYSIS:")
            print("-" * 30)
            
            all_mdrm_found = set()
            for pattern in mdrm_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    pattern_matches = list(set(matches))
                    print(f"Pattern {pattern}: {len(pattern_matches)} unique codes")
                    print(f"  Examples: {pattern_matches[:5]}")
                    all_mdrm_found.update(pattern_matches)
            
            print(f"Total unique MDRM codes found: {len(all_mdrm_found)}")
            if all_mdrm_found:
                print(f"Sample codes: {list(all_mdrm_found)[:10]}")
            
            # Look for field number patterns
            print(f"\n🔢 FIELD NUMBER PATTERNS:")
            print("-" * 30)
            
            field_patterns = [
                r'^\s*(\d+)\s+([A-Za-z][^0-9]{5,})',  # Number + text
                r'^\s*(\d+)\.\s*([A-Za-z][^0-9]{5,})', # Number. + text
                r'Field\s+(\d+)\s+([A-Za-z][^0-9]{5,})', # Field Number + text
            ]
            
            for pattern in field_patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                if matches:
                    print(f"Pattern '{pattern}': {len(matches)} matches")
                    for match in matches[:3]:  # Show first 3
                        print(f"  {match[0]}: {match[1][:50]}...")
            
            # Analyze table structure
            print(f"\n📊 TABLE STRUCTURE ANALYSIS:")
            print("-" * 30)
            
            tables = page.extract_tables()
            print(f"Tables found: {len(tables)}")
            
            for table_idx, table in enumerate(tables):
                if table:
                    print(f"  Table {table_idx + 1}: {len(table)} rows, {len(table[0]) if table[0] else 0} columns")
                    if table and table[0]:
                        print(f"    Header row: {[str(cell)[:20] + '...' if cell and len(str(cell)) > 20 else str(cell) for cell in table[0]]}")
                    if len(table) > 1 and table[1]:
                        print(f"    Sample row: {[str(cell)[:20] + '...' if cell and len(str(cell)) > 20 else str(cell) for cell in table[1]]}")
            
            # Look for specific content patterns
            print(f"\n🎯 CONTENT PATTERN ANALYSIS:")
            print("-" * 30)
            
            # Check for field definition patterns
            if "Field Name" in text and "MDRM" in text:
                print("✅ Found 'Field Name' and 'MDRM' - likely field definition page")
            
            if re.search(r'Field\s*\d+', text):
                field_matches = re.findall(r'Field\s*(\d+)', text)
                print(f"✅ Found {len(field_matches)} 'Field N' references: {field_matches[:5]}")
            
            if "Technical Field Name" in text:
                print("✅ Found 'Technical Field Name' - detailed field definition format")
            
            # Look for specific schedule content
            schedule_indicators = [
                "Schedule H.1", "Schedule H.2", "Corporate Loan", "CRE", "Commercial Real Estate"
            ]
            
            found_indicators = []
            for indicator in schedule_indicators:
                if indicator in text:
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"✅ Schedule indicators found: {found_indicators}")
            
            # Character encoding analysis
            print(f"\n📝 TEXT ENCODING ANALYSIS:")
            print("-" * 30)
            
            # Look for special characters that might cause parsing issues
            special_chars = set()
            for char in text:
                if ord(char) > 127:  # Non-ASCII
                    special_chars.add(char)
            
            if special_chars:
                print(f"Non-ASCII characters found: {len(special_chars)}")
                print(f"Examples: {list(special_chars)[:10]}")
            else:
                print("✅ All ASCII characters - no encoding issues")
            
            # Look for pipe characters or other delimiters
            delimiters = ['|', '\t', '  ', '   ']
            for delim in delimiters:
                count = text.count(delim)
                if count > 10:  # Threshold for likely delimiter
                    print(f"Potential delimiter '{repr(delim)}': {count} occurrences")

if __name__ == "__main__":
    debug_14Q_content() 