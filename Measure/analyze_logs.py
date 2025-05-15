import argparse
import matplotlib.pyplot as plt
import numpy as np
import statistics
import pandas as pd
from datetime import datetime
import os
import seaborn as sns
import re

def calculate_timestamp_differences(vnf_path, pnf_path):
    vnf_timestamps = []
    pnf_timestamps = []
    
    # Enhanced timestamp parsing with regular expression
    timestamp_pattern = re.compile(r'^\[(\d+\.\d+)\]')
    
    # Read VNF timestamps with improved error handling
    try:
        with open(vnf_path, 'r') as vnf_file:
            for line in vnf_file:
                match = timestamp_pattern.search(line)
                if match:
                    try:
                        timestamp = float(match.group(1))
                        vnf_timestamps.append(timestamp)
                    except ValueError as e:
                        print(f"警告: 無法解析時間戳 '{match.group(1)}': {e}")
    except Exception as e:
        print(f"讀取VNF文件時出錯: {e}")
        return []
    
    # Read PNF timestamps with improved error handling
    try:
        with open(pnf_path, 'r') as pnf_file:
            for line in pnf_file:
                match = timestamp_pattern.search(line)
                if match:
                    try:
                        timestamp = float(match.group(1))
                        pnf_timestamps.append(timestamp)
                    except ValueError as e:
                        print(f"警告: 無法解析時間戳 '{match.group(1)}': {e}")
    except Exception as e:
        print(f"讀取PNF文件時出錯: {e}")
        return []
    
    # Print summary of timestamps read
    print(f"讀取到 {len(vnf_timestamps)} 條VNF時間戳和 {len(pnf_timestamps)} 條PNF時間戳")
    
    # Calculate differences between timestamps
    differences = []
    min_length = min(len(vnf_timestamps), len(pnf_timestamps))
    
    if min_length == 0:
        print("警告: 沒有找到匹配的時間戳")
        return []
        
    for i in range(min_length):
        diff = vnf_timestamps[i] - pnf_timestamps[i]
        differences.append((i+1, vnf_timestamps[i], pnf_timestamps[i], diff))
    
    return differences

def generate_output_filenames(vnf_path, pnf_path):
    # Extract base filenames without extensions
    vnf_base = os.path.splitext(os.path.basename(vnf_path))[0]
    pnf_base = os.path.splitext(os.path.basename(pnf_path))[0]
    
    # Create output directory if it doesn't exist
    output_dir = 'Measure'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{vnf_base}_vs_{pnf_base}" #_{timestamp}
    
    return {
        'report': f"{output_dir}/{base_name}_report.txt",
        'plot': f"{output_dir}/{base_name}_plot.png",
        'filtered_plot': f"{output_dir}/{base_name}_filtered_plot.png",
        'box_plot': f"{output_dir}/{base_name}_box_plot.png"
    }

def plot_timestamp_differences(differences, output_filename):
    # Extract data for plotting
    indices = [i for i, _, _, _ in differences]
    diffs_ms = [diff * 1000 for _, _, _, diff in differences]  # Convert to ms
    
    # Calculate statistics
    max_diff = max(diffs_ms)
    min_diff = min(diffs_ms)
    mean_diff = sum(diffs_ms) / len(diffs_ms)
    median_diff = statistics.median(diffs_ms)
    std_dev = statistics.stdev(diffs_ms)
    q1 = np.percentile(diffs_ms, 25)
    q3 = np.percentile(diffs_ms, 75)
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(indices, diffs_ms, 'b-', marker='o', markersize=3)  # Smaller marker size
    plt.title('VNF vs PNF Timestamp Differences')
    plt.xlabel('Packet Number')
    plt.ylabel('Time Difference (ms)')
    plt.grid(True)
    
    # Add a horizontal line for the average
    plt.axhline(y=mean_diff, color='r', linestyle='--', label=f'Mean: {mean_diff:.3f} ms')
    plt.axhline(y=median_diff, color='g', linestyle='-.', label=f'Median: {median_diff:.3f} ms')
    
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.show()
    
    # Print statistics
    print("\n統計資料:")
    print(f"最大值: {max_diff:.3f} ms")
    print(f"最小值: {min_diff:.3f} ms")
    print(f"平均值: {mean_diff:.3f} ms")
    print(f"中位數: {median_diff:.3f} ms")
    print(f"標準差: {std_dev:.3f} ms")
    print(f"第一四分位數 (Q1): {q1:.3f} ms")
    print(f"第三四分位數 (Q3): {q3:.3f} ms")
    
    return mean_diff

def plot_filtered_differences(differences, output_filename):
    # Extract data for plotting
    indices = [i for i, _, _, _ in differences]
    diffs_ms = [diff * 1000 for _, _, _, diff in differences]  # Convert to ms
    diffs_array = np.array(diffs_ms)
    
    # Calculate quartiles and IQR for outlier detection
    q1 = np.percentile(diffs_ms, 25)
    q3 = np.percentile(diffs_ms, 75)
    iqr = q3 - q1
    
    # Define outlier boundaries
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Filter out outliers
    filtered_data = []
    filtered_indices = []
    for i, diff in zip(indices, diffs_ms):
        if lower_bound <= diff <= upper_bound:
            filtered_data.append(diff)
            filtered_indices.append(i)
    
    if not filtered_data:
        print("沒有剩餘資料點，可能需要調整過濾標準。")
        return None
    
    # Calculate statistics for filtered data
    max_diff = max(filtered_data)
    min_diff = min(filtered_data)
    mean_diff = sum(filtered_data) / len(filtered_data)
    median_diff = statistics.median(filtered_data)
    std_dev = statistics.stdev(filtered_data) if len(filtered_data) > 1 else 0
    
    # Create the filtered plot
    plt.figure(figsize=(10, 6))
    plt.plot(filtered_indices, filtered_data, 'g-', marker='o', markersize=1)  # Smaller marker size
    plt.title('VNF vs PNF Timestamp Differences (Outliers Removed)')
    plt.xlabel('Packet Number')
    plt.ylabel('Time Difference (ms)')
    # plt.ylim(top=2)  # Fix y-axis maximum to 2
    plt.grid(True)
    
    # Add horizontal lines for mean and median
    plt.axhline(y=mean_diff, color='r', linestyle='--', label=f'Mean: {mean_diff:.3f} ms')
    plt.axhline(y=median_diff, color='b', linestyle='-.', label=f'Median: {median_diff:.3f} ms')
    
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.show()
    
    # Print filtered statistics
    print("\n過濾後統計資料 (排除異常值):")
    print(f"資料點數量: {len(filtered_data)} (原始: {len(diffs_ms)})")
    
    return {
        'raw': diffs_ms,
        'filtered': filtered_data,
        'stats': {
            'max': max_diff,
            'min': min_diff,
            'mean': mean_diff,
            'median': median_diff,
            'std_dev': std_dev,
            'q1': q1,
            'q3': q3,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        }
    }

def create_box_plot(data_dict, output_filename):
    """
    Create a detailed box plot to compare measurements.
    
    Args:
        data_dict: Dictionary with labels as keys and measurement data as values
        output_filename: Path to save the box plot image
    """
    plt.figure(figsize=(12, 8))
    
    # Extract only raw data
    if 'Raw Data' in data_dict:
        data = [data_dict['Raw Data']]
        labels = ['Raw Data']
    else:
        # Use all provided data
        data = list(data_dict.values())
        labels = list(data_dict.keys())
    
    # Create box plot with custom settings
    box_plot = plt.boxplot(
        data, 
        tick_labels=labels,  # Fix deprecated 'labels' parameter
        patch_artist=True,
        showmeans=True,              # Show mean values
        meanline=True,               # Show mean as a line
        showfliers=True,             # Show outliers
        meanprops={"color":"red", "linewidth":2},  # Mean line properties
        medianprops={"color":"blue", "linewidth":2},  # Median line properties
        flierprops={"marker":"o", "markerfacecolor":"red", "markersize":6}  # Outlier properties
    )
    
    # Customize colors
    colors = ['#8dd3c7', '#bebada', '#fb8072', '#80b1d3', '#fdb462']
    for patch, color in zip(box_plot['boxes'], colors[:len(data)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)  # Semi-transparent for better visualization
    
    # Set logarithmic scale for y-axis
    plt.yscale('log')
    
    plt.title('Time Difference Comparison (Logarithmic Scale Box Plot)', fontsize=16, pad=20)
    plt.xlabel('Measurement Groups', fontsize=14)
    plt.ylabel('Time Difference (ms, log scale)', fontsize=14)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    # Add annotations to explain box plot components in English
    components_text = (
        "Box Plot Components:\n"
        "• Box: Middle 50% of data (Q1 to Q3)\n"
        "• Blue Line: Median (Q2)\n"
        "• Red Line: Mean\n"
        "• Whiskers: Extend to min/max within 1.5*IQR\n"
        "• Red Dots: Outliers outside whisker range"
    )
    
    # Place annotation in a semi-transparent box
    plt.figtext(0.15, 0.01, components_text, ha='left', fontsize=10, 
                bbox={'facecolor':'white', 'alpha':0.8, 'pad':5, 'boxstyle':'round'})
    
    # Add statistics for raw data only
    stats_text = ""
    for label, values in data_dict.items():
        if label == 'Filtered Data':
            continue  # Skip filtered data statistics
            
        # Calculate key statistics
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        median = np.median(values)
        mean = np.mean(values)
        
        stats_text += f"{label}:\n"
        stats_text += f"  Median: {median:.3f} ms\n"
        stats_text += f"  Mean: {mean:.3f} ms\n"
        stats_text += f"  IQR: {iqr:.3f} ms\n"
        stats_text += f"  Outlier bounds: [{q1-1.5*iqr:.3f}, {q3+1.5*iqr:.3f}] ms\n\n"
    
    # Place statistics in a semi-transparent box on the right side
    plt.figtext(0.75, 0.25, stats_text, ha='left', fontsize=9, 
                bbox={'facecolor':'white', 'alpha':0.8, 'pad':5, 'boxstyle':'round'})
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # Adjust layout for annotations
    plt.savefig(output_filename, dpi=300)  # Higher resolution
    plt.show()
    
    print(f"Box plot saved to {output_filename}")

def generate_report(vnf_path, pnf_path, differences, report_path):
    # Convert differences to milliseconds for analysis
    diffs_ms = [diff * 1000 for _, _, _, diff in differences]
    
    # Create a pandas Series for advanced statistics
    diff_series = pd.Series(diffs_ms, name='diff')
    
    # Get first entries information
    first_vnf = differences[0][1] if differences else None
    first_pnf = differences[0][2] if differences else None
    initial_diff_ms = differences[0][3] * 1000 if differences else None
    
    # Calculate statistics
    stats = {
        'mean': np.mean(diffs_ms),
        'median': np.median(diffs_ms),
        'min': np.min(diffs_ms),
        'max': np.max(diffs_ms),
        'std': np.std(diffs_ms)
    }
    
    # Find extreme values
    highest_idx = np.argmax(diffs_ms)
    lowest_idx = np.argmin(diffs_ms)
    
    # Generate report
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"=== Latency Analysis Report ({current_time}) ===\n\n"
    report += f"VNF File: {vnf_path}\n"
    report += f"PNF File: {pnf_path}\n\n"
    
    report += f"VNF First Entry: timestamp={first_vnf:.7f}\n"
    report += f"PNF First Entry: timestamp={first_pnf:.7f}\n"
    report += f"Initial Time Difference: {initial_diff_ms:.4f} ms\n\n"
    
    report += "Statistical Analysis:\n"
    report += f"- Mean latency: {stats['mean']:.4f} ms\n"
    report += f"- Median latency: {stats['median']:.4f} ms\n"
    report += f"- Min latency: {stats['min']:.4f} ms\n"
    report += f"- Max latency: {stats['max']:.4f} ms\n"
    report += f"- Standard deviation: {stats['std']:.4f} ms\n\n"
    
    report += "Full Statistics (in ms):\n"
    report += str(diff_series.describe()) + "\n\n"
    
    report += "Extreme Values:\n"
    report += f"Highest latency - Index: {highest_idx+1}, Value: {diffs_ms[highest_idx]:.4f} ms\n"
    report += f"Lowest latency - Index: {lowest_idx+1}, Value: {diffs_ms[lowest_idx]:.4f} ms\n"
    
    # Save report to file with dynamic filename
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Print report to console
    # print(report)
    print(f"Report saved to {report_path}")
    
    return report_path

def main():
    parser = argparse.ArgumentParser(description="計算VNF與PNF時間戳的差值")
    parser.add_argument("vnf_path", help="VNF檔案路徑")
    parser.add_argument("pnf_path", help="PNF檔案路徑")
    args = parser.parse_args()

    differences = calculate_timestamp_differences(args.vnf_path, args.pnf_path)
    
    # Generate dynamic output filenames
    output_files = generate_output_filenames(args.vnf_path, args.pnf_path)
    
    # Generate comprehensive report
    generate_report(args.vnf_path, args.pnf_path, differences, output_files['report'])
    
    # Generate both plots
    plot_timestamp_differences(differences, output_files['plot'])
    filtered_data = plot_filtered_differences(differences, output_files['filtered_plot'])
    
    # Create box plot comparing raw and filtered data
    if filtered_data:
        data_dict = {
            'Raw Data': filtered_data['raw']
        }
        create_box_plot(data_dict, output_files['box_plot'])

if __name__ == "__main__":
    main()
