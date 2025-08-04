#!/usr/bin/env python3

import pdfplumber
import re

def search_14Q_specific():
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    
    print("Searching for specific content patterns in FR Y-14Q PDF...")
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        # Sample specific pages to understand structure
        sample_pages = [20, 30, 50, 70, 100, 150, 200, 250, 300]
        
        for page_num in sample_pages:
            if page_num >= len(pdf.pages):
                continue
                
            page = pdf.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
            
            print(f"\n=== PAGE {page_num + 1} SAMPLE ===")
            
            # Show first 20 lines to understand content
            lines = text.split('\n')
            for i, line in enumerate(lines[:20]):
                if line.strip():
                    print(f"{i+1:2d}: {line.strip()}")
            
            # Look for any MDRM patterns
            mdrm_pattern = r'\b(M\d{3}|N\d{3}|R\d{3}|S\d{3}|JA\d{2}|PG\d{2}|LE\d{2}|\d{4})\b'
            matches = list(re.finditer(mdrm_pattern, text))
            if matches:
                print(f"MDRM codes found: {[m.group() for m in matches[:3]]}")
            
            # Look for table headers or structures
            table_keywords = [
                'Summary Variable', 'Line Item', 'Variable Name', 'MDRM',
                'Item Name', 'Description', 'Format', 'Data Element'
            ]
            
            found_keywords = []
            for keyword in table_keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
            
            if found_keywords:
                print(f"Table keywords found: {found_keywords}")
            
            print("-" * 50)

if __name__ == "__main__":
    search_14Q_specific() 