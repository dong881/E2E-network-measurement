#!/usr/bin/env python3
"""
Clean and validate iperf3 JSON files analysis
Fixes common JSON formatting issues and validates structure
"""

import json
import re
import os
import glob
from pathlib import Path
import sys

def is_error_block(obj):
    """Check if JSON object is an error block that should be filtered"""
    return (
        isinstance(obj, dict)
        and obj.get("error") == "interrupt - the server has terminated"
        and obj.get("intervals", []) == []
    )

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

def clean_json_file(filepath):
    """Clean a single JSON file with multiple JSON objects handling"""
    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
        
        if not content:
            print(f"⚠️ Empty file: {filepath}")
            return False
        
        # Try to handle multiple JSON objects
        json_objs = []
        decoder = json.JSONDecoder()
        idx = 0
        content_to_parse = content
        
        while idx < len(content_to_parse):
            content_to_parse = content_to_parse.lstrip()
            if not content_to_parse:
                break
                
            try:
                obj, end = decoder.raw_decode(content_to_parse)
                json_objs.append(obj)
                content_to_parse = content_to_parse[end:]
                idx = 0
            except json.JSONDecodeError:
                # If multiple object parsing fails, try single object cleaning
                try:
                    cleaned_content = clean_json_content(content)
                    obj = json.loads(cleaned_content)
                    json_objs = [obj]
                    break
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"❌ Failed to parse {filepath}: {e}")
                    return False
        
        # Filter out error blocks
        cleaned_objs = [obj for obj in json_objs if not is_error_block(obj)]
        
        if cleaned_objs:
            # Keep only the first valid object (usually only need one)
            with open(filepath, "w") as f:
                json.dump(cleaned_objs[0], f, indent=2)
            print(f"✅ Cleaned: {filepath.name}")
            return True
        else:
            print(f"⚠️ No valid JSON object found in {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False

def validate_iperf_json(data, filename):
    """Validate iperf3 JSON structure and report issues"""
    issues = []
    
    # Check required fields
    required_fields = ['start', 'intervals', 'end']
    for field in required_fields:
        if field not in data:
            issues.append(f"Missing required field '{field}'")
    
    # Check intervals structure
    if 'intervals' in data:
        interval_count = len(data['intervals'])
        if interval_count == 0:
            issues.append("No intervals found")
        else:
            # Check first interval structure
            first_interval = data['intervals'][0]
            if 'streams' not in first_interval:
                issues.append("Missing 'streams' in intervals")
    
    # Check end summary
    if 'end' in data:
        end_data = data['end']
        has_summary = any(key in end_data for key in ['sum', 'sum_sent', 'sum_received'])
        if not has_summary:
            issues.append("Missing end summary data")
    
    if issues:
        print(f"⚠️ Validation issues in {filename}: {', '.join(issues)}")
        return False
    else:
        print(f"✅ Validation passed: {filename}")
        return True

def clean_iperf_json_analysis(data_dir=None):
    """Main function to clean and validate iperf3 JSON files in a directory"""
    if data_dir is None:
        from data_selector import get_data_folder_interactive
        data_dir = get_data_folder_interactive()
        if not data_dir:
            return
    else:
        data_dir = Path(data_dir)
    
    # Check for centralized output directory
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        output_dir = Path(os.environ['CENTRALIZED_OUTPUT_DIR'])
        log_file = None
        log_handle = None
    else:
        from data_selector import get_analysis_output_dir, setup_logging, redirect_output_to_log
        output_dir = get_analysis_output_dir(data_dir)
        log_file = setup_logging(output_dir, "json_cleaning")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🧹 Cleaning and validating iperf3 JSON files in: {data_dir}")
    
    # Find all JSON files
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found in the directory")
        return
    
    print(f"📁 Found {len(json_files)} JSON files to process")
    
    cleaned_count = 0
    validated_count = 0
    failed_count = 0
    
    print("\n🔄 Processing JSON files:")
    print("-" * 60)
    
    for json_file in sorted(json_files):
        print(f"📄 Processing: {json_file.name}")
        
        # Clean the file
        if clean_json_file(json_file):
            cleaned_count += 1
            
            # Validate the cleaned file
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                if validate_iperf_json(data, json_file.name):
                    validated_count += 1
                    
            except Exception as e:
                print(f"❌ Validation error for {json_file.name}: {e}")
                failed_count += 1
        else:
            failed_count += 1
        
        print()  # Add spacing between files
    
    # Summary report
    print("=" * 80)
    print(f"🧹 JSON Cleaning and Validation Summary")
    print("=" * 80)
    print(f"📁 Total files processed: {len(json_files)}")
    print(f"✅ Successfully cleaned: {cleaned_count}")
    print(f"✅ Successfully validated: {validated_count}")
    print(f"❌ Failed to process: {failed_count}")
    
    if cleaned_count > 0:
        print(f"💾 All cleaned files are saved in-place in: {data_dir}")
    
    # Create summary report file
    try:
        summary_file = output_dir / 'json_cleaning_summary.txt'
        with open(summary_file, 'w') as f:
            f.write(f"JSON Cleaning and Validation Summary\n")
            f.write(f"Generated: {Path(__file__).name}\n")
            f.write(f"Data Directory: {data_dir}\n")
            f.write(f"="*50 + "\n")
            f.write(f"Total files processed: {len(json_files)}\n")
            f.write(f"Successfully cleaned: {cleaned_count}\n")
            f.write(f"Successfully validated: {validated_count}\n")
            f.write(f"Failed to process: {failed_count}\n")
            f.write(f"="*50 + "\n")
            
            f.write(f"\nProcessed files:\n")
            for json_file in sorted(json_files):
                f.write(f"  - {json_file.name}\n")
        
        print(f"📋 Summary report saved to: {summary_file}")
        
    except Exception as e:
        print(f"⚠️ Could not save summary report: {e}")
    
    print("=" * 80)
    
    if log_file:
        print(f"📝 Detailed logs saved to: {log_file}")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        clean_iperf_json_analysis(sys.argv[1])
    else:
        clean_iperf_json_analysis()
