import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re
import sys

def load_json_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def extract_cpu_data(data):
    """Extract CPU utilization data from iperf3 JSON"""
    if not data:
        return None
    
    try:
        cpu_data = {}
        
        # Extract CPU utilization from end section
        if 'end' in data and 'cpu_utilization_percent' in data['end']:
            cpu_util = data['end']['cpu_utilization_percent']
            cpu_data = {
                'host_total': cpu_util.get('host_total', 0),
                'host_user': cpu_util.get('host_user', 0),
                'host_system': cpu_util.get('host_system', 0),
                'remote_total': cpu_util.get('remote_total', 0),
                'remote_user': cpu_util.get('remote_user', 0),
                'remote_system': cpu_util.get('remote_system', 0)
            }
        
        return cpu_data if cpu_data else None
        
    except Exception as e:
        print(f"Error extracting CPU data: {e}")
        return None

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration directories"""
    configs = []
    
    # Look for files with bandwidth patterns
    for file_path in data_dir.glob('iperf*-*M-*.json'):
        # Extract bandwidth value from filename
        match = re.search(r'-(\d+)M-', file_path.name)
        if match:
            bandwidth_val = int(match.group(1))
            configs.append(bandwidth_val)
    
    return sorted(list(set(configs)))

def find_iperf_files(data_dir, bandwidth_val):
    """Find CN and UE iperf files for a specific bandwidth"""
    cn_file = None
    ue_file = None
    
    # Look for files matching the pattern
    cn_pattern = f"iperf*-{bandwidth_val}M-CN.json"
    ue_pattern = f"iperf*-{bandwidth_val}M-UE.json"
    
    for file_path in data_dir.glob(cn_pattern):
        cn_file = file_path
        break
    
    for file_path in data_dir.glob(ue_pattern):
        ue_file = file_path
        break
    
    return cn_file, ue_file

def create_cpu_analysis_plot(results_dict, output_dir):
    """Create comprehensive CPU utilization analysis visualization"""
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    bandwidths = sorted(results_dict.keys())
    labels = [f"{bw}M" for bw in bandwidths]
    x_pos = np.arange(len(labels))
    width = 0.35  # Slightly wider bars for better visibility
    
    # Extract mode from output directory
    mode = extract_mode_from_folder(output_dir.parent) if hasattr(output_dir, 'parent') else "Unknown"
    
    # Enhanced Total CPU Utilization with Stacked Bars and User Values
    fig1, ax1 = plt.subplots(figsize=(16, 10))
    
    # Extract data for CN and UE
    cn_user = [results_dict[bw]['cn']['host_user'] if results_dict[bw]['cn'] else 0 for bw in bandwidths]
    cn_system = [results_dict[bw]['cn']['host_system'] if results_dict[bw]['cn'] else 0 for bw in bandwidths]
    ue_user = [results_dict[bw]['ue']['host_user'] if results_dict[bw]['ue'] else 0 for bw in bandwidths]
    ue_system = [results_dict[bw]['ue']['host_system'] if results_dict[bw]['ue'] else 0 for bw in bandwidths]
    
    # Create stacked bars with professional color scheme matching throughput_comparison
    bars1_user = ax1.bar(x_pos - width/2, cn_user, width, label='CN User CPU', 
                        color='#2E86AB', alpha=0.9, edgecolor='#1B5E74', linewidth=1.2)
    bars1_system = ax1.bar(x_pos - width/2, cn_system, width, bottom=cn_user, label='CN System CPU',
                          color='#5BA3C7', alpha=0.9, edgecolor='#1B5E74', linewidth=1.2)
    
    bars2_user = ax1.bar(x_pos + width/2, ue_user, width, label='UE User CPU', 
                        color='#A23B72', alpha=0.9, edgecolor='#7A2D56', linewidth=1.2)
    bars2_system = ax1.bar(x_pos + width/2, ue_system, width, bottom=ue_user, label='UE System CPU',
                          color='#C85A90', alpha=0.9, edgecolor='#7A2D56', linewidth=1.2)
    
    ax1.set_xlabel('Bandwidth Configuration', fontsize=13, fontweight='bold')
    ax1.set_ylabel('CPU Utilization (%)', fontsize=13, fontweight='bold')
    ax1.set_title(f'CPU Utilization Analysis - {mode} Mode: CN vs UE (User + System)', 
                  fontsize=15, fontweight='bold', pad=20)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(labels)
    ax1.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True)
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim(0, 100)
    
    # Add professional value labels matching throughput_comparison style
    for i, (cn_u, cn_s, ue_u, ue_s) in enumerate(zip(cn_user, cn_system, ue_user, ue_system)):
        cn_total = cn_u + cn_s
        ue_total = ue_u + ue_s
        
        # CN labels with professional styling
        if cn_u > 2:
            ax1.text(x_pos[i] - width/2, cn_u/2, f'{cn_u:.1f}%', 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        if cn_s > 2:
            ax1.text(x_pos[i] - width/2, cn_u + cn_s/2, f'{cn_s:.1f}%', 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        if cn_total > 0:
            label_y = min(cn_total + 2, 95)
            ax1.text(x_pos[i] - width/2, label_y, f'{cn_total:.1f}%', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                             edgecolor='#2E86AB', alpha=0.9, linewidth=1.5))
        
        # UE labels with professional styling
        if ue_u > 2:
            ax1.text(x_pos[i] + width/2, ue_u/2, f'{ue_u:.1f}%', 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        if ue_s > 2:
            ax1.text(x_pos[i] + width/2, ue_u + ue_s/2, f'{ue_s:.1f}%', 
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')
        if ue_total > 0:
            label_y = min(ue_total + 2, 95)
            ax1.text(x_pos[i] + width/2, label_y, f'{ue_total:.1f}%', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                             edgecolor='#A23B72', alpha=0.9, linewidth=1.5))
    
    plt.tight_layout()
    output_file1 = output_dir / 'cpu_total_utilization_stacked_comparison.png'
    plt.savefig(output_file1, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    
    # Enhanced Statistical Summary Table
    fig2, ax2 = plt.subplots(figsize=(18, 8))
    ax2.axis('off')
    
    # Create enhanced summary table with more detailed breakdown
    table_data = []
    for bw in bandwidths:
        cn_data = results_dict[bw]['cn']
        ue_data = results_dict[bw]['ue']
        row = [
            f"{bw}M",
            f"{cn_data['host_total']:.1f}" if cn_data else "N/A",
            f"{cn_data['host_user']:.1f}" if cn_data else "N/A",
            f"{cn_data['host_system']:.1f}" if cn_data else "N/A",
            f"{ue_data['host_total']:.1f}" if ue_data else "N/A",
            f"{ue_data['host_user']:.1f}" if ue_data else "N/A",
            f"{ue_data['host_system']:.1f}" if ue_data else "N/A",
            f"{(cn_data['host_total'] - ue_data['host_total']):.1f}" if (cn_data and ue_data) else "N/A"
        ]
        table_data.append(row)
    
    table = ax2.table(
        cellText=table_data,
        colLabels=['Bandwidth', 'CN Total', 'CN User', 'CN System', 'UE Total', 'UE User', 'UE System', 'Difference'],
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.4, 2.0)
    
    # Style the table headers with professional colors matching throughput_comparison
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#2E86AB')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax2.set_title(f'CPU Utilization Statistical Summary - {mode} Mode (All Values in %)', 
                  fontsize=14, fontweight='bold', pad=25)
    
    plt.tight_layout()
    output_file2 = output_dir / 'cpu_utilization_enhanced_summary_table.png'
    plt.savefig(output_file2, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    
    return [output_file1, output_file2]

def extract_mode_from_folder(folder_path):
    """Extract mode from folder name"""
    try:
        folder_name = Path(folder_path).name
        if '-' in folder_name:
            parts = folder_name.split('-')
            if len(parts) >= 2:
                mode_part = parts[1].split('(')[0]
                return mode_part
    except:
        pass
    return "Unknown"

def analyze_cpu_utilization(data_dir=None):
    """Main function to analyze CPU utilization across bandwidth configurations"""
    # Use provided data_dir or interactive selection
    if data_dir is None:
        from data_selector import get_data_folder_interactive, setup_logging, redirect_output_to_log, get_analysis_output_dir
        data_dir = get_data_folder_interactive()
        if not data_dir:
            return
    else:
        data_dir = Path(data_dir)
    
    # Check for centralized output directory
    import os
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        output_dir = Path(os.environ['CENTRALIZED_OUTPUT_DIR'])
        log_file = None  # Use centralized logging
        log_handle = None
    else:
        from data_selector import get_analysis_output_dir, setup_logging, redirect_output_to_log
        analysis_base_dir = get_analysis_output_dir(data_dir)
        output_dir = analysis_base_dir
        log_file = setup_logging(output_dir, "cpu_analysis")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing CPU utilization data from: {data_dir}")
    
    # Get all bandwidth configurations
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("❌ No bandwidth configurations found in the data directory")
        return
    
    results_dict = {}
    
    print("✅ Processing CPU utilization data...")
    
    for bandwidth_val in bandwidth_configs:
        print(f"📊 Processing {bandwidth_val}M bandwidth...")
        cn_file, ue_file = find_iperf_files(data_dir, bandwidth_val)
        
        cn_data = load_json_data(cn_file) if cn_file else None
        ue_data = load_json_data(ue_file) if ue_file else None
        
        results_dict[bandwidth_val] = {
            'cn': extract_cpu_data(cn_data),
            'ue': extract_cpu_data(ue_data)
        }
    
    # Create visualization
    if results_dict:
        print("📈 Creating CPU utilization visualizations...")
        output_files = create_cpu_analysis_plot(results_dict, output_dir)
        print(f"✅ CPU analysis complete! Generated {len(output_files)} plots in {output_dir}")
        if log_file:
            print(f"📋 Log file saved to: {log_file}")
    else:
        print("❌ No valid CPU data found for analysis")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    # Check if data directory is provided as command line argument
    if len(sys.argv) > 1:
        analyze_cpu_utilization(sys.argv[1])
    else:
        analyze_cpu_utilization()
