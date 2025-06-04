#!/usr/bin/env python3
"""
Master Analysis Runner
Provides interactive menu to run individual or multiple analysis scripts
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def get_available_analyses():
    """Get list of available analysis scripts"""
    script_dir = Path(__file__).parent
    
    analyses = {
        'throughput': {
            'script': script_dir / 'analyze_throughput.py',
            'name': 'Throughput Analysis',
            'description': 'Analyze CN transmission vs UE reception throughput'
        },
        # 'packet_count': {
        #     'script': script_dir / 'analyze_packet_count.py', 
        #     'name': 'Packet Count Analysis',
        #     'description': 'Compare packet counts between CN and UE'
        # },
        'packet_loss': {
            'script': script_dir / 'analyze_packet_loss.py',
            'name': 'Packet Loss Analysis', 
            'description': 'Analyze UE packet loss rates with quality categorization'
        },
        # 'loss_rate': {
        #     'script': script_dir / 'analyze_loss_rate.py',
        #     'name': 'Loss Rate Analysis',
        #     'description': 'Compare CN vs UE loss rates across configurations'
        # },
        'ping_latency': {
            'script': script_dir / 'analyze_ping_latency.py',
            'name': 'Ping Latency Analysis',
            'description': 'Analyze ping latency with quartile statistics'
        },
        'jitter': {
            'script': script_dir / 'analyze_jitter.py',
            'name': 'Jitter Analysis',
            'description': 'Analyze UE network jitter quality'
        },
        'cpu': {
            'script': script_dir / 'analyze_cpu_utilization.py',
            'name': 'CPU Utilization Analysis',
            'description': 'Analyze CPU usage across bandwidth configurations'
        }
    }
    
    # Filter to only include existing scripts
    return {k: v for k, v in analyses.items() if v['script'].exists()}

def run_analysis(script_path, data_dir, log_file):
    """Run a single analysis script with logging"""
    try:
        print(f"🔄 Running {script_path.name}...")
        result = subprocess.run([
            sys.executable, str(script_path), str(data_dir)
        ], capture_output=True, text=True, timeout=300)
        
        # Write detailed output to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Analysis: {script_path.name}\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n")
            
            if result.stdout:
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\n")
            
            if result.stderr:
                f.write("STDERR:\n")
                f.write(result.stderr)
                f.write("\n")
            
            f.write(f"Return Code: {result.returncode}\n")
            f.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if result.returncode == 0:
            print(f"✅ {script_path.name} completed successfully")
            return True
        else:
            print(f"❌ {script_path.name} failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ {script_path.name} timed out after 5 minutes")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\nERROR: {script_path.name} timed out after 5 minutes\n")
        return False
    except Exception as e:
        print(f"💥 Error running {script_path.name}: {e}")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\nERROR: Exception running {script_path.name}: {e}\n")
        return False

def run_all_analyses(data_dir, selected_analyses=None):
    """Run all or selected analyses with centralized logging"""
    available_analyses = get_available_analyses()
    
    if not available_analyses:
        print("❌ No analysis scripts found!")
        return
    
    # If no specific analyses selected, run all
    if selected_analyses is None:
        selected_analyses = list(available_analyses.keys())
    
    # Validate selected analyses
    invalid_analyses = set(selected_analyses) - set(available_analyses.keys())
    if invalid_analyses:
        print(f"❌ Unknown analyses: {', '.join(invalid_analyses)}")
        print(f"📋 Available analyses: {', '.join(available_analyses.keys())}")
        return
    
    # Set up centralized log file
    from data_selector import get_analysis_output_dir
    output_dir = get_analysis_output_dir(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create centralized log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"analysis_suite_{timestamp}.log"
    
    # Write initial log header
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Network Analysis Suite Log\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Data Directory: {data_dir}\n")
        f.write(f"Selected Analyses: {', '.join(selected_analyses)}\n")
        f.write(f"{'='*80}\n")
    
    print(f"\n🚀 Starting analysis suite...")
    print(f"📁 Data directory: {data_dir}")
    print(f"📊 Running {len(selected_analyses)} analyses: {', '.join(selected_analyses)}")
    print(f"💾 Results will be saved to: {output_dir}")
    print(f"📝 Detailed logs will be saved to: {log_file}")
    print("="*80)
    
    # Set environment variable for centralized output
    os.environ['CENTRALIZED_OUTPUT_DIR'] = str(output_dir)
    
    successful = 0
    failed = 0
    
    for analysis_name in selected_analyses:
        analysis_info = available_analyses[analysis_name]
        print(f"\n📈 {analysis_info['name']}")
        print("-" * 60)
        
        if run_analysis(analysis_info['script'], data_dir, log_file):
            successful += 1
        else:
            failed += 1
    
    # Clean up environment variable
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        del os.environ['CENTRALIZED_OUTPUT_DIR']
    
    # Write final summary to log
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"Analysis Suite Summary\n")
        f.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"{'='*80}\n")
    
    print("\n" + "="*80)
    print(f"📊 Analysis Suite Complete!")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"💾 Results saved to: {output_dir}")
    print(f"📝 Detailed logs saved to: {log_file}")
    print("="*80)

def interactive_analysis_selection():
    """Interactive mode for selecting specific analyses"""
    available_analyses = get_available_analyses()
    
    print("\n📋 Available Analyses:")
    print("="*60)
    
    for i, (key, info) in enumerate(available_analyses.items(), 1):
        print(f"{i:2d}: {info['name']}")
        print(f"     {info['description']}")
        print()
    
    print("="*60)
    print("💡 Enter analysis numbers separated by commas (e.g., 1,3,5)")
    print("💡 Or press Enter for all analyses")
    
    while True:
        try:
            choice = input("🔍 Select analyses: ").strip()
            
            if not choice:  # Empty input means all
                return list(available_analyses.keys())
            
            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in choice.split(',')]
            analysis_keys = list(available_analyses.keys())
            
            selected = []
            for idx in indices:
                if 1 <= idx <= len(analysis_keys):
                    selected.append(analysis_keys[idx - 1])
                else:
                    print(f"❌ Invalid choice: {idx}. Must be between 1 and {len(analysis_keys)}")
                    break
            else:
                return selected
                
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by commas.")
        except KeyboardInterrupt:
            print("\n❌ Selection cancelled.")
            return None

def main():
    parser = argparse.ArgumentParser(
        description='Network Measurement Analysis Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_analysis.py                    # Interactive mode, all analyses by default
  python run_all_analysis.py --select          # Interactive mode with analysis selection
  python run_all_analysis.py --analyses throughput,ping_latency  # Run specific analyses
  python run_all_analysis.py --data /path/to/data --analyses cpu  # Custom data path
        """
    )
    
    parser.add_argument('--data', type=str, help='Data directory path (interactive selection if not provided)')
    parser.add_argument('--analyses', type=str, help='Comma-separated list of analyses to run')
    parser.add_argument('--select', action='store_true', help='Interactive analysis selection mode')
    parser.add_argument('--list', action='store_true', help='List available analyses and exit')
    
    args = parser.parse_args()
    
    # List available analyses and exit
    if args.list:
        available_analyses = get_available_analyses()
        print("📋 Available Analyses:")
        for key, info in available_analyses.items():
            print(f"  {key:15} - {info['name']}")
        return
    
    # Get data directory
    if args.data:
        data_dir = Path(args.data)
        if not data_dir.exists():
            print(f"❌ Data directory not found: {data_dir}")
            return
    else:
        from data_selector import get_data_folder_interactive
        data_dir = get_data_folder_interactive()
        if not data_dir:
            return
    
    # Get selected analyses
    selected_analyses = None
    
    if args.select:
        # Interactive selection mode
        selected_analyses = interactive_analysis_selection()
        if selected_analyses is None:
            return
    elif args.analyses:
        # Command line specified analyses
        selected_analyses = [x.strip() for x in args.analyses.split(',')]
    # If neither --select nor --analyses, use default (all analyses)
    
    # Run the analyses
    run_all_analyses(data_dir, selected_analyses)

if __name__ == "__main__":
    main()
