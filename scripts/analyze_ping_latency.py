import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re
import sys
import os

def load_json_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def parse_ping_log(file_path):
    """Parse ping log files to extract latency data"""
    ping_data = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                ping_match = re.search(r'time=([\d.]+)\s*ms', line)
                if ping_match:
                    ping_time = float(ping_match.group(1))
                    ping_data.append(ping_time)
    except Exception as e:
        print(f"Error parsing ping log {file_path}: {e}")
    
    return ping_data

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration directories"""
    configs = []
    
    for file_path in data_dir.glob('ping*-*M*.log'):
        match = re.search(r'-(\d+)M', file_path.name)
        if match:
            bandwidth_val = int(match.group(1))
            configs.append(bandwidth_val)
    
    return sorted(list(set(configs)))

def calculate_quartile_stats(data):
    """Calculate comprehensive quartile statistics"""
    if len(data) == 0:
        return None
    
    q1 = np.percentile(data, 25)
    q2 = np.percentile(data, 50)  # Median
    q3 = np.percentile(data, 75)
    
    # IQR and outlier boundaries
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Filter outliers using IQR method
    filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]
    
    return {
        'q1': q1,
        'q2': q2,
        'q3': q3,
        'iqr': iqr,
        'mean': np.mean(data),
        'std': np.std(data),
        'outlier_count': len(data) - len(filtered_data),
        'raw_data': data
    }

def extract_mode_from_folder(folder_path):
    """Extract mode from folder name - simplified and reliable"""
    folder_name = Path(folder_path).name
    
    # Handle date prefix pattern: YYYYMMDD-MODE
    if len(folder_name) > 8 and folder_name[8:9] == '-':
        folder_name = folder_name[9:]
    
    # Extract mode before parentheses or first part
    if '(' in folder_name:
        mode = folder_name.split('(')[0].strip().rstrip('-')
    else:
        mode = folder_name.split('-')[0] if '-' in folder_name else folder_name
    
    return mode.strip() if mode.strip() else "Unknown"

def extract_throughput_data(file_path):
    """Extract throughput data from iPerf JSON file (borrowed from analyze_throughput.py)"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        end_summary = data.get('end', {})
        sum_sent = end_summary.get('sum_sent', {})
        sum_received = end_summary.get('sum_received', {})
        
        # For CN data, use bits_per_second from sum section if available
        cn_bits_per_second = end_summary.get('sum', {}).get('bits_per_second', 0)
        if cn_bits_per_second == 0:
            cn_bits_per_second = sum_sent.get('bits_per_second', 0)
        
        return {
            'sent_mbps': cn_bits_per_second / 1_000_000,
            'received_mbps': sum_received.get('bits_per_second', 0) / 1_000_000,
        }
    except Exception as e:
        print(f"Error extracting throughput data from {file_path}: {e}")
        return None

def find_iperf_files_for_bandwidth(data_dir, bandwidth_val):
    """Find CN and UE iPerf files for throughput data"""
    cn_file = None
    ue_file = None
    
    # Multiple patterns to search for files
    cn_patterns = [
        f'*CN*{bandwidth_val}M*.json',
        f'*CN*{bandwidth_val}*.json',
        f'*cn*{bandwidth_val}m*.json',
        f'*{bandwidth_val}*CN*.json',
        f'*{bandwidth_val}*cn*.json'
    ]
    
    ue_patterns = [
        f'*UE*{bandwidth_val}M*.json', 
        f'*UE*{bandwidth_val}*.json',
        f'*ue*{bandwidth_val}m*.json',
        f'*{bandwidth_val}*UE*.json',
        f'*{bandwidth_val}*ue*.json'
    ]
    
    # Search for CN files
    for pattern in cn_patterns:
        for file_path in data_dir.glob(pattern):
            if 'iperf' in file_path.name.lower():
                cn_file = file_path
                break
        if cn_file:
            break
    
    # Search for UE files
    for pattern in ue_patterns:
        for file_path in data_dir.glob(pattern):
            if 'iperf' in file_path.name.lower():
                ue_file = file_path
                break
        if ue_file:
            break
    
    return cn_file, ue_file

def get_throughput_data_for_bandwidths(data_dir, bandwidths):
    """Get throughput data for all bandwidth configurations"""
    throughput_data = {}
    
    for bandwidth_val in bandwidths:
        cn_file, ue_file = find_iperf_files_for_bandwidth(data_dir, bandwidth_val)
        
        cn_data = None
        ue_data = None
        
        if cn_file:
            cn_data = extract_throughput_data(cn_file)
        
        if ue_file:
            ue_data = extract_throughput_data(ue_file)
        
        throughput_data[bandwidth_val] = {
            'cn_sent': cn_data['sent_mbps'] if cn_data else 0,
            'ue_received': ue_data['received_mbps'] if ue_data else 0
        }
    
    return throughput_data

def create_quartile_analysis_plot(results_dict, output_dir, direction, mode, data_dir=None):
    """Create comprehensive quartile analysis visualization with throughput labels"""
    
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 12,
        'legend.fontsize': 9,
    })
    
    bandwidths = sorted(results_dict.keys())
    
    # Get throughput data for enhanced labels
    throughput_data = {}
    if data_dir:
        throughput_data = get_throughput_data_for_bandwidths(data_dir, bandwidths)
    
    # Create enhanced labels with throughput information
    labels = []
    for bw in bandwidths:
        if bw in throughput_data:
            recv_mbps = throughput_data[bw]['ue_received']
            sent_mbps = throughput_data[bw]['cn_sent']
            if recv_mbps > 0 and sent_mbps > 0:
                labels.append(f"{recv_mbps:.1f}M\n({sent_mbps:.1f}M send)")
            else:
                labels.append(f"{bw}M")
        else:
            labels.append(f"{bw}M")
    
    # Color scheme
    box_color = '#2E7D32'
    median_color = '#1B5E20'
    whisker_color = '#4B5563'
    q2_trend_color = '#FF5722'
    
    output_files = []
    
    # 1. Box Plot with Q2 Trend Line
    fig, ax = plt.subplots(figsize=(12, 7))
    
    box_data = [results_dict[bw]['raw_data'] for bw in bandwidths]
    
    box_plot = plt.boxplot(box_data, tick_labels=labels, patch_artist=True, 
                          showfliers=False, widths=0.5)
    
    for patch in box_plot['boxes']:
        patch.set_facecolor(box_color)
        patch.set_alpha(0.8)
        patch.set_edgecolor(whisker_color)
    
    for whisker in box_plot['whiskers']:
        whisker.set_color(whisker_color)
        whisker.set_linewidth(1.8)
    for cap in box_plot['caps']:
        cap.set_color(whisker_color)
        cap.set_linewidth(1.8)
    for median in box_plot['medians']:
        median.set_color(median_color)
        median.set_linewidth(3.0)

    # Add Q2 trend line
    q2_values = [results_dict[bw]['q2'] for bw in bandwidths]
    x_positions = range(1, len(bandwidths) + 1)
    
    ax.plot(x_positions, q2_values, 'o-', 
            linewidth=2.5, markersize=6, 
            color=q2_trend_color, 
            markerfacecolor='white', 
            markeredgewidth=2.0, 
            markeredgecolor=q2_trend_color,
            label='Q2 Median Trend', 
            zorder=10)

    plt.xlabel('Throughput Configuration (recv/send Mbps)')
    plt.ylabel('Ping Latency (ms)')
    plt.title(f'Latency Distribution Analysis: {mode} Mode ({direction.upper()}) - Throughput Impact (recv/send)')
    plt.grid(True, alpha=0.3, linestyle=':', color='gray')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.ylim(0, 100)
    plt.legend()
    plt.tight_layout()
    
    output_file1 = output_dir / f'ping_latency_boxplot_{direction}.png'
    plt.savefig(output_file1, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    output_files.append(output_file1)
    
    # 2. Quality Analysis - also update labels
    fig, ax = plt.subplots(figsize=(12, 7))
    
    outlier_counts = [results_dict[bw]['outlier_count'] for bw in bandwidths]
    total_counts = [len(results_dict[bw]['raw_data']) for bw in bandwidths]
    outlier_percentages = [out/total*100 if total > 0 else 0 
                          for out, total in zip(outlier_counts, total_counts)]
    
    # Color coding based on quality
    bar_colors = []
    for pct in outlier_percentages:
        if pct == 0:
            bar_colors.append('#4CAF50')    # Excellent
        elif pct <= 5:
            bar_colors.append('#66BB6A')    # Good
        elif pct <= 15:
            bar_colors.append('#FFA726')    # Moderate
        else:
            bar_colors.append('#F44336')    # Critical
    
    bars = plt.bar(labels, outlier_percentages, color=bar_colors, alpha=0.8)
    
    # Add professional value labels on bars
    for i, (bar, pct) in enumerate(zip(bars, outlier_percentages)):
        if pct > 0:
            label_y = min(pct + 1, 98)
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{pct:.1f}%', 
                   ha='center', va='bottom', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                            edgecolor=bar_colors[i], alpha=0.9, linewidth=1.5))
    
    # Add color legend for quality levels
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4CAF50', alpha=0.8, label='Excellent (0% outliers)'),
        Patch(facecolor='#66BB6A', alpha=0.8, label='Good (≤5% outliers)'),
        Patch(facecolor='#FFA726', alpha=0.8, label='Moderate (6-15% outliers)'),
        Patch(facecolor='#F44336', alpha=0.8, label='Critical (>15% outliers)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', frameon=True, 
             fancybox=True, shadow=True, framealpha=0.9)
    
    plt.xlabel('Throughput Configuration (recv/send Mbps)')
    plt.ylabel('Outlier Percentage (%)')
    plt.title(f'Network Quality Assessment: {mode} Mode ({direction.upper()}) - Throughput Impact (recv/send)')
    plt.grid(True, alpha=0.3, linestyle=':', axis='y', color='gray')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    
    output_file2 = output_dir / f'ping_latency_quality_{direction}.png'
    plt.savefig(output_file2, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    output_files.append(output_file2)
    
    return output_files

def find_ping_files(data_dir, bandwidth_val):
    """Find downlink and uplink ping files for a specific bandwidth"""
    dl_file = None
    ul_file = None
    
    # Look for downlink and uplink ping files
    dl_pattern = f"ping*-{bandwidth_val}M*dl*.log"
    ul_pattern = f"ping*-{bandwidth_val}M*ul*.log"
    
    for file_path in data_dir.glob(dl_pattern):
        dl_file = file_path
        break
    
    for file_path in data_dir.glob(ul_pattern):
        ul_file = file_path
        break
    
    # If specific dl/ul patterns not found, try generic patterns
    if not dl_file and not ul_file:
        generic_pattern = f"ping*-{bandwidth_val}M*.log"
        for file_path in data_dir.glob(generic_pattern):
            if 'dl' in file_path.name.lower():
                dl_file = file_path
            elif 'ul' in file_path.name.lower():
                ul_file = file_path
            else:
                if not dl_file:
                    dl_file = file_path
    
    return dl_file, ul_file

def create_ping_summary_table(results_dict, output_dir, direction, mode):
    """Create enhanced summary table for ping latency statistics"""
    
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 12,
    })
    
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')
    
    bandwidths = sorted(results_dict.keys())
    
    # Create enhanced summary table with detailed breakdown
    table_data = []
    for bw in bandwidths:
        stats = results_dict[bw]
        row = [
            f"{bw}M",
            f"{stats['mean']:.2f}",
            f"{stats['q2']:.2f}",  # Median
            f"{stats['q1']:.2f}",
            f"{stats['q3']:.2f}",
            f"{stats['iqr']:.2f}",
            f"{stats['std']:.2f}",
            f"{stats['outlier_count']}"
        ]
        table_data.append(row)
    
    table = ax.table(
        cellText=table_data,
        colLabels=['Bandwidth', 'Mean (ms)', 'Median (ms)', 'Q1 (ms)', 'Q3 (ms)', 'IQR (ms)', 'Std Dev (ms)', 'Outliers'],
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.4, 2.0)
    
    # Style the table headers with professional colors matching CPU analysis
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#2E86AB')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax.set_title(f'Ping Latency Statistical Summary - {mode} Mode ({direction.upper()})', 
                  fontsize=14, fontweight='bold', pad=25)
    
    plt.tight_layout()
    output_file = output_dir / f'ping_latency_summary_table_{direction}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    
    return output_file

def create_comprehensive_ping_analysis(ping_data, mode, output_dir, data_dir):
    """Create comprehensive ping latency analysis"""
    
    for direction in ['dl', 'ul']:
        if not ping_data[direction]:
            print(f"⚠️ No {direction.upper()} ping data found, skipping...")
            continue
            
        print(f"📊 Creating {direction.upper()} ping analysis...")
        
        # Calculate quartile statistics for each bandwidth
        results_dict = {}
        for bandwidth, data in ping_data[direction].items():
            if data:
                np_data = np.array(data)
                stats = calculate_quartile_stats(np_data)
                if stats:
                    results_dict[bandwidth] = stats
        
        if not results_dict:
            print(f"⚠️ No valid {direction.upper()} data for analysis")
            continue
        
        # Create analysis plots
        try:
            analysis_files = create_quartile_analysis_plot(results_dict, output_dir, direction, mode, data_dir)
            
            # Create summary table
            table_file = create_ping_summary_table(results_dict, output_dir, direction, mode)
            analysis_files.append(table_file)
            
            print(f"✅ Analysis plots saved: {len(analysis_files)} files")
        except Exception as e:
            print(f"❌ Error creating analysis for {direction}: {e}")
        
        # Print summary statistics
        print(f"\n📋 {direction.upper()} Ping Latency Summary:")
        print("-" * 50)
        for bandwidth in sorted(results_dict.keys()):
            stats = results_dict[bandwidth]
            print(f"{bandwidth}M: Mean={stats['mean']:.2f}ms, "
                  f"Median={stats['q2']:.2f}ms, "
                  f"Std={stats['std']:.2f}ms, "
                  f"Outliers={stats['outlier_count']}")

def analyze_ping_latency(data_dir=None):
    """Main function to analyze ping latency data"""
    if data_dir is None:
        from data_selector import get_data_folder_interactive, setup_logging, redirect_output_to_log, get_analysis_output_dir
        data_dir = get_data_folder_interactive()
        if not data_dir:
            return
    else:
        data_dir = Path(data_dir)
    
    # Extract mode from data directory
    mode = extract_mode_from_folder(data_dir)
    print(f"📋 Detected mode: {mode}")
    
    # Check for centralized output directory
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        output_dir = Path(os.environ['CENTRALIZED_OUTPUT_DIR'])
        log_file = None
        log_handle = None
    else:
        from data_selector import get_analysis_output_dir, setup_logging, redirect_output_to_log
        analysis_base_dir = get_analysis_output_dir(data_dir)
        output_dir = analysis_base_dir
        log_file = setup_logging(output_dir, "ping_latency_analysis")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing ping latency data from: {data_dir}")
    
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("❌ No ping files found in the data directory")
        return
    
    ping_data = {'dl': {}, 'ul': {}}
    
    print("Processing ping latency data:")
    
    for bandwidth_val in bandwidth_configs:
        print(f"📊 Processing {bandwidth_val}M bandwidth...")
        dl_file, ul_file = find_ping_files(data_dir, bandwidth_val)
        
        if dl_file:
            dl_data = parse_ping_log(dl_file)
            ping_data['dl'][bandwidth_val] = dl_data
            print(f"  📥 Downlink: {len(dl_data)} ping measurements")
        
        if ul_file:
            ul_data = parse_ping_log(ul_file)
            ping_data['ul'][bandwidth_val] = ul_data
            print(f"  📤 Uplink: {len(ul_data)} ping measurements")
    
    # Create comprehensive analysis
    create_comprehensive_ping_analysis(ping_data, mode, output_dir, data_dir)
    
    print(f"✅ Ping latency analysis complete! Results saved to {output_dir}")
    if log_file:
        print(f"📋 Log file saved to: {log_file}")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_ping_latency(sys.argv[1])
    else:
        analyze_ping_latency()
