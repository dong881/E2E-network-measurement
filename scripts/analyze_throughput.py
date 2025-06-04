import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
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

def extract_throughput_data(file_path):
    """Extract throughput data from iPerf JSON file"""
    data = load_json_data(file_path)
    if not data:
        return None
    
    try:
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
            'sent_packets': sum_sent.get('packets', 0),
            'received_packets': sum_received.get('packets', 0),
            'lost_packets': sum_sent.get('packets', 0) - sum_received.get('packets', 0),
            'loss_percent': sum_received.get('lost_percent', 0)
        }
    except Exception as e:
        print(f"Error extracting data from {file_path}: {e}")
        return None

def extract_mode_from_folder(folder_path):
    """Extract mode from folder name pattern: MODE(bandwidth) or YYYYMMDD-MODE(bandwidth)"""
    folder_name = Path(folder_path).name
    try:
        # Handle date prefix pattern: YYYYMMDD-MODE(bandwidth)
        if folder_name and len(folder_name) > 8 and folder_name[8:9] == '-':
            # Remove date prefix (first 9 characters: YYYYMMDD-)
            folder_name = folder_name[9:]
        
        # Extract mode before parentheses
        if '(' in folder_name:
            mode_part = folder_name.split('(')[0].strip()
            # Remove any trailing dashes or hyphens
            mode_part = mode_part.rstrip('-').strip()
            return mode_part if mode_part else "Unknown Mode"
        
        # If no parentheses, check for common mode patterns
        if '-' in folder_name:
            parts = folder_name.split('-')
            # Return the first non-empty part that's not a number
            for part in parts:
                part = part.strip()
                if part and not part.isdigit():
                    return part
        
        # Clean up the folder name and return
        cleaned_name = folder_name.strip()
        return cleaned_name if cleaned_name else "Unknown Mode"
    except Exception as e:
        print(f"Warning: Error parsing folder name '{folder_name}': {e}")
        return "Unknown Mode"

def get_bandwidth_configs(data_dir):
    """Find all bandwidth configuration files"""
    configs = []
    
    # Look for iPerf JSON files with various naming patterns
    iperf_patterns = [
        '*CN*M*.json',      # Original pattern
        '*-CN-*M*.json',    # With date prefix
        '*CN_*M*.json',     # Underscore variant
        '*iperf*CN*M*.json', # With iperf prefix
        '*iperf*.json'      # General iperf files
    ]
    
    for pattern in iperf_patterns:
        for file_path in data_dir.glob(pattern):
            # Extract bandwidth from filename
            filename = file_path.name.lower()
            bandwidth_val = None
            
            # Try to find bandwidth value in various formats
            import re
            bandwidth_matches = re.findall(r'(\d+)m', filename)
            if bandwidth_matches:
                for match in bandwidth_matches:
                    val = int(match)
                    if 50 <= val <= 1000:  # Reasonable bandwidth range
                        bandwidth_val = val
                        break
            
            if bandwidth_val:
                configs.append(bandwidth_val)
    
    # Also check for files without M suffix but with numeric values
    for file_path in data_dir.glob('*.json'):
        filename = file_path.name.lower()
        if 'iperf' in filename or 'cn' in filename or 'ue' in filename:
            import re
            # Look for 3-digit numbers that could be bandwidth
            numbers = re.findall(r'\b(\d{3})\b', filename)
            for num in numbers:
                val = int(num)
                if 100 <= val <= 800:  # Common bandwidth range
                    configs.append(val)
    
    return sorted(list(set(configs)))

def find_iperf_files(data_dir, bandwidth_val):
    """Find CN and UE iPerf files for a specific bandwidth"""
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
    
    # Debug information
    if not cn_file and not ue_file:
        print(f"  ⚠️ No iPerf files found for {bandwidth_val}M bandwidth")
        # List all JSON files for debugging
        all_json = list(data_dir.glob('*.json'))
        if all_json:
            print(f"  📁 Available JSON files: {[f.name for f in all_json[:5]]}")
    
    return cn_file, ue_file

def create_throughput_comparison_plot(results_dict, output_dir):
    """Create professional throughput comparison with consistent styling"""
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    bandwidths = sorted(results_dict.keys())
    labels = [f"{bw}M" for bw in bandwidths]
    x_pos = np.arange(len(labels))
    width = 0.35
    
    # Extract mode from output directory
    mode = extract_mode_from_folder(output_dir.parent) if hasattr(output_dir, 'parent') else "Unknown"
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Extract data for CN and UE
    cn_throughput = [results_dict[bw]['cn']['sent_mbps'] if results_dict[bw]['cn'] else 0 for bw in bandwidths]
    ue_throughput = [results_dict[bw]['ue']['received_mbps'] if results_dict[bw]['ue'] else 0 for bw in bandwidths]
    
    # Updated color scheme to match other plots
    bars1 = ax.bar(x_pos - width/2, cn_throughput, width, label='CN Sent Throughput', 
                   color='#5BA3C7', alpha=0.9, edgecolor='#4A8BB0', linewidth=1.2)
    bars2 = ax.bar(x_pos + width/2, ue_throughput, width, label='UE Received Throughput',
                   color='#C85A90', alpha=0.9, edgecolor='#B04A7D', linewidth=1.2)
    
    ax.set_xlabel('Bandwidth Configuration', fontsize=13, fontweight='bold')
    ax.set_ylabel('Throughput (Mbps)', fontsize=13, fontweight='bold')
    ax.set_title(f'Throughput Analysis - {mode} Mode: CN Sent vs UE Received', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels)
    ax.legend(loc='upper left', fontsize=11, frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add professional value labels with background styling
    for i, (cn_val, ue_val) in enumerate(zip(cn_throughput, ue_throughput)):
        # CN value label
        if cn_val > 0:
            ax.text(x_pos[i] - width/2, cn_val + max(cn_throughput) * 0.02, f'{cn_val:.1f}', 
                   ha='center', va='bottom', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                            edgecolor='#5BA3C7', alpha=0.9, linewidth=1.5))
        
        # UE value label
        if ue_val > 0:
            ax.text(x_pos[i] + width/2, ue_val + max(ue_throughput) * 0.02, f'{ue_val:.1f}', 
                   ha='center', va='bottom', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                            edgecolor='#C85A90', alpha=0.9, linewidth=1.5))
        
        # Efficiency calculation
        if cn_val > 0 and ue_val > 0:
            efficiency = (ue_val / cn_val) * 100
            efficiency_y = min(max(cn_val, ue_val) * 0.7, max(max(cn_throughput), max(ue_throughput)) * 0.8)
            ax.text(x_pos[i], efficiency_y, f'{efficiency:.1f}%', 
                   ha='center', va='center', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='#F8E71C', 
                            edgecolor='#D4AC0D', alpha=0.9, linewidth=1.5))
    
    plt.tight_layout()
    output_file = output_dir / 'throughput_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close()
    
    return output_file

def analyze_throughput(data_dir=None):
    """Main function to analyze throughput data"""
    if data_dir is None:
        from data_selector import get_data_folder_interactive
        data_dir = get_data_folder_interactive()
        if not data_dir:
            return
    else:
        data_dir = Path(data_dir)
    
    # Check for centralized output directory
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        output_dir = Path(os.environ['CENTRALIZED_OUTPUT_DIR'])
        log_file = None
        log_handle = None
    else:
        from data_selector import get_analysis_output_dir, setup_logging, redirect_output_to_log
        output_dir = get_analysis_output_dir(data_dir)
        log_file = setup_logging(output_dir, "throughput_analysis")
        log_handle = redirect_output_to_log(log_file)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing throughput data from: {data_dir}")
    
    bandwidth_configs = get_bandwidth_configs(data_dir)
    
    if not bandwidth_configs:
        print("❌ No iPerf files found in the data directory")
        return
    
    results_dict = {}
    
    print("Processing throughput data:")
    
    for bandwidth_val in bandwidth_configs:
        print(f"📊 Processing {bandwidth_val}M bandwidth...")
        cn_file, ue_file = find_iperf_files(data_dir, bandwidth_val)
        
        cn_data = None
        ue_data = None
        
        if cn_file:
            cn_data = extract_throughput_data(cn_file)
            if cn_data:
                print(f"  📤 CN: {cn_data['sent_mbps']:.1f} Mbps sent")
        
        if ue_file:
            ue_data = extract_throughput_data(ue_file)
            if ue_data:
                print(f"  📥 UE: {ue_data['received_mbps']:.1f} Mbps received")
        
        results_dict[bandwidth_val] = {
            'cn': cn_data,
            'ue': ue_data
        }
    
    # Create throughput comparison plot
    try:
        output_file = create_throughput_comparison_plot(results_dict, output_dir)
        print(f"✅ Throughput comparison plot saved: {output_file.name}")
    except Exception as e:
        print(f"❌ Error creating throughput plot: {e}")
    
    print(f"✅ Throughput analysis complete! Results saved to {output_dir}")
    if log_file:
        print(f"📋 Log file saved to: {log_file}")
    
    if log_handle:
        log_handle.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_throughput(sys.argv[1])
    else:
        analyze_throughput()
