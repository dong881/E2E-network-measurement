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
    
    # Increase y-axis height to prevent label compression
    ax1_ylim = ax1.get_ylim()
    ax2_ylim = ax2.get_ylim()
    ax1.set_ylim(ax1_ylim[0], ax1_ylim[1] * 1.2)
    ax2.set_ylim(ax2_ylim[0], ax2_ylim[1] * 1.2)
    
    # Title
    ax1.set_title(f'Data Distribution and Average Times ({mode} Mode)', 
                  fontsize=14, pad=25, color='#333333', fontweight='normal')
    
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
    
    # Legends - positioned to avoid overlap
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', 
               frameon=True, fancybox=False, shadow=False, framealpha=0.9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

# Function to filter outliers and print them with timestamps
def filter_outliers(pairs, timestamps, threshold_us=25):
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

# Function to plot raw data line charts (combined)
def plot_raw_data(pairs, timestamps, mode, output_path):
    # Filter outliers
    filtered_pairs, outliers = filter_outliers(pairs, timestamps)
    
    # Print outliers with timestamps
    if outliers:
        print(f"\nOutliers (>25ms) found in {mode} mode:")
        for suffix, suffix_outliers in outliers.items():
            print(f"  {suffix}:")
            for idx, value, start_time, stop_time in suffix_outliers:
                print(f"    Index {idx}: {value:.2f} µs ({value/1000:.2f} ms)")
                print(f"      Start timestamp: {start_time:.6f}")
                print(f"      Stop timestamp: {stop_time:.6f}")
    
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

def main():
    log_dir = '/home/ming/E2E-network-measurement/Measure/log/'
    output_dir = '/home/ming/E2E-network-measurement/Measure/Analysis'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    log_files = [f for f in os.listdir(log_dir) if f.startswith('measure_filtered-') and f.endswith('.txt')]
    
    # Process all files
    for selected_file in log_files:
        mode = selected_file.split('-')[1].split('.')[0]
        print(f"\nProcessing {selected_file} ({mode} mode)...")
        
        filepath = os.path.join(log_dir, selected_file)
        pairs, timestamps = process_log_file(filepath)
        averages = calculate_averages(pairs)
        
        # Generate bar chart with averages
        output_path_bar = os.path.join(output_dir, f'average_time_differences_{mode}_bar.png')
        plot_averages_with_count(pairs, averages, mode, output_path_bar)
        print(f"Bar chart saved as {output_path_bar}")
        
        # Generate combined raw data line chart
        output_path_raw = os.path.join(output_dir, f'raw_data_trends_{mode}.png')
        plot_raw_data(pairs, timestamps, mode, output_path_raw)
        print(f"Combined raw data chart saved as {output_path_raw}")
        
        # Generate individual raw data charts
        plot_individual_raw_data(pairs, timestamps, mode, output_dir)
        
        # Print averages
        print(f"Average time differences for {mode} mode (µs):")
        for suffix, avg in averages.items():
            print(f"  {suffix}: {avg:.2f} µs")

if __name__ == '__main__':
    main()