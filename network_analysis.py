import json
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from datetime import datetime

def parse_ping_log(ping_file):
    """Parse ping log file to extract timestamp and latency data."""
    ping_data = []
    pattern = r'(\d+): 64 bytes from .+ time=(\d+\.?\d*) ms'
    
    with open(ping_file, 'r') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                timestamp = int(match.group(1))
                latency = float(match.group(2))
                ping_data.append((timestamp, latency))
    
    return pd.DataFrame(ping_data, columns=['timestamp', 'latency'])

def parse_iperf_data(iperf_file):
    """Parse iperf JSON file to extract throughput data."""
    with open(iperf_file, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            # Handle corrupted JSON files
            with open(iperf_file, 'r') as f2:
                content = f2.read()
                # Find the first complete JSON object
                first_json_end = content.find('}\n{')
                if first_json_end > 0:
                    data = json.loads(content[:first_json_end+1])
                else:
                    data = json.loads(content)
    
    start_timestamp = data.get('start_timestamp')
    
    # Extract interval data
    throughput_data = []
    for interval in data.get('intervals', []):
        start_time = interval['sum']['start']
        end_time = interval['sum']['end']
        mid_time = (start_time + end_time) / 2
        abs_timestamp = start_timestamp + mid_time
        
        # Use bits_per_second directly
        throughput = interval['sum']['bits_per_second'] / 1_000_000  # Convert to Mbps
        
        throughput_data.append((abs_timestamp, throughput))
    
    return pd.DataFrame(throughput_data, columns=['timestamp', 'throughput'])

def match_ping_iperf_data(ping_df, iperf_df):
    """Match ping and iperf data based on closest timestamp."""
    matched_data = []
    
    # For each iperf measurement, find the closest ping measurement
    for _, iperf_row in iperf_df.iterrows():
        iperf_time = iperf_row['timestamp']
        
        # Find closest ping data point
        closest_idx = (ping_df['timestamp'] - iperf_time).abs().idxmin()
        closest_ping = ping_df.loc[closest_idx]
        
        # Only match if within reasonable time threshold (e.g., 1 second)
        if abs(closest_ping['timestamp'] - iperf_time) <= 1:
            matched_data.append({
                'timestamp': iperf_time,
                'throughput': iperf_row['throughput'],
                'latency': closest_ping['latency'],
                'ping_timestamp': closest_ping['timestamp']
            })
    
    return pd.DataFrame(matched_data)

def create_visualizations(matched_df, ping_df, iperf_df, output_dir):
    """Create visualizations from the matched data."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Throughput vs Latency scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(matched_df['latency'], matched_df['throughput'], alpha=0.7)
    plt.title('Network Performance: Throughput vs Latency')
    plt.xlabel('Latency (ms)')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'throughput_vs_latency.png'), dpi=300)
    plt.close()
    
    # 2. Time series of both metrics
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Plot throughput on left y-axis
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Throughput (Mbps)', color=color)
    ax1.plot(iperf_df['timestamp'], iperf_df['throughput'], 'o-', color=color, alpha=0.7, label='Throughput')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Plot latency on right y-axis
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Latency (ms)', color=color)
    ax2.plot(ping_df['timestamp'], ping_df['latency'], 'o-', color=color, alpha=0.7, label='Latency')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Format x-axis as human-readable time
    plt.title('Network Performance Over Time')
    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, 'time_series.png'), dpi=300)
    plt.close()
    
    # 3. Latency distribution during data transfer
    plt.figure(figsize=(10, 6))
    min_iperf_time = iperf_df['timestamp'].min()
    max_iperf_time = iperf_df['timestamp'].max()
    
    # Get ping data during iperf test
    during_test = ping_df[(ping_df['timestamp'] >= min_iperf_time-1) & 
                          (ping_df['timestamp'] <= max_iperf_time+1)]
    before_test = ping_df[ping_df['timestamp'] < min_iperf_time-1]
    
    plt.hist([before_test['latency'], during_test['latency']], bins=15, 
             alpha=0.7, label=['Before Transfer', 'During Transfer'])
    plt.title('Latency Distribution: Before vs. During Data Transfer')
    plt.xlabel('Latency (ms)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'latency_distribution.png'), dpi=300)
    plt.close()
    
    # 4. Throughput vs time with latency color mapping
    plt.figure(figsize=(12, 7))
    scatter = plt.scatter(matched_df['timestamp'], matched_df['throughput'], 
                c=matched_df['latency'], cmap='viridis', 
                alpha=0.8, s=50, edgecolors='k', linewidth=0.5)
    plt.colorbar(scatter, label='Latency (ms)')
    plt.title('Throughput Over Time (Colored by Latency)')
    plt.xlabel('Time')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'throughput_time_latency_color.png'), dpi=300)
    plt.close()

def analyze_network_performance(ping_file, iperf_file, output_dir):
    """Main function to analyze network performance."""
    print(f"Analyzing files:\n- {ping_file}\n- {iperf_file}")
    
    # Parse data
    ping_df = parse_ping_log(ping_file)
    iperf_df = parse_iperf_data(iperf_file)
    
    if ping_df.empty or iperf_df.empty:
        print("Error: No data found in input files")
        return
    
    print(f"Found {len(ping_df)} ping data points and {len(iperf_df)} iperf intervals")
    
    # Match data points
    matched_df = match_ping_iperf_data(ping_df, iperf_df)
    
    if matched_df.empty:
        print("Error: Could not match ping and iperf data. Check timestamps.")
        return
    
    print(f"Successfully matched {len(matched_df)} data points")
    
    # Create visualizations
    create_visualizations(matched_df, ping_df, iperf_df, output_dir)
    print(f"Visualizations saved to {output_dir}")
    
    # Print correlation coefficient
    corr = matched_df['throughput'].corr(matched_df['latency'])
    print(f"Correlation between throughput and latency: {corr:.4f}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("\nThroughput (Mbps):")
    print(matched_df['throughput'].describe())
    print("\nLatency (ms):")
    print(matched_df['latency'].describe())

if __name__ == "__main__":
    data_dir = "/home/ming/E2E-network-measurement/data/20250417"
    output_dir = "/home/ming/E2E-network-measurement/results/20250417"
    
    ping_file = os.path.join(data_dir, "ping-dl-udp-100M.log")
    iperf_file = os.path.join(data_dir, "iperf-dl-udp-100M-UE.json")
    
    analyze_network_performance(ping_file, iperf_file, output_dir)
