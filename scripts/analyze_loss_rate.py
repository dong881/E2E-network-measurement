from pathlib import Path
import json
import matplotlib.pyplot as plt
import numpy as np
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

def extract_loss_rate(data):
    """Extract loss rate from iperf3 JSON"""
    if not data:
        return 0
    
    try:
        if 'end' in data and 'sum' in data['end']:
            return data['end']['sum'].get('lost_percent', 0)
    except Exception as e:
        print(f"Error extracting loss rate: {e}")
        return 0

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration directories"""
    configs = []
    
    for file_path in data_dir.glob('iperf*-*M-*.json'):
        match = re.search(r'-(\d+)M-', file_path.name)
        if match:
            bandwidth_val = int(match.group(1))
            configs.append(bandwidth_val)
    
    return sorted(list(set(configs)))

def find_iperf_files(data_dir, bandwidth_val):
    """Find CN and UE iperf files for a specific bandwidth"""
    cn_file = None
    ue_file = None
    
    cn_pattern = f"iperf*-{bandwidth_val}M-CN.json"
    ue_pattern = f"iperf*-{bandwidth_val}M-UE.json"
    
    for file_path in data_dir.glob(cn_pattern):
        cn_file = file_path
        break
    
    for file_path in data_dir.glob(ue_pattern):
        ue_file = file_path
        break
    
    return cn_file, ue_file

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

def analyze_loss_rate(data_dir=None):
    """Main function to analyze and plot loss rate data"""
    if data_dir is None:
        from data_selector import get_data_folder_interactive, setup_logging, redirect_output_to_log, get_analysis_output_dir
        data_dir = get_data_folder_interactive()
        if not data_dir:
            return
    else:
        data_dir = Path(data_dir)
    
    # Extract mode from data directory
    mode = extract_mode_from_folder(data_dir)
    
    # Check for centralized output directory
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        output_dir = Path(os.environ['CENTRALIZED_OUTPUT_DIR'])
        log_file = None
        log_handle = None
    else:
        from data_selector import get_analysis_output_dir, setup_logging, redirect_output_to_log
        analysis_base_dir = get_analysis_output_dir(data_dir)
        output_dir = analysis_base_dir
        log_file = setup_logging(output_dir, "loss_rate_analysis")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing loss rate data from: {data_dir}")
    
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("❌ No bandwidth configurations found in the data directory")
        return
    
    cn_loss_rates = []
    ue_loss_rates = []
    labels = []
    
    print("Processing loss rate data:")
    
    for bandwidth_val in bandwidth_configs:
        print(f"📊 Processing {bandwidth_val}M bandwidth...")
        cn_file, ue_file = find_iperf_files(data_dir, bandwidth_val)
        
        cn_data = load_json_data(cn_file) if cn_file else None
        ue_data = load_json_data(ue_file) if ue_file else None
        
        cn_loss_rate = extract_loss_rate(cn_data)
        ue_loss_rate = extract_loss_rate(ue_data)
        
        cn_loss_rates.append(cn_loss_rate)
        ue_loss_rates.append(ue_loss_rate)
        labels.append(f"{bandwidth_val}M")
    
    # Create merged loss rate analysis plot
    fig, ax1 = plt.subplots(figsize=(16, 10))
    
    x = np.arange(len(labels))
    width = 0.35
    
    # Create bars
    bars1 = ax1.bar(x - width/2, cn_loss_rates, width, label='CN (Sender)', 
                   color='#1E88E5', alpha=0.7, edgecolor='black', linewidth=1)
    bars2 = ax1.bar(x + width/2, ue_loss_rates, width, label='UE (Receiver)', 
                   color='#D32F2F', alpha=0.7, edgecolor='black', linewidth=1)
    
    # Add trend lines
    ax1.plot(x, cn_loss_rates, 'o-', color='#0D47A1', linewidth=2, markersize=6, 
             markerfacecolor='white', markeredgewidth=2, label='CN Trend')
    ax1.plot(x, ue_loss_rates, 's-', color='#B71C1C', linewidth=2, markersize=6, 
             markerfacecolor='white', markeredgewidth=2, label='UE Trend')
    
    # Add value labels with smart positioning
    max_loss = max(max(cn_loss_rates), max(ue_loss_rates)) if cn_loss_rates or ue_loss_rates else 1
    label_spacing = max_loss * 0.015  # 1.5% spacing for better visibility
    
    for i, (cn_val, ue_val) in enumerate(zip(cn_loss_rates, ue_loss_rates)):
        # CN labels with background boxes
        if cn_val >= 0.01:  # Only show if >= 0.01%
            ax1.text(i - width/2, cn_val + label_spacing, f'{cn_val:.2f}%', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', 
                             edgecolor='#1E88E5', alpha=0.9))
        else:
            ax1.text(i - width/2, cn_val + label_spacing, f'{cn_val:.3f}%', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', 
                             edgecolor='#1E88E5', alpha=0.9))
        
        # UE labels with background boxes
        if ue_val >= 0.01:  # Only show if >= 0.01%
            ax1.text(i + width/2, ue_val + label_spacing, f'{ue_val:.2f}%', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', 
                             edgecolor='#D32F2F', alpha=0.9))
        else:
            ax1.text(i + width/2, ue_val + label_spacing, f'{ue_val:.3f}%', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', 
                             edgecolor='#D32F2F', alpha=0.9))
    
    ax1.set_xlabel('Bandwidth Configuration', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Loss Rate (%)', fontsize=14, fontweight='bold')
    ax1.set_title(f'Network Loss Rate Analysis - {mode} Mode\nCN (Sender) vs UE (Receiver) Comparison with Trends', 
                  fontsize=16, fontweight='bold', pad=20)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend(fontsize=11, loc='upper left')
    ax1.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_file = output_dir / 'merged_loss_rate_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    print(f"✅ Loss rate analysis complete! Plot saved to {output_file}")
    if log_file:
        print(f"📋 Log file saved to: {log_file}")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_loss_rate(sys.argv[1])
    else:
        analyze_loss_rate()