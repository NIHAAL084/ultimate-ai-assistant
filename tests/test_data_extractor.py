#!/usr/bin/env python3
"""
Test script for data extraction functions
Tests with test.docx and resume.pdf files
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.assistant.utils.data_extractor import extract_universal_pdf_data, extract_docx_data

def test_pdf_extraction():
    """Test PDF extraction with resume.pdf"""
    print("=" * 60)
    print("TESTING PDF EXTRACTION")
    print("=" * 60)
    
    pdf_path = "/Users/nihaalanupoju/Documents/resume.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    try:
        print(f"📄 Extracting data from: {pdf_path}")
        pdf_data = extract_universal_pdf_data(pdf_path)
        
        print(f"\n✅ Successfully extracted data from {len(pdf_data)} pages")
        
        for i, page_data in enumerate(pdf_data, 1):
            print(f"\n--- PAGE {i} ---")
            print(f"Page Number: {page_data['page_number']}")
            text = page_data['text']
            if text:
                print(f"Text Length: {len(text)} characters")
                # Show first 200 characters
                preview = text[:200].replace('\n', ' ').strip()
                print(f"Text Preview: {preview}...")
            else:
                print("Text: No text extracted")
            
            tables = page_data['tables']
            if tables:
                print(f"Tables Found: {len(tables)}")
                for j, table in enumerate(tables, 1):
                    print(f"  Table {j}: {len(table)} rows x {len(table[0]) if table else 0} columns")
            else:
                print("Tables: None found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting PDF data: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_docx_extraction():
    """Test DOCX extraction with test.docx"""
    print("\n" + "=" * 60)
    print("TESTING DOCX EXTRACTION")
    print("=" * 60)
    
    docx_path = "/Users/nihaalanupoju/Documents/test.docx"
    
    if not os.path.exists(docx_path):
        print(f"❌ File not found: {docx_path}")
        return False
    
    try:
        print(f"📄 Extracting data from: {docx_path}")
        docx_data = extract_docx_data(docx_path)
        
        print("✅ Successfully extracted DOCX data")
        
        text = docx_data['text']
        if text:
            print(f"\nText Length: {len(text)} characters")
            # Show first 300 characters
            preview = text[:300].replace('\n', ' ').strip()
            print(f"Text Preview: {preview}...")
        else:
            print("\nText: No text found")
        
        tables = docx_data['tables']
        if tables:
            print(f"\nTables Found: {len(tables)}")
            for i, table in enumerate(tables, 1):
                print(f"  Table {i}: {len(table)} rows")
                if table:
                    print(f"    Columns: {len(table[0])}")
                    # Show first few cells of first row
                    if table[0]:
                        first_row_preview = " | ".join(table[0][:3])
                        print(f"    First Row Preview: {first_row_preview}")
        else:
            print("\nTables: None found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting DOCX data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Data Extraction Tests")
    
    pdf_success = test_pdf_extraction()
    docx_success = test_docx_extraction()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"PDF Extraction: {'✅ PASSED' if pdf_success else '❌ FAILED'}")
    print(f"DOCX Extraction: {'✅ PASSED' if docx_success else '❌ FAILED'}")
    
    if pdf_success and docx_success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed!")

if __name__ == "__main__":
    main()
