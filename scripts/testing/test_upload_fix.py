#!/usr/bin/env python3

import sys
sys.path.append('.')
from app.api.v1.endpoints.request_info import _determine_document_type

def test_document_type_mapping():
    """Test that document type mapping returns correct database enum values"""
    
    print("Testing document type mapping...")
    
    # Test PDF files
    pdf_type = _determine_document_type("sample_document.pdf", "application/pdf")
    print(f"PDF file -> {pdf_type}")
    assert pdf_type == "Source Document", f"Expected 'Source Document', got '{pdf_type}'"
    
    # Test image files
    img_type = _determine_document_type("screenshot.png", "image/png")
    print(f"PNG file -> {img_type}")
    assert img_type == "Supporting Evidence", f"Expected 'Supporting Evidence', got '{img_type}'"
    
    # Test Excel files
    excel_type = _determine_document_type("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    print(f"Excel file -> {excel_type}")
    assert excel_type == "Data Extract", f"Expected 'Data Extract', got '{excel_type}'"
    
    # Test Word files
    word_type = _determine_document_type("report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    print(f"Word file -> {word_type}")
    assert word_type == "Supporting Evidence", f"Expected 'Supporting Evidence', got '{word_type}'"
    
    # Test unknown files
    other_type = _determine_document_type("unknown.xyz", "application/octet-stream")
    print(f"Unknown file -> {other_type}")
    assert other_type == "Other", f"Expected 'Other', got '{other_type}'"
    
    print("✅ All document type mappings are correct!")

if __name__ == "__main__":
    test_document_type_mapping() 