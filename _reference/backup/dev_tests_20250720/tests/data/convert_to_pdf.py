#!/usr/bin/env python3
"""Convert HTML credit card statements to PDF using Playwright"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

def convert_html_to_pdf(html_file, pdf_file):
    """Convert HTML file to PDF using Playwright"""
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Load the HTML file
        file_path = Path(html_file).absolute()
        page.goto(f'file://{file_path}')
        
        # Generate PDF with proper formatting
        page.pdf(
            path=pdf_file,
            format='Letter',
            print_background=True,
            margin={
                'top': '0.5in',
                'right': '0.5in',
                'bottom': '0.5in',
                'left': '0.5in'
            }
        )
        
        browser.close()
        print(f"✓ Converted {html_file} to {pdf_file}")

def main():
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Convert both credit card statements
    html_files = [
        ('credit_card_statement_1.html', 'credit_card_statement_1.pdf'),
        ('credit_card_statement_2.html', 'credit_card_statement_2.pdf')
    ]
    
    for html_file, pdf_file in html_files:
        html_path = current_dir / html_file
        pdf_path = current_dir / pdf_file
        
        if html_path.exists():
            try:
                convert_html_to_pdf(str(html_path), str(pdf_path))
            except Exception as e:
                print(f"✗ Error converting {html_file}: {str(e)}")
        else:
            print(f"✗ HTML file not found: {html_file}")

if __name__ == "__main__":
    main()