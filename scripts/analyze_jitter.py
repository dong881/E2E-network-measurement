from pathlib import Path
import json
import matplotlib.pyplot as plt
import numpy as np
import re
import sys
import os

def load_json_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def extract_ue_jitter(data):
    """Extract UE (receiver) jitter data from iperf3 JSON"""
    if not data:
        return 0
    
    try:
        if 'end' in data and 'streams' in data['end']:
            for stream in data['end']['streams']:
                if 'udp' in stream and 'jitter_ms' in stream['udp']:
                    return stream['udp']['jitter_ms']
        return 0
    except Exception as e:
        print(f"Error extracting jitter: {e}")
        return 0

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration directories"""
    configs = []
    
    # Look for files with bandwidth patterns
    for file_path in data_dir.glob('iperf*-*M-*.json'):
        match = re.search(r'-(\d+)M-', file_path.name)
        if match:
            bandwidth_val = int(match.group(1))
            configs.append(bandwidth_val)
    
    return sorted(list(set(configs)))

def find_iperf_files(data_dir, bandwidth_val):
    """Find CN and UE iperf files for a specific bandwidth"""
    cn_file = None
    ue_file = None
    
    # Look for files matching the pattern
    cn_pattern = f"iperf*-{bandwidth_val}M-CN.json"
    ue_pattern = f"iperf*-{bandwidth_val}M-UE.json"
    
    for file_path in data_dir.glob(cn_pattern):
        cn_file = file_path
        break
    
    for file_path in data_dir.glob(ue_pattern):
        ue_file = file_path
        break
    
    return cn_file, ue_file

def extract_mode_from_folder(folder_path):
    """Extract mode from folder name - simplified and reliable"""
    folder_name = Path(folder_path).name
    
    # Handle date prefix pattern: YYYYMMDD-MODE
    if len(folder_name) > 8 and folder_name[8:9] == '-':
        folder_name = folder_name[9:]
    
    # Extract mode before parentheses or first part
    if '(' in folder_name:
        mode = folder_name.split('(')[0].strip().rstrip('-')
    else:
        mode = folder_name.split('-')[0] if '-' in folder_name else folder_name
    
    return mode.strip() if mode.strip() else "Unknown"

def analyze_jitter(data_dir=None):
    """Main function to analyze and plot jitter data"""
    # Use provided data_dir or interactive selection
    if data_dir is None:
        from data_selector import get_data_folder_interactive, setup_logging, redirect_output_to_log, get_analysis_output_dir
        data_dir = get_data_folder_interactive()
        if not data_dir:
            return
    else:
        data_dir = Path(data_dir)
    
    # Extract mode from data directory
    mode = extract_mode_from_folder(data_dir)
    
    # Check for centralized output directory
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        output_dir = Path(os.environ['CENTRALIZED_OUTPUT_DIR'])
        log_file = None
        log_handle = None
    else:
        from data_selector import get_analysis_output_dir, setup_logging, redirect_output_to_log
        analysis_base_dir = get_analysis_output_dir(data_dir)
        output_dir = analysis_base_dir
        log_file = setup_logging(output_dir, "jitter_analysis")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing jitter data from: {data_dir}")
    
    # Get all bandwidth configurations
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("❌ No bandwidth configurations found in the data directory")
        return
    
    ue_jitter_values = []
    labels = []
    
    print("Processing jitter data:")
    
    for bandwidth_val in bandwidth_configs:
        print(f"📊 Processing {bandwidth_val}M bandwidth...")
        cn_file, ue_file = find_iperf_files(data_dir, bandwidth_val)
        
        ue_data = load_json_data(ue_file) if ue_file else None
        ue_jitter = extract_ue_jitter(ue_data)
        
        ue_jitter_values.append(ue_jitter)
        labels.append(f"{bandwidth_val}M")
        print(f"  📈 UE Jitter: {ue_jitter:.3f}ms")
    
    # Create jitter analysis plot with professional colors
    plt.figure(figsize=(14, 9))
    
    # Professional color scheme - consistent with enhanced theme
    colors = []
    for jitter in ue_jitter_values:
        if jitter <= 1:
            colors.append('#1B5E20')  # Professional Dark Green - Excellent
        elif jitter <= 3:
            colors.append('#2E7D32')  # Professional Green - Good
        elif jitter <= 5:
            colors.append('#F57F17')  # Professional Amber - Fair
        elif jitter <= 10:
            colors.append('#EF6C00')  # Professional Orange - Poor
        else:
            colors.append('#C62828')  # Professional Red - Very Poor
    
    bars = plt.bar(labels, ue_jitter_values, color=colors, alpha=0.85, 
                   edgecolor='#263238', linewidth=1.2, width=0.6)
    
    # Enhanced value labels with professional background styling
    for bar, jitter in zip(bars, ue_jitter_values):
        label_y = bar.get_height() + max(ue_jitter_values) * 0.02
        plt.text(bar.get_x() + bar.get_width()/2, label_y,
                f'{jitter:.2f}ms', ha='center', va='bottom', 
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                         edgecolor=bar.get_facecolor(), alpha=0.9, linewidth=1.5))
    
    # Customize the plot with enhanced styling
    plt.xlabel('Bandwidth Configuration', fontsize=14, fontweight='bold', color='#263238')
    plt.ylabel('Jitter (ms)', fontsize=14, fontweight='bold', color='#263238')
    plt.title(f'UE Network Jitter Quality Analysis - {mode} Mode\nColor-coded by Performance Level', 
              fontsize=16, fontweight='bold', color='#1A237E', pad=25)
    
    # Create custom legend
    legend_elements = [
        plt.Rectangle((0,0),1,1, facecolor='#1B5E20', label='Excellent (≤1ms)'),
        plt.Rectangle((0,0),1,1, facecolor='#2E7D32', label='Good (1-3ms)'),
        plt.Rectangle((0,0),1,1, facecolor='#F57F17', label='Fair (3-5ms)'),
        plt.Rectangle((0,0),1,1, facecolor='#EF6C00', label='Poor (5-10ms)'),
        plt.Rectangle((0,0),1,1, facecolor='#C62828', label='Very Poor (>10ms)')
    ]
    
    plt.legend(handles=legend_elements, loc='upper right', fontsize=10, 
               title='Jitter Quality Levels', title_fontsize=11)
    
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    output_file = output_dir / 'ue_jitter_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    print(f"✅ Jitter analysis complete! Plot saved to {output_file}")
    if log_file:
        print(f"📋 Log file saved to: {log_file}")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_jitter(sys.argv[1])
    else:
        analyze_jitter()
