import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import glob
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Define the base directories
BASE_DATA_DIR = "/home/ming/E2E-network-measurement/data"
BASE_OUTPUT_DIR = "/home/ming/E2E-network-measurement/results"
# Define buffer time in seconds to exclude from start/end of ping data
PING_BUFFER_SECONDS = 5  # Adjust as needed

def parse_iperf_json(file_path):
    """Parse iperf JSON files to extract comprehensive throughput data"""
    try:
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON from {file_path}: {e}")
                return None
        
        intervals_data = []
        
        if "intervals" in data:
            for interval in data.get("intervals", []):
                for stream in interval.get("streams", []):
                    # Extract all relevant metrics
                    throughput = stream.get("bits_per_second", 0) / 1_000_000  # Convert to Mbps
                    jitter = stream.get("jitter_ms", 0)
                    lost_packets = stream.get("lost_packets", 0)
                    packets = stream.get("packets", 0)
                    lost_percent = stream.get("lost_percent", 0)
                    
                    # Try different ways to get start/end time
                    start_time = stream.get("start", 0)
                    if start_time == 0:
                        start_time = interval.get("start", 0)
                        if isinstance(start_time, dict):
                            start_time = 0
                            
                    end_time = stream.get("end", 0)
                    if end_time == 0:
                        end_time = interval.get("end", 0)
                        if isinstance(end_time, dict):
                            end_time = 0
                    
                    interval_info = {
                        "throughput": throughput,
                        "jitter_ms": jitter,
                        "lost_packets": lost_packets,
                        "packets": packets,
                        "lost_percent": lost_percent,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                    intervals_data.append(interval_info)
        
        # Extract CPU info if available
        cpu_info = {}
        if "end" in data and "cpu_utilization_percent" in data["end"]:
            cpu_info = data["end"]["cpu_utilization_percent"]
        
        # Calculate summary statistics (excluding high loss intervals)
        all_throughputs = [item["throughput"] for item in intervals_data if item.get("lost_percent", 100) < 5]
        
        if not all_throughputs:
            # If all intervals have high loss, include them all
            all_throughputs = [item["throughput"] for item in intervals_data]
        
        summary = {
            "min_throughput": min(all_throughputs) if all_throughputs else 0,
            "max_throughput": max(all_throughputs) if all_throughputs else 0,
            "avg_throughput": sum(all_throughputs) / len(all_throughputs) if all_throughputs else 0,
            "intervals": intervals_data,
            "cpu_utilization": cpu_info
        }
        
        return summary
        
    except Exception as e:
        print(f"Error processing iperf file {file_path}: {e}")
        return None

def parse_ping_log(file_path):
    """Parse ping log files to extract timestamped latency data"""
    ping_data = []
    start_time = None
    line_count = 0
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line_count += 1
                
                # Try to extract timestamp in different formats
                timestamp = None
                
                # Format 1: Epoch timestamp at beginning of line
                epoch_match = re.match(r'^(\d{10})\D', line)
                if epoch_match:
                    timestamp = float(epoch_match.group(1)) - start_time if start_time else 0
                    if start_time is None:
                        start_time = float(epoch_match.group(1))
                
                # Format 2: Bracketed timestamp [HH:MM:SS]
                time_match = re.search(r'\[([\d.:]+)\]', line)
                if time_match and not timestamp:
                    time_str = time_match.group(1)
                    time_components = time_str.split(':')
                    if len(time_components) >= 3:  # HH:MM:SS format
                        hours, minutes, seconds = map(float, time_components)
                        timestamp = hours * 3600 + minutes * 60 + seconds
                        if start_time is None:
                            start_time = timestamp
                        timestamp = timestamp - start_time
                
                # Format 3: No timestamp, use line number
                if timestamp is None:
                    timestamp = line_count
                
                # Extract ping time
                ping_match = re.search(r'time=([\d.]+) ms', line)
                if ping_match:
                    ping_time = float(ping_match.group(1))
                    ping_data.append({
                        "timestamp": timestamp,
                        "ping_ms": ping_time
                    })
        
        if len(ping_data) == 0:
            print(f"Warning: No ping data extracted from {file_path}")
            # Print first few lines of the file for debugging
            with open(file_path, 'r') as f:
                print("File content preview:")
                for i, line in enumerate(f):
                    if i < 5:  # Show first 5 lines
                        print(f"  {line.strip()}")
                    else:
                        break
                print("...")
    
    except Exception as e:
        print(f"Error parsing ping log {file_path}: {e}")
    
    return ping_data

def get_test_groups(data_dir):
    """Find and group related test files within the specified data directory"""
    dl_groups = []
    ul_groups = []
    
    # Debug: Print all files in the directory to help identify the issue
    all_files = os.listdir(data_dir)
    print(f"\nFiles found in {data_dir}: {len(all_files)} files")
    
    # Print some example filenames
    print("\nExample files:")
    for i, filename in enumerate(all_files):
        if i < 5:
            print(f"  {filename}")
    print("  ...")
    
    # List all files to see patterns
    iperf_files = [f for f in all_files if f.endswith('.json') and 'iperf' in f]
    ping_files = [f for f in all_files if f.endswith('.log') and 'ping' in f]
    
    print(f"Found {len(iperf_files)} iperf JSON files")
    print(f"Found {len(ping_files)} ping log files")
    
    # Count files by type
    ue_files = [f for f in iperf_files if 'UE' in f]
    cn_files = [f for f in iperf_files if 'CN' in f]
    
    print(f"\nFound {len(cn_files)} CN files and {len(ue_files)} UE files")
    
    # Handle the case where we only have UE files (no CN files)
    # In this case, we'll create "dummy" CN files by duplicating the UE files
    use_dummy_cn = len(cn_files) == 0 and len(ue_files) > 0
    if use_dummy_cn:
        print("No CN files found. Using UE files as both CN and UE endpoints.")
    
    # Extract all unique bandwidths
    bandwidths = set()
    for f in all_files:
        bw_match = re.search(r'(\d+M)', f)
        if bw_match:
            bandwidths.add(bw_match.group(1))
    
    # For each bandwidth, try to form a test group
    for bw in sorted(bandwidths):
        print(f"Looking for files with bandwidth {bw}")
        
        # Find UE file
        ue_file = None
        for f in all_files:
            if f.endswith('.json') and 'UE' in f and bw in f:
                ue_file = os.path.join(data_dir, f)
                print(f"  Found UE file: {f}")
                break
                
        # Find CN file or use UE file as placeholder
        cn_file = None
        if use_dummy_cn and ue_file:
            cn_file = ue_file  # Use UE file as CN file
            print(f"  Using UE file as CN file")
        else:
            for f in all_files:
                if f.endswith('.json') and 'CN' in f and bw in f:
                    cn_file = os.path.join(data_dir, f)
                    print(f"  Found CN file: {f}")
                    break
                    
        # Find ping file
        ping_file = None
        for f in all_files:
            if f.endswith('.log') and 'ping' in f and bw in f:
                ping_file = os.path.join(data_dir, f)
                print(f"  Found ping file: {f}")
                break
                
        # If we have all necessary files, form a test group
        if ue_file and (cn_file or use_dummy_cn) and ping_file:
            # If we're using dummy CN files, ensure cn_file is set
            if use_dummy_cn:
                cn_file = ue_file
                
            # Determine direction
            direction = 'dl'  # Default
            dir_match = re.search(r'(dl|ul)', os.path.basename(ping_file))
            if dir_match:
                direction = dir_match.group(1)
                
            print(f"  Complete group found for {bw} ({direction})")
            
            if direction == 'dl':
                dl_groups.append((cn_file, ue_file, ping_file))
                print(f"  Added DL group: {bw}")
            else:
                ul_groups.append((cn_file, ue_file, ping_file))
                print(f"  Added UL group: {bw}")
                
    print(f"\nFound {len(dl_groups)} DL groups and {len(ul_groups)} UL groups")
    return dl_groups, ul_groups

def extract_target_throughput(filename):
    """Extract target throughput value from filename"""
    match = re.search(r'udp-(\d+M)', filename)
    if match:
        bw_str = match.group(1)
        if bw_str.endswith('M'):
            return int(bw_str[:-1])
    
    # If the standard pattern fails, try a more flexible approach
    match = re.search(r'(\d+)M', filename)
    if match:
        return int(match.group(1))
    
    return 0

def correlate_throughput_ping(throughput_data, ping_data, ping_file):
    """Correlate throughput and ping data by timestamp"""
    # Create a dataframe with ping data
    ping_df = pd.DataFrame(ping_data)
    
    if ping_df.empty:
        print(f"Warning: No ping data in {ping_file}")
        return pd.DataFrame()
    
    # Get the test duration from throughput intervals
    if not throughput_data or "intervals" not in throughput_data or not throughput_data["intervals"]:
        print(f"Warning: No throughput intervals found")
        return ping_df  # Return just ping data
    
    # Get the total test duration
    start_time = 0
    end_time = max([interval["end_time"] for interval in throughput_data["intervals"]])
    
    # Mark each ping data point as being in buffer or test period
    ping_df["in_test_period"] = ping_df["timestamp"].apply(
        lambda t: start_time + PING_BUFFER_SECONDS <= t <= end_time - PING_BUFFER_SECONDS
    )
    
    return ping_df

def plot_detailed_test_results(result, direction, output_dir):
    """Create detailed plots for a single test showing ping vs throughput over time"""
    target_throughput = result["target_throughput"]
    
    # Create figure with two subplots sharing x-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)
    
    # Plot ping data on top subplot
    ping_df = result["correlated_ping_data"]
    
    if ping_df.empty:
        print(f"Warning: No ping data to plot for {direction} {target_throughput}M")
        plt.close()
        return
    
    test_period = ping_df[ping_df["in_test_period"]]
    buffer_period = ping_df[~ping_df["in_test_period"]]
    
    # Plot test period and buffer period with different styles
    if not test_period.empty:
        ax1.plot(test_period["timestamp"], test_period["ping_ms"], 'b.-', label='Test Period')
    if not buffer_period.empty:
        ax1.plot(buffer_period["timestamp"], buffer_period["ping_ms"], 'r.--', alpha=0.5, label='Buffer Period')
    
    # Add buffer zone indicators
    if not ping_df.empty:
        min_time = ping_df["timestamp"].min()
        max_time = ping_df["timestamp"].max()
        buffer_start = min_time + PING_BUFFER_SECONDS
        buffer_end = max_time - PING_BUFFER_SECONDS
        
        # Add vertical lines for buffer zones
        ax1.axvline(x=buffer_start, color='r', linestyle='--', alpha=0.7)
        ax1.axvline(x=buffer_end, color='r', linestyle='--', alpha=0.7)
        
        # Add labels
        ax1.text(buffer_start + 0.5, ax1.get_ylim()[1] * 0.9, 'Test Start', rotation=90)
        ax1.text(buffer_end + 0.5, ax1.get_ylim()[1] * 0.9, 'Test End', rotation=90)
    
    ax1.set_title(f'{direction.upper()} UDP {target_throughput}M - Ping Latency Over Time', fontsize=14)
    ax1.set_ylabel('Ping Latency (ms)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()
    
    # Plot throughput data on bottom subplot
    cn_intervals = result.get("cn_intervals", [])
    ue_intervals = result.get("ue_intervals", [])
    
    if cn_intervals:
        # CN throughput
        cn_times = [interval["start_time"] for interval in cn_intervals]
        cn_throughputs = [interval["throughput"] for interval in cn_intervals]
        ax2.plot(cn_times, cn_throughputs, 'g.-', label='CN Throughput')
    
    if ue_intervals:
        # UE throughput
        ue_times = [interval["start_time"] for interval in ue_intervals]
        ue_throughputs = [interval["throughput"] for interval in ue_intervals]
        ax2.plot(ue_times, ue_throughputs, 'b.-', label='UE Throughput')
    
    # Add target throughput reference line
    ax2.axhline(y=target_throughput, color='r', linestyle='-', alpha=0.7, label='Target Throughput')
    
    # Same buffer zone lines on throughput plot
    if not ping_df.empty:
        ax2.axvline(x=buffer_start, color='r', linestyle='--', alpha=0.7)
        ax2.axvline(x=buffer_end, color='r', linestyle='--', alpha=0.7)
    
    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_ylabel('Throughput (Mbps)', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{direction}_udp_{target_throughput}M_detailed.png"), dpi=300, bbox_inches='tight')
    plt.close()

def analyze_test_group(cn_file, ue_file, ping_file):
    """Analyze one test group (CN, UE, ping) to calculate throughput and latency statistics"""
    target_throughput = extract_target_throughput(os.path.basename(ue_file))  # Use UE file for target
    
    print(f"Analyzing test group with target throughput {target_throughput}M")
    print(f"  UE file: {os.path.basename(ue_file)}")
    if cn_file != ue_file:
        print(f"  CN file: {os.path.basename(cn_file)}")
    else:
        print(f"  CN file: [using UE file]")
    print(f"  Ping file: {os.path.basename(ping_file)}")
    
    # Parse the JSON files - if CN file is the same as UE file, only parse once
    if cn_file == ue_file:
        ue_data = parse_iperf_json(ue_file)
        cn_data = ue_data  # Use the same data for both
    else:
        ue_data = parse_iperf_json(ue_file)
        cn_data = parse_iperf_json(cn_file)
        
    ping_data = parse_ping_log(ping_file)
    
    # Skip if any data is missing
    if not ue_data:
        print(f"  Error: Failed to parse UE data from {os.path.basename(ue_file)}")
        return None
    
    # Correlate ping data with throughput test periods
    correlated_ping_df = correlate_throughput_ping(ue_data, ping_data, ping_file)
    
    # Calculate statistics for ping data during test period
    test_period_ping = correlated_ping_df[correlated_ping_df["in_test_period"]] if not correlated_ping_df.empty else pd.DataFrame()
    
    if test_period_ping.empty:
        print(f"  Warning: No ping data within test period for {os.path.basename(ping_file)}")
        min_ping, max_ping, avg_ping = 0, 0, 0
    else:
        min_ping = test_period_ping["ping_ms"].min()
        max_ping = test_period_ping["ping_ms"].max()
        avg_ping = test_period_ping["ping_ms"].mean()
        print(f"  Ping stats: min={min_ping:.2f}ms, avg={avg_ping:.2f}ms, max={max_ping:.2f}ms")
    
    # Extract comprehensive test info
    result = {
        "target_throughput": target_throughput,
        "cn_avg_throughput": cn_data["avg_throughput"],
        "cn_min_throughput": cn_data["min_throughput"],
        "cn_max_throughput": cn_data["max_throughput"],
        "ue_avg_throughput": ue_data["avg_throughput"],
        "ue_min_throughput": ue_data["min_throughput"],
        "ue_max_throughput": ue_data["max_throughput"],
        "min_ping": min_ping,
        "max_ping": max_ping,
        "avg_ping": avg_ping,
        "correlated_ping_data": correlated_ping_df,
        "cn_intervals": cn_data["intervals"],
        "ue_intervals": ue_data["intervals"],
        "cn_cpu": cn_data.get("cpu_utilization", {}),
        "ue_cpu": ue_data.get("cpu_utilization", {})
    }
    
    print(f"  Analysis complete: UE avg={ue_data['avg_throughput']:.2f}Mbps")
    
    return result

def plot_results(groups, direction, output_dir):
    """Create plots for the given test groups and direction, saving to the specified output directory"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nProcessing {len(groups)} {direction} test groups:")
    
    # Debug: Show what groups we have
    for i, (cn_file, ue_file, ping_file) in enumerate(groups):
        bw = extract_target_throughput(os.path.basename(ue_file))
        print(f"  Group {i+1}: {bw}M")
        print(f"    UE: {os.path.basename(ue_file)}")
        if cn_file != ue_file:
            print(f"    CN: {os.path.basename(cn_file)}")
        else:
            print("    CN: [using UE file]")
        print(f"    Ping: {os.path.basename(ping_file)}")
    
    # Sort by bandwidth
    try:
        sorted_groups = sorted(groups, key=lambda x: extract_target_throughput(os.path.basename(x[1])))
    except Exception as e:
        print(f"Error sorting groups: {e}")
        sorted_groups = groups
    
    # Analyze each group
    results = []
    for cn_file, ue_file, ping_file in sorted_groups:
        try:
            result = analyze_test_group(cn_file, ue_file, ping_file)
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error analyzing group: {e}")
    
    if not results:
        print(f"No valid test results to plot for {direction} direction")
        return
    
    # Extract data for summary plot
    target_throughputs = [r["target_throughput"] for r in results]
    min_pings = [r["min_ping"] for r in results]
    max_pings = [r["max_ping"] for r in results]
    avg_pings = [r["avg_ping"] for r in results]
    
    # Create figure for ping latency summary
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
    
    # Create detailed plots for each test case
    for result in results:
        try:
            plot_detailed_test_results(result, direction, output_dir)
        except Exception as e:
            print(f"Error creating detailed plot: {e}")
        
    # Create comprehensive comparison table/plot
    create_comparison_table(results, direction, output_dir)

def create_comparison_table(results, direction, output_dir):
    """Create a comprehensive comparison table/plot of all test results"""
    # Extract data for table
    data = []
    for r in results:
        row = {
            "Target (Mbps)": r["target_throughput"],
            "CN Avg (Mbps)": round(r["cn_avg_throughput"], 2),
            "CN Min (Mbps)": round(r["cn_min_throughput"], 2),
            "CN Max (Mbps)": round(r["cn_max_throughput"], 2),
            "UE Avg (Mbps)": round(r["ue_avg_throughput"], 2),
            "UE Min (Mbps)": round(r["ue_min_throughput"], 2),
            "UE Max (Mbps)": round(r["ue_max_throughput"], 2),
            "Ping Avg (ms)": round(r["avg_ping"], 2),
            "Ping Min (ms)": round(r["min_ping"], 2),
            "Ping Max (ms)": round(r["max_ping"], 2),
            "Host CPU (%)": round(r["cn_cpu"].get("host_total", 0), 2),
            "Remote CPU (%)": round(r["ue_cpu"].get("remote_total", 0), 2)
        }
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save as CSV
    csv_path = os.path.join(output_dir, f"{direction}_udp_comparison.csv")
    df.to_csv(csv_path, index=False)
    
    # Create visualization of key metrics
    fig, axes = plt.subplots(2, 2, figsize=(20, 15))
    
    # Throughput comparison
    axes[0, 0].plot(df["Target (Mbps)"], df["CN Avg (Mbps)"], 'go-', label='CN Throughput')
    axes[0, 0].plot(df["Target (Mbps)"], df["UE Avg (Mbps)"], 'bo-', label='UE Throughput')
    axes[0, 0].plot(df["Target (Mbps)"], df["Target (Mbps)"], 'r--', label='Target')
    axes[0, 0].set_xlabel('Target Throughput (Mbps)')
    axes[0, 0].set_ylabel('Achieved Throughput (Mbps)')
    axes[0, 0].set_title('Throughput Comparison')
    axes[0, 0].grid(True)
    axes[0, 0].legend()
    
    # Ping latency vs throughput
    axes[0, 1].plot(df["Target (Mbps)"], df["Ping Avg (ms)"], 'ko-', label='Average Ping')
    axes[0, 1].fill_between(df["Target (Mbps)"], df["Ping Min (ms)"], df["Ping Max (ms)"], 
                          color='lightgray', alpha=0.5, label='Min-Max Range')
    axes[0, 1].set_xlabel('Target Throughput (Mbps)')
    axes[0, 1].set_ylabel('Ping Latency (ms)')
    axes[0, 1].set_title('Ping Latency vs Throughput')
    axes[0, 1].grid(True)
    axes[0, 1].legend()
    
    # CPU utilization
    axes[1, 0].plot(df["Target (Mbps)"], df["Host CPU (%)"], 'mo-', label='Host CPU')
    axes[1, 0].plot(df["Target (Mbps)"], df["Remote CPU (%)"], 'co-', label='Remote CPU')
    axes[1, 0].set_xlabel('Target Throughput (Mbps)')
    axes[1, 0].set_ylabel('CPU Utilization (%)')
    axes[1, 0].set_title('CPU Utilization vs Throughput')
    axes[1, 0].grid(True)
    axes[1, 0].legend()
    
    # Throughput efficiency
    efficiency = df["UE Avg (Mbps)"] / df["Target (Mbps)"] * 100
    axes[1, 1].bar(df["Target (Mbps)"].astype(str) + "M", efficiency, color='royalblue')
    axes[1, 1].axhline(y=100, color='r', linestyle='--')
    for i, v in enumerate(efficiency):
        axes[1, 1].text(i, v + 1, f"{v:.1f}%", ha='center')
    axes[1, 1].set_xlabel('Target Throughput (Mbps)')
    axes[1, 1].set_ylabel('Efficiency (%)')
    axes[1, 1].set_title('Throughput Efficiency (UE/Target)')
    axes[1, 1].grid(True, axis='y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{direction}_udp_metrics_comparison.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved comparison data to {csv_path}")

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
