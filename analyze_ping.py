import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def parse_ping_log(file_path):
    """Parse ping log file and extract latency data"""
    latencies = []
    timestamps = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Parse ping response line
                if 'time=' in line:
                    # Extract timestamp
                    timestamp_match = re.search(r'^(\d+):', line)
                    if timestamp_match:
                        timestamp = int(timestamp_match.group(1))
                        timestamps.append(timestamp)
                    
                    # Extract latency
                    time_match = re.search(r'time=([0-9.]+) ms', line)
                    if time_match:
                        latency = float(time_match.group(1))
                        latencies.append(latency)
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return timestamps, latencies

def get_ping_configs(data_dir):
    """Find all ping configuration files"""
    configs = []
    
    for file_path in data_dir.glob('ping*-*M.log'):
        # Extract throughput value from filename
        match = re.search(r'-(\d+)M\.log', file_path.name)
        if match:
            throughput_val = int(match.group(1))
            configs.append((throughput_val, file_path))
    
    return sorted(configs, key=lambda x: x[0])

def analyze_ping_latency():
    """Analyze ping latency data"""
    data_dir = Path('/home/mini/E2E-network-measurement/data/20250525-TEST')
    
    # Get all ping configurations
    ping_configs = get_ping_configs(data_dir)
    
    if not ping_configs:
        print("No ping log files found!")
        return
    
    plt.figure(figsize=(14, 8))
    
    avg_latencies = []
    labels = []
    
    print("Processing ping latency data:")
    
    for throughput_val, ping_file in ping_configs:
        labels.append(f"{throughput_val}M")
        
        print(f"\n{throughput_val}M configuration:")
        print(f"  Ping file: {ping_file}")
        
        # Parse ping data
        timestamps, latencies = parse_ping_log(ping_file)
        
        if latencies:
            avg_latency = np.mean(latencies)
            min_latency = np.min(latencies)
            max_latency = np.max(latencies)
            std_latency = np.std(latencies)
            
            avg_latencies.append(avg_latency)
            
            print(f"  Average latency: {avg_latency:.2f} ms")
            print(f"  Min latency: {min_latency:.2f} ms")
            print(f"  Max latency: {max_latency:.2f} ms")
            print(f"  Std deviation: {std_latency:.2f} ms")
        else:
            avg_latencies.append(0)
            print(f"  No latency data found")
    
    # Create bar chart
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(labels)))
    bars = plt.bar(range(len(labels)), avg_latencies, color=colors, 
                   edgecolor='black', linewidth=0.8, alpha=0.8)
    
    # Customize the plot
    plt.xlabel('Throughput Configuration', fontsize=12, fontweight='bold')
    plt.ylabel('Average Ping Latency (ms)', fontsize=12, fontweight='bold')
    plt.title('Network Latency Analysis Under Different Loads', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(range(len(labels)), labels, rotation=0)
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for i, (bar, latency) in enumerate(zip(bars, avg_latencies)):
        if latency > 0:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + max(avg_latencies) * 0.01,
                    f'{latency:.1f}ms', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold')
    
    # Set y-axis limit
    if avg_latencies and max(avg_latencies) > 0:
        plt.ylim(0, max(avg_latencies) * 1.15)
    
    plt.tight_layout()
    plt.savefig('/home/mini/E2E-network-measurement/ping_latency_analysis.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"\nPing latency analysis chart saved as 'ping_latency_analysis.png'")

if __name__ == "__main__":
    analyze_ping_latency()
