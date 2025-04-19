import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import glob

# Define the base directories
BASE_DATA_DIR = "/home/ming/E2E-network-measurement/data"
BASE_OUTPUT_DIR = "/home/ming/E2E-network-measurement/results"

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

def extract_target_throughput(filename):
    """Extract target throughput value from filename"""
    match = re.search(r'udp-(\d+M)', filename)
    if match:
        bw_str = match.group(1)
        if bw_str.endswith('M'):
            return int(bw_str[:-1])
    return 0

def analyze_test_group(cn_file, ue_file, ping_file):
    """Analyze one test group (CN, UE, ping) to calculate throughput and latency statistics"""
    target_throughput = extract_target_throughput(os.path.basename(cn_file))
    
    cn_data = parse_iperf_json(cn_file)
    ue_data = parse_iperf_json(ue_file)
    ping_data = parse_ping_log(ping_file)
    
    cn_throughput = cn_data["throughput"].mean() if not cn_data.empty else 0
    ue_throughput = ue_data["throughput"].mean() if not ue_data.empty else 0
    
    min_ping = ping_data["ping_time"].min() if not ping_data.empty else 0
    max_ping = ping_data["ping_time"].max() if not ping_data.empty else 0
    avg_ping = ping_data["ping_time"].mean() if not ping_data.empty else 0
    
    return {
        "target_throughput": target_throughput,
        "cn_throughput": cn_throughput,
        "ue_throughput": ue_throughput,
        "min_ping": min_ping,
        "max_ping": max_ping,
        "avg_ping": avg_ping
    }

def get_test_groups(data_dir):
    """Find and group related test files within the specified data directory"""
    dl_groups = []
    ul_groups = []
    
    ping_files = glob.glob(os.path.join(data_dir, "ping-*.log"))
    
    for ping_file in ping_files:
        basename = os.path.basename(ping_file)
        dir_match = re.search(r'ping-(dl|ul)-udp-(\d+M)\.log', basename)
        
        if dir_match:
            direction = dir_match.group(1)
            bandwidth_label = dir_match.group(2)
            
            cn_file = os.path.join(data_dir, f"iperf-{direction}-udp-{bandwidth_label}-CN.json")
            ue_file = os.path.join(data_dir, f"iperf-{direction}-udp-{bandwidth_label}-UE.json")
            
            if os.path.exists(cn_file) and os.path.exists(ue_file):
                if direction == "dl":
                    dl_groups.append((cn_file, ue_file, ping_file))
                else:  # ul
                    ul_groups.append((cn_file, ue_file, ping_file))
    
    return dl_groups, ul_groups

def plot_results(groups, direction, output_dir):
    """Create plots for the given test groups and direction, saving to the specified output directory"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    sorted_groups = sorted(groups, key=lambda x: extract_target_throughput(os.path.basename(x[0])))
    
    results = []
    for cn_file, ue_file, ping_file in sorted_groups:
        result = analyze_test_group(cn_file, ue_file, ping_file)
        results.append(result)
    
    target_throughputs = [r["target_throughput"] for r in results]
    min_pings = [r["min_ping"] for r in results]
    max_pings = [r["max_ping"] for r in results]
    avg_pings = [r["avg_ping"] for r in results]
    
    # Create figure for ping latency
    plt.figure(figsize=(15, 10))
    
    bar_width = 0.6
    x = np.arange(len(target_throughputs))
    
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
    
    plt.xticks(x, [f"{bw}M" for bw in target_throughputs])
    plt.xlabel('Target Throughput (Mbps)', fontsize=12)
    plt.ylabel('Ping Latency (ms)', fontsize=12)
    
    # Set title and add test environment info
    direction_text = "Downlink" if direction == "dl" else "Uplink"
    plt.title(f'Ping Latency vs Target Throughput - UDP {direction_text}\nTest Environment: UDP {direction_text.upper()}', 
              fontsize=16)
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"ping_latency_{direction}_udp.png"), dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main function to execute the analysis"""
    
    # Find available data directories
    try:
        available_dirs = sorted([d for d in os.listdir(BASE_DATA_DIR) if os.path.isdir(os.path.join(BASE_DATA_DIR, d))])
    except FileNotFoundError:
        print(f"Error: Base data directory not found: {BASE_DATA_DIR}")
        return
        
    if not available_dirs:
        print(f"No data directories found in {BASE_DATA_DIR}")
        return

    # Prompt user to select a directory
    print("Available data directories:")
    for i, dir_name in enumerate(available_dirs):
        print(f"{i + 1}: {dir_name}")

    while True:
        try:
            choice = input(f"Select a directory number (1-{len(available_dirs)}): ")
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(available_dirs):
                selected_dir_name = available_dirs[choice_index]
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Set DATA_DIR and OUTPUT_DIR based on selection
    DATA_DIR = os.path.join(BASE_DATA_DIR, selected_dir_name)
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, selected_dir_name)
    
    print(f"\nAnalyzing data from: {DATA_DIR}")
    print(f"Saving results to: {OUTPUT_DIR}")

    dl_groups, ul_groups = get_test_groups(DATA_DIR)
    
    if dl_groups:
        plot_results(dl_groups, "dl", OUTPUT_DIR)
        print(f"Processed {len(dl_groups)} downlink test groups.")
    
    if ul_groups:
        plot_results(ul_groups, "ul", OUTPUT_DIR)
        print(f"Processed {len(ul_groups)} uplink test groups.")
        
    if not dl_groups and not ul_groups:
        print("No valid test groups found in the selected directory.")
    else:
        print(f"\nAnalysis complete. Output images saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
