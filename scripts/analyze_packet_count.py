import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re
import sys
import os
from matplotlib.ticker import FuncFormatter

def load_json_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def extract_packet_data(data):
    """Extract packet count data from iperf3 JSON"""
    if not data:
        return None
    
    try:
        if 'end' in data and 'sum' in data['end']:
            sum_data = data['end']['sum']
            return {
                'packets': sum_data.get('packets', 0),
                'lost_packets': sum_data.get('lost_packets', 0),
                'received_packets': sum_data.get('packets', 0) - sum_data.get('lost_packets', 0)
            }
    except Exception as e:
        print(f"Error extracting packet data: {e}")
        return None

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration directories"""
    configs = []
    
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
    """Extract mode from folder name"""
    folder_name = Path(folder_path).name
    
    if '-' in folder_name:
        parts = folder_name.split('-')
        if len(parts) >= 2:
            mode_part = parts[1].split('(')[0]
            return mode_part
    return "Unknown Mode"

def format_large_number(num):
    """Format large numbers with appropriate units"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(int(num))

def analyze_packet_count(data_dir=None):
    """Main function to analyze and plot packet count data"""
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
        log_file = setup_logging(output_dir, "packet_count_analysis")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing packet count data from: {data_dir}")
    
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("❌ No bandwidth configurations found in the data directory")
        return
    
    cn_packets = []
    ue_packets = []
    labels = []
    
    print("Processing packet count data:")
    
    for bandwidth_val in bandwidth_configs:
        print(f"📊 Processing {bandwidth_val}M bandwidth...")
        cn_file, ue_file = find_iperf_files(data_dir, bandwidth_val)
        
        cn_data = load_json_data(cn_file) if cn_file else None
        ue_data = load_json_data(ue_file) if ue_file else None
        
        cn_packet_data = extract_packet_data(cn_data)
        ue_packet_data = extract_packet_data(ue_data)
        
        cn_packet_count = cn_packet_data['packets'] if cn_packet_data else 0
        ue_packet_count = ue_packet_data['received_packets'] if ue_packet_data else 0
        
        cn_packets.append(cn_packet_count)
        ue_packets.append(ue_packet_count)
        labels.append(f"{bandwidth_val}M")
    
    # Create packet count comparison plot
    plt.figure(figsize=(16, 10))
    
    x = np.arange(len(labels))
    width = 0.35
    
    bars1 = plt.bar(x - width/2, cn_packets, width, label='CN Transmission', 
                   color='#C85A90', alpha=0.8, edgecolor='black', linewidth=1)
    bars2 = plt.bar(x + width/2, ue_packets, width, label='UE Reception', 
                   color='#5BA3C7', alpha=0.8, edgecolor='black', linewidth=1)
    
    # Add value labels with smart positioning and formatting
    max_packets = max(max(cn_packets), max(ue_packets))
    label_spacing = max_packets * 0.015  # Increased spacing to 1.5%
    
    for i, (cn_val, ue_val) in enumerate(zip(cn_packets, ue_packets)):
        # CN labels - positioned above bars with formatted numbers
        if cn_val > 0:
            # Offset CN labels slightly to the left to avoid overlap
            plt.text(i - width/2 - 0.05, cn_val + label_spacing, 
                    format_large_number(cn_val), 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                             edgecolor='#C85A90', alpha=0.9),
                    rotation=0)
        
        # UE labels - positioned above bars with formatted numbers
        if ue_val > 0:
            # Offset UE labels slightly to the right to avoid overlap
            plt.text(i + width/2 + 0.05, ue_val + label_spacing, 
                    format_large_number(ue_val), 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                             edgecolor='#5BA3C7', alpha=0.9),
                    rotation=0)
    plt.xlabel('Bandwidth Configuration', fontsize=14, fontweight='bold')
    plt.ylabel('Packet Count', fontsize=14, fontweight='bold')
    plt.title(f'Network Packet Count Analysis - {mode} Mode\nCN Transmission vs UE Reception Comparison', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xticks(x, labels)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Format y-axis with appropriate units using FuncFormatter
    ax = plt.gca()
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: format_large_number(x)))
    
    plt.tight_layout()
    output_file = output_dir / 'packet_count_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    print(f"✅ Packet count analysis complete! Plot saved to {output_file}")
    if log_file:
        print(f"📋 Log file saved to: {log_file}")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_packet_count(sys.argv[1])
    else:
        analyze_packet_count()