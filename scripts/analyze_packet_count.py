import json
import matplotlib.pyplot as plt
import numpy as np
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

def analyze_packet_count(data_dir=None):
    """Main function to analyze and plot packet count comparison"""
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
    
    print(f"Analyzing packet data from: {data_dir}")
    
    # Get all bandwidth configurations
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("No bandwidth configuration files found!")
        return
    
    plt.figure(figsize=(14, 8))
    
    cn_packets = []
    ue_packets = []
    labels = []
    
    print("Processing packet count data:")
    
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
        cn_packet_count = 0
        ue_packet_count = 0
        
        if cn_data and 'end' in cn_data and 'sum' in cn_data['end']:
            cn_packet_count = cn_data['end']['sum'].get('packets', 0)
        
        if ue_data and 'end' in ue_data and 'sum_received' in ue_data['end']:
            ue_packet_count = ue_data['end']['sum_received'].get('packets', 0)
        
        cn_packets.append(cn_packet_count)
        ue_packets.append(ue_packet_count)
        
        print(f"  CN packets sent: {cn_packet_count}")
        print(f"  UE packets received: {ue_packet_count}")
        
        if cn_packet_count > 0:
            packet_loss = cn_packet_count - ue_packet_count
            loss_percent = (packet_loss / cn_packet_count) * 100
            print(f"  Packet loss: {packet_loss} ({loss_percent:.2f}%)")
    
    # Create grouped bar chart
    bar_width = 0.35
    x_positions = np.arange(len(labels))
    
    bars1 = plt.bar(x_positions - bar_width/2, cn_packets, bar_width, 
                    label='CN Packets Sent', color='#2E86AB', alpha=0.8, 
                    edgecolor='black', linewidth=0.5)
    bars2 = plt.bar(x_positions + bar_width/2, ue_packets, bar_width, 
                    label='UE Packets Received', color='#A23B72', alpha=0.8, 
                    edgecolor='black', linewidth=0.5)
    
    # Customize the plot
    plt.xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    plt.ylabel('Packet Count', fontsize=12, fontweight='bold')
    plt.title('Network Packet Count Analysis: CN Transmission vs UE Reception', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(x_positions, labels, rotation=0)
    plt.legend(fontsize=11, loc='upper left')
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Improved value labels on bars - fix overlapping
    max_val = max(max(cn_packets) if cn_packets else [0], max(ue_packets) if ue_packets else [0])
    
    for i, (cn_val, ue_val) in enumerate(zip(cn_packets, ue_packets)):
        # Format numbers with appropriate unit (K for thousands, M for millions)
        def format_number(num):
            if num >= 1_000_000:
                return f'{num/1_000_000:.1f}M'
            elif num >= 1_000:
                return f'{num/1_000:.1f}K'
            else:
                return str(num)
        
        # Position labels with proper spacing
        if cn_val > 0:
            plt.text(bars1[i].get_x() + bars1[i].get_width()/2., 
                    cn_val + max_val * 0.02, 
                    format_number(cn_val), 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        if ue_val > 0:
            plt.text(bars2[i].get_x() + bars2[i].get_width()/2., 
                    ue_val + max_val * 0.02, 
                    format_number(ue_val), 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # Set y-axis limit with better spacing
    if max_val > 0:
        plt.ylim(0, max_val * 1.25)
    
    # Format y-axis with appropriate units
    def y_formatter(x, pos):
        if x >= 1_000_000:
            return f'{x/1_000_000:.1f}M'
        elif x >= 1_000:
            return f'{x/1_000:.0f}K'
        else:
            return f'{x:.0f}'
    
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(y_formatter))
    
    plt.tight_layout()
    output_file = output_dir / 'packet_count_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"\nPacket count comparison chart saved as '{output_file}'")

if __name__ == "__main__":
    # Check if data directory is provided as command line argument
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
        analyze_packet_count(data_directory)
    else:
        analyze_packet_count()