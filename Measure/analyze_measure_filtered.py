import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Function to parse timestamp from log line
def parse_timestamp(line):
    timestamp_str = line.split(']')[0].strip('[')
    return float(timestamp_str)

# Function to extract suffix from stop line
def get_suffix(line):
    return line.split('stop-')[1].split()[0]

# Function to process a single log file
def process_log_file(filepath):
    pairs = {}
    timestamps = {}  # Store timestamps for each measurement
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        if 'start' in lines[i]:
            start_time = parse_timestamp(lines[i])
            frame_slot = re.search(r'frame=(\d+) slot=(\d+)', lines[i]).group()
            i += 1
            while i < len(lines) and 'stop' in lines[i]:
                stop_time = parse_timestamp(lines[i])
                suffix = get_suffix(lines[i])
                if suffix not in pairs:
                    pairs[suffix] = []
                    timestamps[suffix] = []
                # Convert to microseconds
                time_diff = (stop_time - start_time) * 1_000_000
                pairs[suffix].append(time_diff)
                timestamps[suffix].append((start_time, stop_time))
                i += 1
        else:
            i += 1
    return pairs, timestamps

# Function to calculate averages
def calculate_averages(pairs):
    averages = {}
    for suffix, times in pairs.items():
        averages[suffix] = np.mean(times) if times else 0
    return averages

# Function to plot averages with data count background
def plot_averages_with_count(pairs, averages, mode, output_path):
    plt.style.use('default')
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    suffixes = list(averages.keys())
    # Format x-axis labels to uppercase
    formatted_suffixes = [suffix.upper() for suffix in suffixes]
    counts = [len(pairs[suffix]) for suffix in suffixes]
    avg_values = [averages[suffix] for suffix in suffixes]
    
    # Create second y-axis for averages (left side)
    ax2 = ax1.twinx()
    
    # Create bar chart for data counts (background) - more visible
    bars = ax1.bar(formatted_suffixes, counts, alpha=0.6, color='#e0e0e0', 
                   label='Data Count', edgecolor='#999999', linewidth=1)
    
    # Plot averages on left axis
    points = ax2.scatter(formatted_suffixes, avg_values, color='#d62728', s=120, 
                        label='Average Time', zorder=5, alpha=0.9, edgecolors='white', linewidth=1)
    
    # Swap axes - averages on left, counts on right
    ax1.set_ylabel('Data Count', fontsize=12, color='#666666')
    ax2.set_ylabel('Average Time (µs)', fontsize=12, color='#d62728')
    ax1.yaxis.set_label_position('right')
    ax2.yaxis.set_label_position('left')
    ax1.yaxis.tick_right()
    ax2.yaxis.tick_left()
    
    ax1.set_xlabel('Measurement Type', fontsize=12, color='#333333')
    ax1.tick_params(axis='y', labelcolor='#666666', labelsize=10, right=True, left=False)
    ax2.tick_params(axis='y', labelcolor='#d62728', labelsize=10, left=True, right=False)
    # Remove rotation for x-axis labels
    ax1.tick_params(axis='x', labelsize=10, rotation=0)
    
    # Set fixed y-axis limits instead of dynamic scaling
    max_count = max(counts) if counts else 100
    max_avg = max(avg_values) if avg_values else 1000
    ax1.set_ylim(0, max_count * 1.1)  # Fixed height with 10% margin
    ax2.set_ylim(0, max_avg * 1.1)    # Fixed height with 10% margin
    
    # Title
    ax1.set_title(f'Data Distribution and Average Times ({mode} Mode)', 
                  fontsize=14, pad=40, color='#333333', fontweight='normal')
    
    # Remove spines
    ax1.spines['top'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax1.spines['right'].set_color('#cccccc')
    ax1.spines['bottom'].set_color('#cccccc')
    ax2.spines['left'].set_color('#cccccc')
    
    # Grid
    ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.set_axisbelow(True)
    
    # Legends - positioned above the plot area but below title
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', 
               bbox_to_anchor=(0.5, 1.05), ncol=2, frameon=True, fancybox=False, shadow=False, framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

# Function to filter outliers and write them to log file
def filter_outliers(pairs, timestamps, threshold_us=60, log_file=None):
    filtered_pairs = {}
    outliers = {}
        
    for suffix, data in pairs.items():
        filtered_data = []
        suffix_outliers = []
        
        for i, value in enumerate(data):
            if value > threshold_us:
                start_time, stop_time = timestamps[suffix][i]
                suffix_outliers.append((i, value, start_time, stop_time))
            else:
                filtered_data.append(value)
        
        filtered_pairs[suffix] = filtered_data
        if suffix_outliers:
            outliers[suffix] = suffix_outliers
    
    return filtered_pairs, outliers

# Function to write outliers to log file
def write_outliers_to_log(outliers, mode, log_file):
    if outliers:
        log_file.write(f"\nOutliers found in {mode} mode:\n")
        for suffix, suffix_outliers in outliers.items():
            log_file.write(f"  {suffix}:\n")
            for idx, value, start_time, stop_time in suffix_outliers:
                log_file.write(f"    Index {idx}: {value:.2f} µs ({value/1000:.2f} ms)\n")
                log_file.write(f"      Start timestamp: {start_time:.6f}\n")
                log_file.write(f"      Stop timestamp: {stop_time:.6f}\n")

# Function to plot raw data line charts (combined)
def plot_raw_data(pairs, timestamps, mode, output_path, log_file=None):
    # Filter outliers
    filtered_pairs, outliers = filter_outliers(pairs, timestamps)
    
    # Write outliers to log file instead of printing
    if log_file:
        write_outliers_to_log(outliers, mode, log_file)
    
    plt.style.use('default')
    
    # Create subplots for each suffix
    suffixes = list(filtered_pairs.keys())
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # Calculate global y-axis limits for consistency
    all_values = []
    for data in filtered_pairs.values():
        all_values.extend(data)
    
    if all_values:
        global_min = min(all_values)
        global_max = max(all_values)
        y_margin = (global_max - global_min) * 0.05  # 5% margin
        global_ylim = (global_min - y_margin, global_max + y_margin)
    else:
        global_ylim = (0, 1000)  # Default range
    
    for i, suffix in enumerate(suffixes):
        if i < len(axes):
            ax = axes[i]
            data = filtered_pairs[suffix]
            
            # Plot clean line without any markers
            ax.plot(range(len(data)), data, color=colors[i % len(colors)], 
                   linewidth=1.5, alpha=0.8, marker='', linestyle='-')
            
            # Set consistent y-axis limits
            ax.set_ylim(global_ylim)
            
            # Customize subplot
            ax.set_title(f'{suffix}', fontsize=12, color='#333333', fontweight='normal')
            ax.set_xlabel('Measurement Index', fontsize=10, color='#666666')
            ax.set_ylabel('Time (µs)', fontsize=10, color='#666666')
            
            # Styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#cccccc')
            ax.spines['bottom'].set_color('#cccccc')
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            ax.tick_params(axis='both', labelsize=9, colors='#666666')
    
    # Hide unused subplots
    for i in range(len(suffixes), len(axes)):
        axes[i].set_visible(False)
    
    plt.suptitle(f'Raw Data Trends ({mode} Mode)', fontsize=14, 
                 color='#333333', fontweight='normal', y=0.95)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

# Function to plot individual raw data charts
def plot_individual_raw_data(pairs, timestamps, mode, output_dir):
    # Filter outliers
    filtered_pairs, outliers = filter_outliers(pairs, timestamps)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, (suffix, data) in enumerate(filtered_pairs.items()):
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot line without markers
        ax.plot(range(len(data)), data, color=colors[i % len(colors)], 
               linewidth=2, alpha=0.8)
        
        # Customize plot
        ax.set_title(f'{suffix} - Raw Data Trend ({mode} Mode)', 
                    fontsize=14, color='#333333', fontweight='normal', pad=20)
        ax.set_xlabel('Measurement Index', fontsize=12, color='#666666')
        ax.set_ylabel('Time (µs)', fontsize=12, color='#666666')
        
        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis='both', labelsize=11, colors='#666666')
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, f'raw_data_{mode}_{suffix}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"Individual chart saved: {output_path}")

# Function to plot combined raw data as box plots
def plot_combined_raw_data(pairs, timestamps, mode, output_path, log_file=None):
    # Use all data (including outliers) instead of filtered data
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Prepare data for box plots
    box_data = []
    labels = []
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for suffix, data in pairs.items():
        if data:  # Only include if data exists
            box_data.append(data)
            labels.append(suffix.upper())
    
    if not box_data:
        print(f"No data available for {mode} mode box plot")
        return
    
    # Create box plots with all outliers shown
    box_plot = ax.boxplot(box_data, tick_labels=labels, patch_artist=True,
                         showmeans=True, meanline=True, showfliers=True)
    
    # Customize box plot colors
    for i, patch in enumerate(box_plot['boxes']):
        patch.set_facecolor(colors[i % len(colors)])
        patch.set_alpha(0.7)
        patch.set_edgecolor(colors[i % len(colors)])
        patch.set_linewidth(1.5)
    
    # Customize other elements
    for element in ['whiskers', 'medians', 'caps']:
        plt.setp(box_plot[element], color='#333333', linewidth=1.5)
    
    # Customize fliers (outliers)
    for i, flier in enumerate(box_plot['fliers']):
        flier.set_marker('o')
        flier.set_markerfacecolor(colors[i % len(colors)])
        flier.set_markeredgecolor(colors[i % len(colors)])
        flier.set_markersize(3)
        flier.set_alpha(0.6)
    
    # Mean lines
    plt.setp(box_plot['means'], color='red', linewidth=2)
    
    # Set logarithmic y-axis
    ax.set_yscale('log')
    
    # Customize plot
    ax.set_title(f'Statistical Distribution Analysis - All Measurements ({mode} Mode)\n' +
                'Box plots show: Min, Q1, Median, Q3, Max, Mean (red line), and all outliers',
                fontsize=14, color='#333333', fontweight='normal', pad=25)
    ax.set_xlabel('Measurement Type', fontsize=12, color='#666666')
    ax.set_ylabel('Time (µs) - Log Scale', fontsize=12, color='#666666')
    
    # Color x-axis labels to match their respective box colors
    tick_labels = ax.get_xticklabels()
    for i, label in enumerate(tick_labels):
        label.set_color(colors[i % len(colors)])
        label.set_fontweight('bold')
        label.set_fontsize(12)
    
    # Styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, axis='y')
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', labelsize=10, colors='#666666')
    ax.tick_params(axis='x', labelsize=12, colors='#666666')
    
    # Add legend explaining the box plot elements
    legend_elements = [
        plt.Line2D([0], [0], color='#333333', linewidth=1.5, label='Q1, Median, Q3'),
        plt.Line2D([0], [0], color='red', linewidth=2, label='Mean'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                  markersize=6, alpha=0.6, label='Outliers', linestyle='None')
    ]
    ax.legend(handles=legend_elements, loc='upper right', frameon=True, 
             fancybox=False, shadow=False, framealpha=0.9, fontsize=10)
    
    # Write statistics to log file instead of printing
    if log_file:
        log_file.write(f"\nBox plot statistics for {mode} mode (all data including outliers):\n")
        for i, (suffix, data) in enumerate(pairs.items()):
            if data:
                q1 = np.percentile(data, 25)
                q2 = np.percentile(data, 50)  # median
                q3 = np.percentile(data, 75)
                min_val = np.min(data)
                max_val = np.max(data)
                mean_val = np.mean(data)
                count = len(data)
                log_file.write(f"  {suffix.upper()} (n={count}):\n")
                log_file.write(f"    Min: {min_val:.2f} µs\n")
                log_file.write(f"    Q1:  {q1:.2f} µs\n")
                log_file.write(f"    Q2 (Median): {q2:.2f} µs\n")
                log_file.write(f"    Q3:  {q3:.2f} µs\n")
                log_file.write(f"    Max: {max_val:.2f} µs\n")
                log_file.write(f"    Mean: {mean_val:.2f} µs\n")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

def main():
    import sys
    
    # Check if input file is provided as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"Error: Input file not found: {input_file}")
            return
        
        # Extract mode from filename
        filename = os.path.basename(input_file)
        if 'Monolithic' in filename or 'monolithic' in filename:
            mode = 'Monolithic'
        elif 'NFAPI' in filename or 'nfapi' in filename:
            mode = 'NFAPI'
        else:
            mode = 'Unknown'
        
        print(f"Processing single file: {input_file} ({mode} mode)")
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime('%Y%m%d')
        output_dir = os.path.join('/home/ming/E2E-network-measurement/Measure/Analysis', f'analysis-measure-{mode}-{timestamp}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create log report file
        log_report_path = os.path.join(output_dir, f'analysis_report_{timestamp}.log')
        
        with open(log_report_path, 'w') as log_report:
            log_report.write(f"Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_report.write("=" * 60 + "\n")
            log_report.write(f"\nProcessing {filename} ({mode} mode)\n")
            log_report.write("-" * 40 + "\n")
            
            pairs, timestamps = process_log_file(input_file)
            averages = calculate_averages(pairs)
            
            # Write averages to log
            log_report.write(f"\nAverage time differences for {mode} mode (µs):\n")
            for suffix, avg in averages.items():
                log_report.write(f"  {suffix}: {avg:.2f} µs\n")
            
            # Generate charts
            output_path_bar = os.path.join(output_dir, f'average_time_differences_{mode}_bar.png')
            plot_averages_with_count(pairs, averages, mode, output_path_bar)
            print(f"Bar chart saved as {output_path_bar}")
            
            output_path_raw = os.path.join(output_dir, f'raw_data_trends_{mode}.png')
            plot_raw_data(pairs, timestamps, mode, output_path_raw, log_report)
            print(f"Combined raw data chart saved as {output_path_raw}")
            
            output_path_combined = os.path.join(output_dir, f'raw_data_trends_{mode}_combined.png')
            plot_combined_raw_data(pairs, timestamps, mode, output_path_combined, log_report)
            print(f"Combined all-in-one raw data chart saved as {output_path_combined}")
            
            plot_individual_raw_data(pairs, timestamps, mode, output_dir)
        
        print(f"Analysis report saved as {log_report_path}")
        return
    
    # Original code for processing all files in log directory
    log_dir = '/home/ming/E2E-network-measurement/Measure/log/'
    base_output_dir = '/home/ming/E2E-network-measurement/Measure/Analysis'
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y%m%d')
    output_dir = os.path.join(base_output_dir, f'analysis-measure-NFAPI-{timestamp}')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create log report file
    log_report_path = os.path.join(output_dir, f'analysis_report_{timestamp}.log')
    
    log_files = [f for f in os.listdir(log_dir) if f.startswith('measure_filtered-') and f.endswith('.txt')]
    
    # Process all files
    with open(log_report_path, 'w') as log_report:
        log_report.write(f"Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_report.write("=" * 60 + "\n")
        
        for selected_file in log_files:
            mode = selected_file.split('-')[1].split('.')[0]
            print(f"\nProcessing {selected_file} ({mode} mode)...")
            
            log_report.write(f"\n\nProcessing {selected_file} ({mode} mode)\n")
            log_report.write("-" * 40 + "\n")
            
            filepath = os.path.join(log_dir, selected_file)
            pairs, timestamps = process_log_file(filepath)
            averages = calculate_averages(pairs)
            
            # Write averages to log
            log_report.write(f"\nAverage time differences for {mode} mode (µs):\n")
            for suffix, avg in averages.items():
                log_report.write(f"  {suffix}: {avg:.2f} µs\n")
            
            # Generate bar chart with averages
            output_path_bar = os.path.join(output_dir, f'average_time_differences_{mode}_bar.png')
            plot_averages_with_count(pairs, averages, mode, output_path_bar)
            print(f"Bar chart saved as {output_path_bar}")
            
            # Generate combined raw data line chart
            output_path_raw = os.path.join(output_dir, f'raw_data_trends_{mode}.png')
            plot_raw_data(pairs, timestamps, mode, output_path_raw, log_report)
            print(f"Combined raw data chart saved as {output_path_raw}")
            
            # Generate combined raw data chart (all on one plot)
            output_path_combined = os.path.join(output_dir, f'raw_data_trends_{mode}_combined.png')
            plot_combined_raw_data(pairs, timestamps, mode, output_path_combined, log_report)
            print(f"Combined all-in-one raw data chart saved as {output_path_combined}")
            
            # Generate individual raw data charts
            plot_individual_raw_data(pairs, timestamps, mode, output_dir)
    
    print(f"\nAnalysis report saved as {log_report_path}")

if __name__ == '__main__':
    main()