#!/usr/bin/env python3

import pdfplumber
import re
from collections import OrderedDict

def outline_14Q_schedules():
    pdf_path = "_reference/regulations/14Q/FR_Y-14Q20240331_i.pdf"
    
    print("Outlining FR Y-14Q Schedules and Sub-schedules...")
    print("="*70)
    
    schedules_found = OrderedDict()
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        # Focus on table of contents and early pages where schedules are outlined
        for page_num in range(min(15, len(pdf.pages))):  # First 15 pages
            page = pdf.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                line_stripped = line.strip()
                
                # Look for main schedule patterns
                main_schedule_patterns = [
                    r'Schedule\s+([A-L])\s*[–-]\s*(.+?)(?:\s*\.{3,}|\s*\d+$|$)',
                    r'Schedule\s+([A-L])—(.+?)(?:\s*\.{3,}|\s*\d+$|$)',
                    r'Schedule\s+([A-L])\s*[–-]\s*(.+)'
                ]
                
                for pattern in main_schedule_patterns:
                    match = re.search(pattern, line_stripped, re.IGNORECASE)
                    if match:
                        schedule_id = match.group(1).upper()
                        schedule_name = match.group(2).strip()
                        
                        # Clean up schedule name
                        schedule_name = re.sub(r'\s*\.{3,}.*$', '', schedule_name)
                        schedule_name = re.sub(r'\s*\d+\s*$', '', schedule_name)
                        
                        if schedule_id not in schedules_found:
                            schedules_found[schedule_id] = {
                                'name': schedule_name,
                                'sub_schedules': []
                            }
                
                # Look for sub-schedule patterns
                sub_schedule_patterns = [
                    r'([A-L]\.\d+)\s*[–-]\s*(.+?)(?:\s*\.{3,}|\s*\d+$|$)',
                    r'([A-L]\.\d+)—(.+?)(?:\s*\.{3,}|\s*\d+$|$)',
                    r'([A-L]\.\d+)\s*[–-]\s*(.+)'
                ]
                
                for pattern in sub_schedule_patterns:
                    match = re.search(pattern, line_stripped, re.IGNORECASE)
                    if match:
                        sub_schedule_id = match.group(1).upper()
                        sub_schedule_name = match.group(2).strip()
                        
                        # Clean up sub-schedule name
                        sub_schedule_name = re.sub(r'\s*\.{3,}.*$', '', sub_schedule_name)
                        sub_schedule_name = re.sub(r'\s*\d+\s*$', '', sub_schedule_name)
                        
                        # Get the main schedule letter
                        main_schedule = sub_schedule_id[0]
                        
                        if main_schedule in schedules_found:
                            # Check if sub-schedule already exists
                            existing_subs = [s['id'] for s in schedules_found[main_schedule]['sub_schedules']]
                            if sub_schedule_id not in existing_subs:
                                schedules_found[main_schedule]['sub_schedules'].append({
                                    'id': sub_schedule_id,
                                    'name': sub_schedule_name
                                })
        
        # Also search later pages for additional schedule information
        sample_pages = [20, 30, 50, 70, 100]
        for page_num in sample_pages:
            if page_num >= len(pdf.pages):
                continue
                
            page = pdf.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
            
            # Look for schedule headers in content pages
            lines = text.split('\n')
            for line in lines:
                # More flexible patterns for content pages
                content_patterns = [
                    r'^([A-L]\.\d+)\s*[–-]\s*(.+)',
                    r'Schedule\s+([A-L])\s*[–-]\s*(.+)',
                ]
                
                for pattern in content_patterns:
                    match = re.search(pattern, line.strip(), re.IGNORECASE)
                    if match:
                        if '.' in match.group(1):  # Sub-schedule
                            sub_id = match.group(1).upper()
                            sub_name = match.group(2).strip()
                            main_schedule = sub_id[0]
                            
                            if main_schedule in schedules_found:
                                existing_subs = [s['id'] for s in schedules_found[main_schedule]['sub_schedules']]
                                if sub_id not in existing_subs and len(sub_name) > 5:
                                    schedules_found[main_schedule]['sub_schedules'].append({
                                        'id': sub_id,
                                        'name': sub_name[:50] + '...' if len(sub_name) > 50 else sub_name
                                    })
    
    # Print the organized schedule outline
    print("\nFR Y-14Q SCHEDULE OUTLINE:")
    print("="*70)
    
    total_schedules = 0
    total_sub_schedules = 0
    
    for schedule_id in sorted(schedules_found.keys()):
        schedule = schedules_found[schedule_id]
        total_schedules += 1
        
        print(f"\n📋 Schedule {schedule_id}: {schedule['name']}")
        print("-" * (len(f"Schedule {schedule_id}: {schedule['name']}") + 2))
        
        if schedule['sub_schedules']:
            for sub in sorted(schedule['sub_schedules'], key=lambda x: x['id']):
                total_sub_schedules += 1
                print(f"   └── {sub['id']}: {sub['name']}")
        else:
            print("   └── (No sub-schedules detected)")
    
    print("\n" + "="*70)
    print("SUMMARY:")
    print(f"📊 Total Main Schedules: {total_schedules}")
    print(f"📋 Total Sub-schedules: {total_sub_schedules}")
    print(f"📑 Total Schedule Items: {total_schedules + total_sub_schedules}")
    
    # Return the structured data for the extractor
    return schedules_found

if __name__ == "__main__":
    schedule_structure = outline_14Q_schedules() 