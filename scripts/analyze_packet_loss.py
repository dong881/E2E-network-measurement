import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
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

def extract_ue_loss_rate(data):
    """Extract UE (receiver) loss rate from iperf3 JSON"""
    if not data:
        return None
    
    try:
        # Primary source: sum_received.lost_percent
        if 'end' in data and 'sum_received' in data['end']:
            return data['end']['sum_received'].get('lost_percent', 0)
        
        # Fallback: sum.lost_percent
        if 'end' in data and 'sum' in data['end']:
            return data['end']['sum'].get('lost_percent', 0)
        
        return 0
        
    except Exception as e:
        print(f"Error extracting UE loss rate: {e}")
        return 0

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration directories"""
    configs = []
    
    for file_path in data_dir.glob('iperf*-*M-UE.json'):
        match = re.search(r'-(\d+)M-', file_path.name)
        if match:
            bandwidth_val = int(match.group(1))
            configs.append(bandwidth_val)
    
    return sorted(list(set(configs)))

def find_ue_iperf_files(data_dir, bandwidth_val):
    """Find UE iperf files for a specific bandwidth"""
    ue_pattern = f"iperf*-{bandwidth_val}M-UE.json"
    
    for file_path in data_dir.glob(ue_pattern):
        return file_path
    
    return None

def get_loss_rate_color(loss_rate):
    """Get color based on loss rate (Green for good, Red for bad)"""
    if loss_rate == 0:
        return '#2E8B57'  # Sea Green (Best)
    elif loss_rate <= 0.1:
        return '#32CD32'  # Lime Green  
    elif loss_rate <= 0.5:
        return '#FFD700'  # Gold
    elif loss_rate <= 1.0:
        return '#FF8C00'  # Dark Orange
    elif loss_rate <= 3.0:
        return '#FF4500'  # Orange Red
    else:
        return '#DC143C'  # Crimson (Worst)

def extract_mode_from_folder(folder_path):
    """Extract mode from folder name"""
    folder_name = Path(folder_path).name
    
    if '-' in folder_name:
        parts = folder_name.split('-')
        if len(parts) >= 2:
            mode_part = parts[1].split('(')[0]
            return mode_part
    return "Unknown Mode"

def analyze_packet_loss(data_dir=None):
    """Main function to analyze and plot UE packet loss data"""
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
        log_file = setup_logging(output_dir, "packet_loss_analysis")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing UE packet loss data from: {data_dir}")
    
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("❌ No UE iperf files found in the data directory")
        return
    
    ue_loss_rates = []
    labels = []
    colors = []
    
    print("Processing UE packet loss data:")
    
    for bandwidth_val in bandwidth_configs:
        print(f"📊 Processing {bandwidth_val}M bandwidth...")
        ue_file = find_ue_iperf_files(data_dir, bandwidth_val)
        
        if ue_file:
            ue_data = load_json_data(ue_file)
            loss_rate = extract_ue_loss_rate(ue_data)
            
            ue_loss_rates.append(loss_rate)
            labels.append(f"{bandwidth_val}M")
            colors.append(get_loss_rate_color(loss_rate))
            
            print(f"  📉 UE Loss Rate: {loss_rate:.3f}%")
    
    if not ue_loss_rates:
        print("❌ No valid UE loss rate data found")
        return
    
    # Create UE packet loss analysis plot
    plt.figure(figsize=(14, 9))
    
    bars = plt.bar(labels, ue_loss_rates, color=colors, alpha=0.85, 
                   edgecolor='#37474F', linewidth=1.5, width=0.7)
    
    # Add value labels with better spacing
    max_loss = max(ue_loss_rates) if ue_loss_rates else 1
    label_height = max_loss * 0.02  # 2% of max value for spacing
    
    for bar, loss_rate in zip(bars, ue_loss_rates):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + label_height,
                f'{loss_rate:.2f}%', ha='center', va='bottom', 
                fontsize=11, fontweight='bold')
    
    # Add trend line
    x_pos = range(len(labels))
    plt.plot(x_pos, ue_loss_rates, 'k-o', linewidth=2, markersize=6, 
             markerfacecolor='white', markeredgewidth=2, alpha=0.8)
    
    plt.xlabel('Bandwidth Configuration', fontsize=14, fontweight='bold')
    plt.ylabel('Packet Loss Rate (%)', fontsize=14, fontweight='bold')
    plt.title(f'UE Network Packet Loss Analysis - {mode} Mode\nReceiver-Side Loss Rate Assessment', 
              fontsize=16, fontweight='bold', pad=25)
    
    # Set y-axis limit to 100%
    plt.ylim(0, 100)
    
    # Create custom legend for loss rate ranges (Natural order)
    legend_elements = [
        plt.Rectangle((0,0),1,1, facecolor='#2E8B57', label='Perfect (0%)'),
        plt.Rectangle((0,0),1,1, facecolor='#32CD32', label='Excellent (≤0.1%)'),
        plt.Rectangle((0,0),1,1, facecolor='#FFD700', label='Very Good (≤0.5%)'),
        plt.Rectangle((0,0),1,1, facecolor='#FF8C00', label='Good (≤1.0%)'),
        plt.Rectangle((0,0),1,1, facecolor='#FF4500', label='Poor (≤3.0%)'),
        plt.Rectangle((0,0),1,1, facecolor='#DC143C', label='Critical (>3.0%)')
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', fontsize=10, 
               title='Loss Rate Ranges', title_fontsize=11, frameon=True, 
               fancybox=True, shadow=True)
    
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    output_file = output_dir / 'ue_packet_loss_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    print(f"✅ UE packet loss analysis complete! Plot saved to {output_file}")
    if log_file:
        print(f"📋 Log file saved to: {log_file}")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_packet_loss(sys.argv[1])
    else:
        analyze_packet_loss()
