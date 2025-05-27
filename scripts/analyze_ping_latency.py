import os
import re
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

def parse_ping_log(file_path):
    """Parse ping log file and extract latency data"""
    latencies = []
    timestamps = []
    
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f):
                # Extract timestamp (epoch or relative time)
                timestamp = None
                
                # Format 1: Epoch timestamp at beginning
                epoch_match = re.match(r'^(\d{10})\D', line)
                if epoch_match:
                    timestamp = float(epoch_match.group(1))
                
                # Format 2: Bracketed timestamp [HH:MM:SS]
                time_match = re.search(r'\[([\d.:]+)\]', line)
                if time_match and not timestamp:
                    time_str = time_match.group(1)
                    time_components = time_str.split(':')
                    if len(time_components) >= 3:
                        hours, minutes, seconds = map(float, time_components)
                        timestamp = hours * 3600 + minutes * 60 + seconds
                
                # Default: use line number
                if timestamp is None:
                    timestamp = line_num
                
                # Extract ping time
                ping_match = re.search(r'time=([\d.]+) ms', line)
                if ping_match:
                    ping_time = float(ping_match.group(1))
                    latencies.append(ping_time)
                    timestamps.append(timestamp)
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'latency_ms': latencies
        })
    
    except Exception as e:
        print(f"Error parsing ping log {file_path}: {e}")
        return pd.DataFrame()

def get_ping_configs(data_dir):
    """Find all ping configuration files"""
    configs = []
    
    for file_path in data_dir.glob('ping*-*M.log'):
        # Extract bandwidth value
        match = re.search(r'-(\d+)M', file_path.name)
        if match:
            bandwidth_val = int(match.group(1))
            direction = 'dl' if 'dl' in file_path.name else 'ul'
            configs.append((bandwidth_val, direction, file_path))
    
    return sorted(configs, key=lambda x: x[0])

def calculate_quartile_stats(data):
    """Calculate comprehensive quartile statistics"""
    if len(data) == 0:
        return None
    
    q1 = np.percentile(data, 25)
    q2 = np.percentile(data, 50)  # Median
    q3 = np.percentile(data, 75)
    q4 = np.percentile(data, 100)  # Maximum
    
    # IQR and outlier boundaries
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Filter data to Q2-Q3 range for core analysis
    q2_q3_data = data[(data >= q2) & (data <= q3)]
    
    # Filter outliers using IQR method
    filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]
    
    return {
        'q1': q1,
        'q2': q2,
        'q3': q3,
        'q4': q4,
        'iqr': iqr,
        'mean': np.mean(data),
        'std': np.std(data),
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'outlier_count': len(data) - len(filtered_data),
        'q2_q3_data': q2_q3_data,
        'filtered_data': filtered_data,
        'raw_data': data
    }

def create_quartile_analysis_plot(results_dict, output_dir, direction):
    """Create comprehensive quartile analysis visualization"""
    
    # Set up the plotting style
    plt.style.use('seaborn-v0_8-whitegrid')
    fig = plt.figure(figsize=(20, 16))
    
    # Extract data for plotting
    bandwidths = sorted(results_dict.keys())
    labels = [f"{bw}M" for bw in bandwidths]
    
    # 1. Quartile Box Plot (Top Left)
    ax1 = plt.subplot(2, 3, (1, 2))
    
    box_data = [results_dict[bw]['raw_data'] for bw in bandwidths]
    
    # Create box plot with custom styling
    box_plot = ax1.boxplot(box_data, labels=labels, patch_artist=True, 
                          showfliers=False, widths=0.6)
    
    # Color the boxes with a gradient
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(bandwidths)))
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.set_xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Ping Latency (ms)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Ping Latency Distribution - {direction.upper()} UDP', 
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 2. Q2-Q3 Range Analysis (Top Right)
    ax2 = plt.subplot(2, 3, 3)
    
    q2_means = [np.mean(results_dict[bw]['q2_q3_data']) if len(results_dict[bw]['q2_q3_data']) > 0 else 0 
                for bw in bandwidths]
    q2_stds = [np.std(results_dict[bw]['q2_q3_data']) if len(results_dict[bw]['q2_q3_data']) > 1 else 0 
               for bw in bandwidths]
    
    bars = ax2.bar(labels, q2_means, yerr=q2_stds, capsize=5, 
                   color='lightcoral', alpha=0.8, edgecolor='black')
    
    # Add value labels
    for i, (mean_val, std_val) in enumerate(zip(q2_means, q2_stds)):
        ax2.text(i, mean_val + std_val + max(q2_means) * 0.02, 
                f'{mean_val:.1f}±{std_val:.1f}', 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax2.set_xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Q2-Q3 Range Analysis\n(Core Performance)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Outlier Analysis (Bottom Left)
    ax3 = plt.subplot(2, 3, 4)
    
    outlier_counts = [results_dict[bw]['outlier_count'] for bw in bandwidths]
    total_counts = [len(results_dict[bw]['raw_data']) for bw in bandwidths]
    outlier_percentages = [out/total*100 if total > 0 else 0 
                          for out, total in zip(outlier_counts, total_counts)]
    
    bars = ax3.bar(labels, outlier_percentages, color='orange', alpha=0.8, edgecolor='black')
    
    # Add percentage labels
    for i, pct in enumerate(outlier_percentages):
        ax3.text(i, pct + max(outlier_percentages) * 0.02, 
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax3.set_xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Outlier Percentage (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Outlier Distribution\n(IQR Method)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Statistical Summary Table (Bottom Center)
    ax4 = plt.subplot(2, 3, 5)
    ax4.axis('off')
    
    # Create summary table
    table_data = []
    for bw in bandwidths:
        stats = results_dict[bw]
        row = [
            f"{bw}M",
            f"{stats['q1']:.1f}",
            f"{stats['q2']:.1f}",
            f"{stats['q3']:.1f}",
            f"{stats['mean']:.1f}",
            f"{stats['std']:.1f}"
        ]
        table_data.append(row)
    
    table = ax4.table(
        cellText=table_data,
        colLabels=['BW', 'Q1', 'Q2', 'Q3', 'Mean', 'Std'],
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)
    ax4.set_title('Statistical Summary', fontsize=12, fontweight='bold', pad=20)
    
    # 5. Trend Analysis (Bottom Right)
    ax5 = plt.subplot(2, 3, 6)
    
    means = [results_dict[bw]['mean'] for bw in bandwidths]
    q2s = [results_dict[bw]['q2'] for bw in bandwidths]
    
    ax5.plot(bandwidths, means, 'o-', linewidth=2, markersize=6, 
            label='Mean Latency', color='red')
    ax5.plot(bandwidths, q2s, 's-', linewidth=2, markersize=6, 
            label='Median (Q2)', color='blue')
    
    ax5.set_xlabel('Bandwidth (Mbps)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax5.set_title('Latency Trend Analysis', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.legend()
    
    plt.tight_layout()
    output_file = output_dir / f'ping_latency_quartile_analysis_{direction}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return output_file

def create_filtered_box_plot(results_dict, output_dir, direction):
    """Create publication-quality box plot with filtered data"""
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    bandwidths = sorted(results_dict.keys())
    labels = [f"{bw}M" for bw in bandwidths]
    
    # 1. Raw Data Box Plot
    raw_data = [results_dict[bw]['raw_data'] for bw in bandwidths]
    
    box1 = ax1.boxplot(raw_data, labels=labels, patch_artist=True, 
                      showfliers=True, widths=0.6)
    
    # Color with gradient
    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(bandwidths)))
    for patch, color in zip(box1['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
    
    ax1.set_xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Ping Latency (ms)', fontsize=12, fontweight='bold')
    ax1.set_title('Raw Data Distribution\n(Including Outliers)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 2. Filtered Data Box Plot (Q2-Q3 Range)
    filtered_data = [results_dict[bw]['q2_q3_data'] for bw in bandwidths]
    
    box2 = ax2.boxplot(filtered_data, labels=labels, patch_artist=True, 
                      showfliers=False, widths=0.6)
    
    # Color with different gradient
    colors2 = plt.cm.Greens(np.linspace(0.4, 0.8, len(bandwidths)))
    for patch, color in zip(box2['boxes'], colors2):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
    
    ax2.set_xlabel('Bandwidth Configuration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Ping Latency (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Q2-Q3 Range Distribution\n(Core Performance)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = output_dir / f'ping_latency_filtered_boxplot_{direction}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return output_file

def analyze_ping_latency(data_dir=None):
    """Analyze ping latency data with quartile statistics"""
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
    
    print(f"Analyzing ping latency data from: {data_dir}")
    
    # Get all ping configurations
    ping_configs = get_ping_configs(data_dir)
    
    if not ping_configs:
        print("No ping configuration files found!")
        return
    
    # Group by direction
    dl_configs = [(bw, path) for bw, direction, path in ping_configs if direction == 'dl']
    ul_configs = [(bw, path) for bw, direction, path in ping_configs if direction == 'ul']
    
    # Process each direction
    for direction, configs in [('dl', dl_configs), ('ul', ul_configs)]:
        if not configs:
            continue
            
        print(f"\nProcessing {direction.upper()} configurations:")
        
        results_dict = {}
        
        for bandwidth, file_path in configs:
            print(f"  Processing {bandwidth}M: {file_path.name}")
            
            # Parse ping data
            ping_df = parse_ping_log(file_path)
            
            if ping_df.empty:
                print(f"    Warning: No valid ping data found")
                continue
            
            # Calculate quartile statistics
            stats = calculate_quartile_stats(ping_df['latency_ms'].values)
            
            if stats:
                results_dict[bandwidth] = stats
                print(f"    Q1: {stats['q1']:.2f}ms, Q2: {stats['q2']:.2f}ms, Q3: {stats['q3']:.2f}ms")
                print(f"    Mean: {stats['mean']:.2f}ms, Outliers: {stats['outlier_count']}")
        
        if results_dict:
            # Create visualizations
            quartile_file = create_quartile_analysis_plot(results_dict, output_dir, direction)
            boxplot_file = create_filtered_box_plot(results_dict, output_dir, direction)
            
            print(f"\n{direction.upper()} analysis complete:")
            print(f"  Quartile analysis: {quartile_file}")
            print(f"  Filtered box plot: {boxplot_file}")

if __name__ == "__main__":
    # Check if data directory is provided as command line argument
    if len(sys.argv) > 1:
        data_directory = sys.argv[1]
        analyze_ping_latency(data_directory)
    else:
        analyze_ping_latency()
