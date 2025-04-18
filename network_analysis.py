import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import glob

# Define the root data directory
DATA_DIR = "/home/ming/E2E-network-measurement/data/20250418"
OUTPUT_DIR = "/home/ming/E2E-network-measurement/results/20250418"

def parse_iperf_json(file_path):
    """Parse iperf JSON files to extract throughput data"""
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {file_path}: {e}")
            return pd.DataFrame(columns=["throughput"])
    
    throughputs = []
    
    if "intervals" in data:
        for interval in data.get("intervals", []):
            for stream in interval.get("streams", []):
                throughput = stream.get("bits_per_second", 0) / 1_000_000  # Convert to Mbps
                throughputs.append(throughput)
    
    return pd.DataFrame({"throughput": throughputs})

def parse_ping_log(file_path):
    """Parse ping log files to extract latency data"""
    ping_times = []
    
    with open(file_path, 'r') as f:
        for line in f:
            ping_match = re.search(r'time=([\d.]+) ms', line)
            if ping_match:
                ping_times.append(float(ping_match.group(1)))
    
    return pd.DataFrame({"ping_time": ping_times})

def extract_bandwidth(filename):
    """Extract bandwidth value from filename"""
    match = re.search(r'udp-(\d+M)', filename)
    if match:
        bw_str = match.group(1)
        if bw_str.endswith('M'):
            return int(bw_str[:-1])
    return 0

def analyze_test_group(cn_file, ue_file, ping_file):
    """Analyze one test group (CN, UE, ping) to calculate throughput and latency statistics"""
    bandwidth = extract_bandwidth(os.path.basename(cn_file))
    
    cn_data = parse_iperf_json(cn_file)
    ue_data = parse_iperf_json(ue_file)
    ping_data = parse_ping_log(ping_file)
    
    cn_throughput = cn_data["throughput"].mean() if not cn_data.empty else 0
    ue_throughput = ue_data["throughput"].mean() if not ue_data.empty else 0
    
    min_ping = ping_data["ping_time"].min() if not ping_data.empty else 0
    max_ping = ping_data["ping_time"].max() if not ping_data.empty else 0
    avg_ping = ping_data["ping_time"].mean() if not ping_data.empty else 0
    
    return {
        "target_bandwidth": bandwidth,
        "cn_throughput": cn_throughput,
        "ue_throughput": ue_throughput,
        "min_ping": min_ping,
        "max_ping": max_ping,
        "avg_ping": avg_ping
    }

def get_test_groups():
    """Find and group related test files"""
    dl_groups = []
    ul_groups = []
    
    ping_files = glob.glob(os.path.join(DATA_DIR, "ping-*.log"))
    
    for ping_file in ping_files:
        basename = os.path.basename(ping_file)
        dir_match = re.search(r'ping-(dl|ul)-udp-(\d+M)\.log', basename)
        
        if dir_match:
            direction = dir_match.group(1)
            bandwidth = dir_match.group(2)
            
            cn_file = os.path.join(DATA_DIR, f"iperf-{direction}-udp-{bandwidth}-CN.json")
            ue_file = os.path.join(DATA_DIR, f"iperf-{direction}-udp-{bandwidth}-UE.json")
            
            if os.path.exists(cn_file) and os.path.exists(ue_file):
                if direction == "dl":
                    dl_groups.append((cn_file, ue_file, ping_file))
                else:  # ul
                    ul_groups.append((cn_file, ue_file, ping_file))
    
    return dl_groups, ul_groups

def plot_results(groups, direction):
    """Create plots for the given test groups and direction"""
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    sorted_groups = sorted(groups, key=lambda x: extract_bandwidth(os.path.basename(x[0])))
    
    results = []
    for cn_file, ue_file, ping_file in sorted_groups:
        result = analyze_test_group(cn_file, ue_file, ping_file)
        results.append(result)
    
    bandwidths = [r["target_bandwidth"] for r in results]
    min_pings = [r["min_ping"] for r in results]
    max_pings = [r["max_ping"] for r in results]
    avg_pings = [r["avg_ping"] for r in results]
    
    # Create figure for ping latency
    plt.figure(figsize=(15, 10))
    
    bar_width = 0.6
    x = np.arange(len(bandwidths))
    
    # Plot min to avg as one color
    plt.bar(x, [avg - min_val for avg, min_val in zip(avg_pings, min_pings)], 
            bottom=min_pings, width=bar_width, color='skyblue', label='Min to Avg Range')
    
    # Plot avg to max as another color
    plt.bar(x, [max_val - avg for max_val, avg in zip(max_pings, avg_pings)], 
            bottom=avg_pings, width=bar_width, color='lightcoral', label='Avg to Max Range')
    
    # Plot average line
    plt.plot(x, avg_pings, 'ko-', linewidth=2, label='Average Ping')
    
    # Add value labels
    for i, (min_val, avg_val, max_val) in enumerate(zip(min_pings, avg_pings, max_pings)):
        plt.text(i, min_val - 1, f"{min_val:.1f}", ha='center', fontsize=8)
        plt.text(i, avg_val, f"{avg_val:.1f}", ha='center', fontsize=8)
        plt.text(i, max_val + 1, f"{max_val:.1f}", ha='center', fontsize=8)
    
    plt.xticks(x, [f"{bw}M" for bw in bandwidths])
    plt.xlabel('Target Bandwidth (Mbps)', fontsize=12)
    plt.ylabel('Ping Latency (ms)', fontsize=12)
    
    # Set title and add test environment info
    direction_text = "Downlink" if direction == "dl" else "Uplink"
    plt.title(f'Ping Latency vs Bandwidth - UDP {direction_text}\nTest Environment: UDP {direction_text.upper()}', 
              fontsize=16)
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"ping_latency_{direction}_udp.png"), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main function to execute the analysis"""
    dl_groups, ul_groups = get_test_groups()
    
    if dl_groups:
        plot_results(dl_groups, "dl")
        print(f"Processed {len(dl_groups)} downlink test groups.")
    
    if ul_groups:
        plot_results(ul_groups, "ul")
        print(f"Processed {len(ul_groups)} uplink test groups.")
    
    print(f"Analysis complete. Output images saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
