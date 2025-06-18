#!/usr/bin/env python3
"""
Clean and validate iperf3 JSON files
Fixes common JSON formatting issues and validates structure
"""

import json
import argparse
import re
import os
import glob
from pathlib import Path

DATA_DIR = "/home/ming/E2E-network-measurement/data/20250530-NFAPI-SingleMachine(100-800M)"

def is_error_block(obj):
    return (
        isinstance(obj, dict)
        and obj.get("error") == "interrupt - the server has terminated"
        and obj.get("intervals", []) == []
    )

def clean_json_file(filepath):
    with open(filepath, "r") as f:
        content = f.read().strip()
    # 嘗試處理多個 JSON 物件的情況
    json_objs = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(content):
        content = content.lstrip()
        try:
            obj, end = decoder.raw_decode(content)
            json_objs.append(obj)
            content = content[end:]
            idx = 0
        except json.JSONDecodeError:
            break
    # 過濾掉 error block
    cleaned_objs = [obj for obj in json_objs if not is_error_block(obj)]
    # 只保留第一個合法物件（通常只需要一個）
    if cleaned_objs:
        with open(filepath, "w") as f:
            json.dump(cleaned_objs[0], f, indent=4)
        print(f"Cleaned: {filepath}")
    else:
        print(f"Warning: No valid JSON object found in {filepath}")

def clean_json_content(content):
    """Clean JSON content by fixing common issues"""
    # Remove any non-JSON content before the actual JSON
    content = content.strip()
    
    # Find the start of JSON (first '{')
    start_idx = content.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in content")
    
    # Find the end of JSON (last '}')
    end_idx = content.rfind('}')
    if end_idx == -1:
        raise ValueError("No complete JSON object found in content")
    
    # Extract JSON portion
    json_content = content[start_idx:end_idx+1]
    
    # Fix common JSON issues
    # Remove trailing commas
    json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
    
    # Fix single quotes to double quotes
    json_content = re.sub(r"'([^']*)':", r'"\1":', json_content)
    
    return json_content

def validate_iperf_json(data):
    """Validate iperf3 JSON structure"""
    required_fields = ['start', 'intervals', 'end']
    
    for field in required_fields:
        if field not in data:
            print(f"Warning: Missing required field '{field}'")
    
    # Check intervals structure
    if 'intervals' in data:
        interval_count = len(data['intervals'])
        print(f"Found {interval_count} intervals")
        
        if interval_count > 0:
            # Check first interval structure
            first_interval = data['intervals'][0]
            if 'streams' in first_interval:
                stream_count = len(first_interval['streams'])
                print(f"Found {stream_count} streams per interval")
    
    # Check end summary
    if 'end' in data:
        end_data = data['end']
        if 'sum' in end_data:
            print("Found end summary data")
        if 'sum_sent' in end_data:
            print("Found sender summary data")
        if 'sum_received' in end_data:
            print("Found receiver summary data")
    
    return True

def clean_iperf_json_file(input_file, output_file=None):
    """Clean a single iperf3 JSON file"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Read original file
    with open(input_path, 'r') as f:
        content = f.read()
    
    print(f"Processing file: {input_path}")
    print(f"Original file size: {len(content)} bytes")
    
    # Clean content
    try:
        cleaned_content = clean_json_content(content)
        
        # Parse JSON to validate
        data = json.loads(cleaned_content)
        
        # Validate structure
        validate_iperf_json(data)
        
        # Determine output file
        if output_file is None:
            output_file = input_path.with_suffix('.cleaned.json')
        else:
            output_file = Path(output_file)
        
        # Write cleaned file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Cleaned file saved to: {output_file}")
        print(f"Cleaned file size: {output_file.stat().st_size} bytes")
        
        return output_file
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        raise
    except Exception as e:
        print(f"Error cleaning file: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Clean and validate iperf3 JSON files')
    parser.add_argument('input_file', help='Input iperf3 JSON file')
    parser.add_argument('-o', '--output', help='Output file (default: input_file.cleaned.json)')
    parser.add_argument('-v', '--validate-only', action='store_true',
                       help='Only validate, do not create cleaned file')
    
    args = parser.parse_args()
    
    try:
        if args.validate_only:
            # Just validate the file
            with open(args.input_file, 'r') as f:
                content = f.read()
            
            cleaned_content = clean_json_content(content)
            data = json.loads(cleaned_content)
            validate_iperf_json(data)
            print("File validation completed successfully")
        else:
            # Clean and save the file
            output_file = clean_iperf_json_file(args.input_file, args.output)
            print(f"File cleaning completed successfully: {output_file}")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    for filepath in files:
        clean_json_file(filepath)
    exit(main())
