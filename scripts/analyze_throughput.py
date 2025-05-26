import json
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pandas as pd
from pathlib import Path
import re
import sys

def load_json_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def extract_cn_throughput(data):
    """Extract CN (sender) throughput data from iperf3 JSON"""
    if not data:
        return None, None, 0
    
    try:
        # CN is the sender, get sent data from end.sum (sender=true)
        if 'end' in data and 'sum' in data['end']:
            bits_per_second = data['end']['sum'].get('bits_per_second', 0)
            mbits_per_second = bits_per_second / 1_000_000  # Convert to Mbps
            packets_sent = data['end']['sum'].get('packets', 0)
            
            # Get interval data for time series (sender intervals)
            intervals = []
            throughputs = []
            
            if 'intervals' in data:
                for interval in data['intervals']:
                    if 'sum' in interval and interval['sum'].get('sender', False):
                        start_time = interval['sum'].get('start', 0)
                        interval_bps = interval['sum'].get('bits_per_second', 0)
                        interval_mbps = interval_bps / 1_000_000
                        
                        intervals.append(start_time)
                        throughputs.append(interval_mbps)
            
            return mbits_per_second, (intervals, throughputs), packets_sent
        
        return None, None, 0
    except Exception as e:
        print(f"Error extracting CN throughput: {e}")
        return None, None, 0

def extract_ue_throughput(data):
    """Extract UE (receiver) throughput data from iperf3 JSON"""
    if not data:
        return None, None, 0
    
    try:
        # UE is the receiver, get received data from sum_received (most accurate)
        received_mbps = None
        packets_received = 0
        
        if 'end' in data and 'sum_received' in data['end']:
            # This is the actual received data at UE
            bits_per_second = data['end']['sum_received'].get('bits_per_second', 0)
            received_mbps = bits_per_second / 1_000_000
            packets_received = data['end']['sum_received'].get('packets', 0)
        
        # Get interval data for receiver (sender=false)
        intervals = []
        throughputs = []
        
        if 'intervals' in data:
            for interval in data['intervals']:
                if 'sum' in interval and not interval['sum'].get('sender', True):
                    start_time = interval['sum'].get('start', 0)
                    interval_bps = interval['sum'].get('bits_per_second', 0)
                    interval_mbps = interval_bps / 1_000_000
                    
                    intervals.append(start_time)
                    throughputs.append(interval_mbps)
        
        return received_mbps, (intervals, throughputs), packets_received
        
    except Exception as e:
        print(f"Error extracting UE throughput: {e}")
        return None, None, 0

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration directories"""
    configs = []
    
    # Look for files with bandwidth patterns
    for file_path in data_dir.glob('iperf*-*M-*.json'):
        # Extract bandwidth value from filename
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

def analyze_throughput_comparison(data_dir=None):
    """Main function to analyze and plot throughput comparison"""
    # Use provided data_dir or interactive selection
    if data_dir is None:
        from data_selector import get_data_folder_interactive
        data_dir = get_data_folder_interactive()
        if not data_dir:
            print("No data folder selected. Exiting...")
            return
    else:
        data_dir = Path(data_dir)
    
    output_dir = Path('~/E2E-network-measurement/output').expanduser()
    output_dir.mkdir(exist_ok=True)
    
    print(f"Analyzing data from: {data_dir}")
    
    # Get all bandwidth configurations
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("No bandwidth configuration files found!")
        return
    
    plt.figure(figsize=(14, 8))
    
    cn_averages = []
    ue_averages = []
    labels = []
    
    print("Processing bandwidth configurations:")
    
    for bandwidth_val in bandwidth_configs:
        labels.append(f"{bandwidth_val}M")
        
        # Find corresponding files
        cn_file, ue_file = find_iperf_files(data_dir, bandwidth_val)
        
        print(f"\n{bandwidth_val}M bandwidth configuration:")
        print(f"  CN file: {cn_file}")
        print(f"  UE file: {ue_file}")
        
        # Load and process data
        cn_data = load_json_data(cn_file) if cn_file else None
        ue_data = load_json_data(ue_file) if ue_file else None
        
        # Extract throughput values with correct sender/receiver logic
        cn_avg, cn_intervals, cn_packets = extract_cn_throughput(cn_data)
        ue_avg, ue_intervals, ue_packets = extract_ue_throughput(ue_data)
        
        cn_averages.append(cn_avg if cn_avg else 0)
        ue_averages.append(ue_avg if ue_avg else 0)
        
        print(f"  CN sent: {cn_avg:.2f} Mbps, {cn_packets} packets" if cn_avg else "  CN sent: N/A")
        print(f"  UE received: {ue_avg:.2f} Mbps, {ue_packets} packets" if ue_avg else "  UE received: N/A")
        
        # Calculate and show the difference
        if cn_avg and ue_avg:
            throughput_diff = cn_avg - ue_avg
            packet_diff = cn_packets - ue_packets
            throughput_loss_percent = (throughput_diff / cn_avg) * 100
            packet_loss_percent = (packet_diff / cn_packets) * 100 if cn_packets > 0 else 0
            
            print(f"  Throughput difference: {throughput_diff:.2f} Mbps ({throughput_loss_percent:.2f}% loss)")
            print(f"  Packet difference: {packet_diff} packets ({packet_loss_percent:.2f}% loss)")
    
    # Create grouped bar chart
    bar_width = 0.35
    x_positions = np.arange(len(labels))
    
    bars1 = plt.bar(x_positions - bar_width/2, cn_averages, bar_width, 
                    label='CN Transmission (Sent)', color='#2E86AB', alpha=0.8, 
                    edgecolor='black', linewidth=0.5)
    bars2 = plt.bar(x_positions + bar_width/2, ue_averages, bar_width, 
                    label='UE Reception (Received)', color='#A23B72', alpha=0.8, 
                    edgecolor='black', linewidth=0.5)
    
    # Customize the plot
    plt.xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    plt.ylabel('Actual Throughput (Mbits/s)', fontsize=12, fontweight='bold')
    plt.title('Network Throughput Analysis: CN Transmission vs UE Reception', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(x_positions, labels, rotation=0)
    plt.legend(fontsize=11, loc='upper left')
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for i, (cn_val, ue_val) in enumerate(zip(cn_averages, ue_averages)):
        if cn_val > 0:
            plt.text(bars1[i].get_x() + bars1[i].get_width()/2., cn_val + max(cn_averages) * 0.01, 
                    f'{cn_val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        if ue_val > 0:
            plt.text(bars2[i].get_x() + bars2[i].get_width()/2., ue_val + max(ue_averages) * 0.01, 
                    f'{ue_val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Set y-axis limit
    max_val = max(max(cn_averages) if cn_averages else [0], max(ue_averages) if ue_averages else [0])
    if max_val > 0:
        plt.ylim(0, max_val * 1.15)
    
    plt.tight_layout()
    output_file = output_dir / 'throughput_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"\nThroughput comparison chart saved as '{output_file}'")

if __name__ == "__main__":
    # Check if data directory is provided as command line argument
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
        analyze_throughput_comparison(data_directory)
    else:
        analyze_throughput_comparison()
