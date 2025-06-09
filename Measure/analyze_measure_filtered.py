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
                # Convert to microseconds
                time_diff = (stop_time - start_time) * 1_000_000
                pairs[suffix].append(time_diff)
                i += 1
        else:
            i += 1
    return pairs

# Function to calculate averages
def calculate_averages(pairs):
    averages = {}
    for suffix, times in pairs.items():
        averages[suffix] = np.mean(times) if times else 0
    return averages

# Function to plot averages
def plot_averages(averages, mode, output_path):
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(8, 5))
    
    suffixes = list(averages.keys())
    values = [averages[suffix] for suffix in suffixes]
    
    # Plot line without markers
    ax.plot(suffixes, values, color='#1f77b4', linewidth=2)
    
    # Customize plot
    ax.set_xlabel('Measurement Type', fontsize=12)
    ax.set_ylabel('Average Time Difference (µs)', fontsize=12)
    ax.set_title(f'Average Time Differences ({mode} Mode)', fontsize=14, pad=15)
    
    # Customize spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('gray')
    ax.spines['bottom'].set_color('gray')
    
    # Customize ticks
    ax.tick_params(axis='both', which='major', labelsize=10)
    plt.xticks(rotation=45, ha='right')
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    log_dir = '/home/ming/E2E-network-measurement/Measure/log/'
    log_files = [f for f in os.listdir(log_dir) if f.startswith('measure_filtered-') and f.endswith('.txt')]
    
    print("Available log files:")
    for i, fname in enumerate(log_files, 1):
        print(f"{i}. {fname}")
    
    choice = int(input("Select a file (enter number): ")) - 1
    selected_file = log_files[choice]
    mode = selected_file.split('-')[1].split('.')[0]
    
    filepath = os.path.join(log_dir, selected_file)
    pairs = process_log_file(filepath)
    averages = calculate_averages(pairs)
    
    output_path = f'average_time_differences_{mode}.png'
    plot_averages(averages, mode, output_path)
    print(f"Plot saved as {output_path}")
    
    # Print averages
    print("\nAverage time differences (µs):")
    for suffix, avg in averages.items():
        print(f"{suffix}: {avg:.2f} µs")

if __name__ == '__main__':
    main()