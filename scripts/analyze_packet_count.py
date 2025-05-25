import json
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re

def load_json_data(file_path):
    """Load JSON data from a file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

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

def extract_packet_counts(cn_data, ue_data):
    """Extract packet counts from CN and UE data"""
    cn_packets = cn_data['end']['streams'][0]['udp']['packets'] if cn_data and 'end' in cn_data and 'streams' in cn_data['end'] and len(cn_data['end']['streams']) > 0 and 'udp' in cn_data['end']['streams'][0] else 0
    ue_packets = ue_data['end']['streams'][0]['udp']['packets'] if ue_data and 'end' in ue_data and 'streams' in ue_data['end'] and len(ue_data['end']['streams']) > 0 and 'udp' in ue_data['end']['streams'][0] else 0
    
    return cn_packets, ue_packets

def analyze_packet_counts():
    """Main function to analyze and plot packet counts"""
    data_dir = Path('/home/mini/E2E-network-measurement/data/20250525-TEST')
    output_dir = Path('/home/mini/E2E-network-measurement/output')
    output_dir.mkdir(exist_ok=True)
    
    # Get all bandwidth configurations
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("No bandwidth configuration files found!")
        return
    
    plt.figure(figsize=(14, 8))
    
    cn_packet_counts = []
    ue_packet_counts = []
    labels = []
    
    print("Processing packet count analysis:")
    
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
        
        # Extract packet counts
        cn_packets, ue_packets = extract_packet_counts(cn_data, ue_data)
        
        cn_packet_counts.append(cn_packets)
        ue_packet_counts.append(ue_packets)
        
        print(f"  CN sent packets: {cn_packets}")
        print(f"  UE received packets: {ue_packets}")
        
        # Calculate difference
        if cn_packets > 0 and ue_packets > 0:
            lost_packets = cn_packets - ue_packets
            loss_percent = (lost_packets / cn_packets) * 100
            print(f"  Lost packets: {lost_packets} ({loss_percent:.2f}%)")
    
    # Create grouped bar chart
    bar_width = 0.35
    x_positions = np.arange(len(labels))
    
    bars1 = plt.bar(x_positions - bar_width/2, cn_packet_counts, bar_width, 
                    label='CN Packets Sent', color='#3498db', alpha=0.8, 
                    edgecolor='black', linewidth=0.5)
    bars2 = plt.bar(x_positions + bar_width/2, ue_packet_counts, bar_width, 
                    label='UE Packets Received', color='#e74c3c', alpha=0.8, 
                    edgecolor='black', linewidth=0.5)
    
    # Customize the plot
    plt.xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    plt.ylabel('Packet Count', fontsize=12, fontweight='bold')
    plt.title('Network Packet Analysis: Sent vs Received Packets', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(x_positions, labels, rotation=0)
    plt.legend(fontsize=11, loc='upper left')
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for i, (cn_count, ue_count) in enumerate(zip(cn_packet_counts, ue_packet_counts)):
        if cn_count > 0:
            plt.text(bars1[i].get_x() + bars1[i].get_width()/2., cn_count + max(cn_packet_counts) * 0.01, 
                    f'{cn_count:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        if ue_count > 0:
            plt.text(bars2[i].get_x() + bars2[i].get_width()/2., ue_count + max(ue_packet_counts) * 0.01, 
                    f'{ue_count:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Set y-axis limit
    max_val = max(max(cn_packet_counts) if cn_packet_counts else [0], 
                  max(ue_packet_counts) if ue_packet_counts else [0])
    if max_val > 0:
        plt.ylim(0, max_val * 1.15)
    
    plt.tight_layout()
    output_file = output_dir / 'packet_count_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"\nPacket count analysis chart saved as '{output_file}'")
    
    # Print summary table
    print("\nPacket Count Summary:")
    print("Bandwidth\t\tSent\t\tReceived\tLost\t\tLoss%")
    print("-" * 70)
    for i, label in enumerate(labels):
        sent = cn_packet_counts[i]
        received = ue_packet_counts[i]
        lost = sent - received
        loss_pct = (lost / sent * 100) if sent > 0 else 0
        print(f"{label}\t\t{sent:,}\t\t{received:,}\t\t{lost:,}\t\t{loss_pct:.2f}%")

if __name__ == "__main__":
    analyze_packet_counts()