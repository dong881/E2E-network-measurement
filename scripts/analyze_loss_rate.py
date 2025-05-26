import re
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

def load_json_data(file_path):
    """Load JSON data from a file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_iperf_loss_data(cn_data, ue_data):
    """Extract loss data from iperf CN and UE JSON results"""
    cn_packets_sent = cn_data['end']['streams'][0]['udp']['packets']
    ue_packets_received = ue_data['end']['streams'][0]['udp']['packets']
    
    # Calculate loss percentages
    cn_loss_percent = cn_data['end']['streams'][0]['udp']['lost_percent']
    ue_loss_percent = ue_data['end']['streams'][0]['udp']['lost_percent']
    
    # Manual calculation based on actual packet counts
    manual_loss_rate = ((cn_packets_sent - ue_packets_received) / cn_packets_sent) * 100 if cn_packets_sent > 0 else 0
    
    return {
        'cn_packets_sent': cn_packets_sent,
        'ue_packets_received': ue_packets_received,
        'cn_loss_percent': cn_loss_percent,
        'ue_loss_percent': ue_loss_percent,
        'manual_loss_rate': manual_loss_rate
    }

def get_jitter_info(ue_data):
    """Extract jitter information from UE data"""
    try:
        return ue_data['end']['streams'][0]['udp']['jitter_ms']
    except KeyError:
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

def analyze_loss_rates(data_dir=None):
    """Main function to analyze and plot loss rates"""
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
    
    print(f"Analyzing loss data from: {data_dir}")
    
    # Get all bandwidth configurations
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("No bandwidth configuration files found!")
        return
    
    iperf_loss_rates = []
    manual_loss_rates = []
    jitter_values = []
    labels = []
    
    print("Processing loss rate calculations (iperf vs manual):")
    
    for bandwidth_val in bandwidth_configs:
        labels.append(f"{bandwidth_val}M")
        
        # Find corresponding files
        cn_file, ue_file = find_iperf_files(data_dir, bandwidth_val)
        
        print(f"\n{bandwidth_val}M bandwidth configuration:")
        
        # Load data and extract loss information
        cn_data = load_json_data(cn_file) if cn_file else None
        ue_data = load_json_data(ue_file) if ue_file else None
        
        loss_data = extract_iperf_loss_data(cn_data, ue_data)
        jitter = get_jitter_info(ue_data)
        
        # Use the more accurate loss rate (manual calculation from actual packet counts)
        final_loss_rate = loss_data['manual_loss_rate']
        
        iperf_loss_rates.append(loss_data['ue_loss_percent'])
        manual_loss_rates.append(final_loss_rate)
        jitter_values.append(jitter if jitter else 0)
        
        print(f"  CN packets sent: {loss_data['cn_packets_sent']}")
        print(f"  UE packets received: {loss_data['ue_packets_received']}")
        print(f"  CN reported loss: {loss_data['cn_loss_percent']:.2f}%")
        print(f"  UE reported loss: {loss_data['ue_loss_percent']:.2f}%")
        print(f"  Manual calculated loss: {final_loss_rate:.2f}%")
        if jitter:
            print(f"  Jitter: {jitter:.3f} ms")
    
    # Create the plot using manual calculation (more accurate)
    plt.figure(figsize=(12, 7))
    
    # Create color gradient based on loss rate values
    if max(manual_loss_rates) > 0:
        normalized_rates = np.array(manual_loss_rates) / max(manual_loss_rates)
        colors = plt.cm.Reds(0.3 + normalized_rates * 0.6)
    else:
        colors = ['#2E86AB'] * len(manual_loss_rates)
    
    bars = plt.bar(range(len(labels)), manual_loss_rates, color=colors, 
                   edgecolor='black', linewidth=0.8, alpha=0.8)
    
    # Customize the plot
    plt.xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    plt.ylabel('Packet Loss Rate (%)', fontsize=12, fontweight='bold')
    plt.title('Network Packet Loss Rate Analysis (Manual Calculation)', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(range(len(labels)), labels, rotation=0)
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for i, (bar, loss_rate) in enumerate(zip(bars, manual_loss_rates)):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + max(manual_loss_rates) * 0.01,
                f'{loss_rate:.2f}%', ha='center', va='bottom', 
                fontsize=10, fontweight='bold')
    
    # Add a horizontal line at acceptable loss rate threshold (e.g., 1%)
    if max(manual_loss_rates) > 1:
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, linewidth=2, 
                    label='1% Loss Threshold')
        plt.legend(fontsize=10)
    
    # Set y-axis to start from 0 and add some margin
    plt.ylim(0, max(manual_loss_rates) * 1.15 if manual_loss_rates and max(manual_loss_rates) > 0 else 5)
    
    plt.tight_layout()
    output_file = output_dir / 'loss_rate_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    # Print detailed comparison
    print("\nDetailed Loss Rate Comparison:")
    print("Bandwidth\t\tiperf Report\tManual Calc\tJitter (ms)")
    print("-" * 70)
    for i, label in enumerate(labels):
        iperf_loss = iperf_loss_rates[i]
        manual_loss = manual_loss_rates[i]
        jitter = jitter_values[i]
        jitter_str = f"{jitter:.3f}" if jitter > 0 else "N/A"
        print(f"{label}\t\t{iperf_loss:.2f}%\t\t{manual_loss:.2f}%\t\t{jitter_str}")
    
    print(f"\nLoss rate analysis chart saved as '{output_file}'")

if __name__ == "__main__":
    # Check if data directory is provided as command line argument
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
        analyze_loss_rates(data_directory)
    else:
        analyze_loss_rates()