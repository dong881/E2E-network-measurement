import json
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re

def load_json_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def calculate_iperf_loss_rate(cn_data, ue_data):
    """Calculate packet loss rate from iperf3 data"""
    if not cn_data or not ue_data:
        return 0, 0, 0, 0
    
    try:
        # Get packet counts from CN (sender) and UE (receiver)
        cn_packets_sent = 0
        cn_bytes_sent = 0
        ue_packets_received = 0
        ue_bytes_received = 0
        
        # From CN (sender) data - get total packets and bytes sent
        if 'end' in cn_data and 'sum' in cn_data['end']:
            cn_packets_sent = cn_data['end']['sum'].get('packets', 0)
            cn_bytes_sent = cn_data['end']['sum'].get('bytes', 0)
        
        # From UE (receiver) data - get packets and bytes actually received
        # Use sum_received which is the most accurate for received data
        if 'end' in ue_data and 'sum_received' in ue_data['end']:
            ue_packets_received = ue_data['end']['sum_received'].get('packets', 0)
            ue_bytes_received = ue_data['end']['sum_received'].get('bytes', 0)
        
        print(f"  CN sent: {cn_packets_sent} packets, {cn_bytes_sent} bytes")
        print(f"  UE received: {ue_packets_received} packets, {ue_bytes_received} bytes")
        
        # Calculate loss rates
        packet_loss_rate = 0
        byte_loss_rate = 0
        
        if cn_packets_sent > 0:
            lost_packets = cn_packets_sent - ue_packets_received
            packet_loss_rate = (lost_packets / cn_packets_sent) * 100
            packet_loss_rate = max(0, packet_loss_rate)  # Ensure non-negative
        
        if cn_bytes_sent > 0:
            lost_bytes = cn_bytes_sent - ue_bytes_received
            byte_loss_rate = (lost_bytes / cn_bytes_sent) * 100
            byte_loss_rate = max(0, byte_loss_rate)  # Ensure non-negative
        
        return packet_loss_rate, byte_loss_rate, cn_packets_sent, ue_packets_received
        
    except Exception as e:
        print(f"Error calculating loss rate: {e}")
        return 0, 0, 0, 0

def get_jitter_info(ue_data):
    """Extract jitter information from UE data"""
    if not ue_data:
        return None
    
    try:
        if 'end' in ue_data and 'sum_received' in ue_data['end']:
            return ue_data['end']['sum_received'].get('jitter_ms', None)
        elif 'end' in ue_data and 'sum' in ue_data['end']:
            return ue_data['end']['sum'].get('jitter_ms', None)
    except:
        pass
    
    return None

def get_throughput_configs(data_dir):
    """Find all throughput configuration directories"""
    configs = []
    
    # Look for files with throughput patterns
    for file_path in data_dir.glob('iperf*-*M-*.json'):
        # Extract throughput value from filename
        match = re.search(r'-(\d+)M-', file_path.name)
        if match:
            throughput_val = int(match.group(1))
            configs.append(throughput_val)
    
    return sorted(list(set(configs)))

def find_iperf_files(data_dir, throughput_val):
    """Find CN and UE iperf files for a specific throughput"""
    cn_file = None
    ue_file = None
    
    # Look for files matching the pattern
    cn_pattern = f"iperf*-{throughput_val}M-CN.json"
    ue_pattern = f"iperf*-{throughput_val}M-UE.json"
    
    for file_path in data_dir.glob(cn_pattern):
        cn_file = file_path
        break
    
    for file_path in data_dir.glob(ue_pattern):
        ue_file = file_path
        break
    
    return cn_file, ue_file

def analyze_loss_rates():
    """Main function to analyze and plot loss rates"""
    data_dir = Path('/home/mini/E2E-network-measurement/data/20250525-TEST')
    
    # Get all throughput configurations
    throughput_configs = get_throughput_configs(data_dir)
    
    if not throughput_configs:
        print("No throughput configuration files found!")
        return
    
    packet_loss_rates = []
    byte_loss_rates = []
    jitter_values = []
    labels = []
    
    print("Processing loss rate calculations:")
    
    for throughput_val in throughput_configs:
        labels.append(f"{throughput_val}M")
        
        # Find corresponding files
        cn_file, ue_file = find_iperf_files(data_dir, throughput_val)
        
        print(f"\n{throughput_val}M configuration:")
        
        # Load data and calculate loss rate
        cn_data = load_json_data(cn_file) if cn_file else None
        ue_data = load_json_data(ue_file) if ue_file else None
        
        packet_loss_rate, byte_loss_rate, sent_packets, received_packets = calculate_iperf_loss_rate(cn_data, ue_data)
        jitter = get_jitter_info(ue_data)
        
        packet_loss_rates.append(packet_loss_rate)
        byte_loss_rates.append(byte_loss_rate)
        jitter_values.append(jitter if jitter else 0)
        
        print(f"  Packet loss rate: {packet_loss_rate:.2f}%")
        print(f"  Byte loss rate: {byte_loss_rate:.2f}%")
        if jitter:
            print(f"  Jitter: {jitter:.3f} ms")
    
    # Create the plot - use packet loss rate as primary metric
    plt.figure(figsize=(12, 7))
    
    # Create color gradient based on loss rate values
    if max(packet_loss_rates) > 0:
        normalized_rates = np.array(packet_loss_rates) / max(packet_loss_rates)
        colors = plt.cm.Reds(0.3 + normalized_rates * 0.6)
    else:
        colors = ['#2E86AB'] * len(packet_loss_rates)
    
    bars = plt.bar(range(len(labels)), packet_loss_rates, color=colors, 
                   edgecolor='black', linewidth=0.8, alpha=0.8)
    
    # Customize the plot
    plt.xlabel('Throughput Configuration', fontsize=12, fontweight='bold')
    plt.ylabel('Packet Loss Rate (%)', fontsize=12, fontweight='bold')
    plt.title('Network Packet Loss Rate Analysis', fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(range(len(labels)), labels, rotation=0)
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for i, (bar, loss_rate) in enumerate(zip(bars, packet_loss_rates)):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + max(packet_loss_rates) * 0.01,
                f'{loss_rate:.2f}%', ha='center', va='bottom', 
                fontsize=10, fontweight='bold')
    
    # Add a horizontal line at acceptable loss rate threshold (e.g., 1%)
    if max(packet_loss_rates) > 1:
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, linewidth=2, 
                    label='1% Loss Threshold')
        plt.legend(fontsize=10)
    
    # Set y-axis to start from 0 and add some margin
    plt.ylim(0, max(packet_loss_rates) * 1.15 if packet_loss_rates and max(packet_loss_rates) > 0 else 5)
    
    plt.tight_layout()
    plt.savefig('/home/mini/E2E-network-measurement/loss_rate_analysis.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    # Print summary
    print("\nDetailed Loss Analysis Summary:")
    for i, label in enumerate(labels):
        jitter_str = f", Jitter: {jitter_values[i]:.3f}ms" if jitter_values[i] > 0 else ""
        print(f"{label}: Packet Loss: {packet_loss_rates[i]:.2f}%, Byte Loss: {byte_loss_rates[i]:.2f}%{jitter_str}")
    
    print(f"\nLoss rate analysis chart saved as 'loss_rate_analysis.png'")

if __name__ == "__main__":
    analyze_loss_rates()
