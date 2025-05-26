import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

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
        # Extract bandwidth value from filename
        match = re.search(r'-(\d+)M\.log', file_path.name)
        if match:
            bandwidth_val = int(match.group(1))
            configs.append((bandwidth_val, file_path))
    
    return sorted(configs, key=lambda x: x[0])

def analyze_ping_latency(data_dir=None):
    """Analyze ping latency data"""
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
    
    print(f"Analyzing ping data from: {data_dir}")
    
    # Get all ping configurations
    ping_configs = get_ping_configs(data_dir)
    
    if not ping_configs:
        print("No ping log files found!")
        return
    
    plt.figure(figsize=(14, 8))
    
    avg_latencies = []
    min_latencies = []
    max_latencies = []
    std_latencies = []
    labels = []
    
    print("Processing ping latency data:")
    
    for bandwidth_val, ping_file in ping_configs:
        labels.append(f"{bandwidth_val}M")
        
        print(f"\n{bandwidth_val}M bandwidth configuration:")
        print(f"  Ping file: {ping_file}")
        
        # Parse ping data
        timestamps, latencies = parse_ping_log(ping_file)
        
        if latencies:
            avg_latency = np.mean(latencies)
            min_latency = np.min(latencies)
            max_latency = np.max(latencies)
            std_latency = np.std(latencies)
            
            avg_latencies.append(avg_latency)
            min_latencies.append(min_latency)
            max_latencies.append(max_latency)
            std_latencies.append(std_latency)
            
            print(f"  Average latency: {avg_latency:.2f} ms")
            print(f"  Min latency: {min_latency:.2f} ms")
            print(f"  Max latency: {max_latency:.2f} ms")
            print(f"  Std deviation: {std_latency:.2f} ms")
            print(f"  Total pings: {len(latencies)}")
        else:
            avg_latencies.append(0)
            min_latencies.append(0)
            max_latencies.append(0)
            std_latencies.append(0)
            print(f"  No latency data found")
    
    # Create bar chart with error bars
    x_positions = np.arange(len(labels))
    
    # Create colors based on latency values
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(labels)))
    
    bars = plt.bar(x_positions, avg_latencies, 
                   yerr=std_latencies, 
                   color=colors, 
                   edgecolor='black', 
                   linewidth=0.8, 
                   alpha=0.8,
                   capsize=5)
    
    # Customize the plot
    plt.xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    plt.ylabel('Ping Latency (ms)', fontsize=12, fontweight='bold')
    plt.title('Network Latency Analysis Under Different Bandwidth Loads', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.xticks(x_positions, labels, rotation=0)
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Add value labels on bars
    for i, (bar, avg_lat, min_lat, max_lat) in enumerate(zip(bars, avg_latencies, min_latencies, max_latencies)):
        if avg_lat > 0:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + max(avg_latencies) * 0.01,
                    f'{avg_lat:.1f}ms', ha='center', va='bottom', 
                    fontsize=10, fontweight='bold')
            
            # Add min/max labels
            plt.text(bar.get_x() + bar.get_width()/2., height + std_latencies[i] + max(avg_latencies) * 0.03,
                    f'[{min_lat:.1f}-{max_lat:.1f}]', ha='center', va='bottom', 
                    fontsize=8, color='gray')
    
    # Set y-axis limit
    if avg_latencies and max(avg_latencies) > 0:
        max_val = max([avg + std for avg, std in zip(avg_latencies, std_latencies)])
        plt.ylim(0, max_val * 1.2)
    
    plt.tight_layout()
    output_file = output_dir / 'ping_latency_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"\nPing latency analysis chart saved as '{output_file}'")
    
    # Print summary table
    print("\nPing Latency Summary:")
    print("Bandwidth\tAvg (ms)\tMin (ms)\tMax (ms)\tStd (ms)\tSamples")
    print("-" * 70)
    for i, label in enumerate(labels):
        if avg_latencies[i] > 0:
            print(f"{label}\t\t{avg_latencies[i]:.2f}\t\t{min_latencies[i]:.2f}\t\t{max_latencies[i]:.2f}\t\t{std_latencies[i]:.2f}\t\tN/A")
        else:
            print(f"{label}\t\tN/A\t\tN/A\t\tN/A\t\tN/A\t\tN/A")

if __name__ == "__main__":
    # Check if data directory is provided as command line argument
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
        analyze_ping_latency(data_directory)
    else:
        analyze_ping_latency()
