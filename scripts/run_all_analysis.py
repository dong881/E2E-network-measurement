"""
Network Measurement Analysis Runner
Executes all analysis scripts and generates charts in output directory
"""

import subprocess
import sys
from pathlib import Path

def run_analysis():
    """Run all analysis scripts"""
    script_dir = Path(__file__).parent
    output_dir = Path('/home/mini/E2E-network-measurement/output')
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    scripts = [
        ("Throughput Analysis", script_dir / "analyze_throughput.py"),
        ("Packet Count Analysis", script_dir / "analyze_packet_count.py"),
        ("Loss Rate Analysis", script_dir / "analyze_loss_rate.py"),
        ("Ping Latency Analysis", script_dir / "analyze_ping_latency.py")
    ]
    
    successful_runs = 0
    
    for script_name, script_path in scripts:
        if script_path.exists():
            print(f"\n{'='*60}")
            print(f"Running {script_name}...")
            print(f"Script: {script_path}")
            print(f"{'='*60}")
            
            try:
                subprocess.run([sys.executable, str(script_path)], check=True)
                print(f"✓ {script_name} completed successfully")
                successful_runs += 1
            except subprocess.CalledProcessError as e:
                print(f"✗ Error running {script_name}: {e}")
        else:
            print(f"✗ Script not found: {script_path}")
    
    print(f"\n{'='*60}")
    print(f"Analysis Summary: {successful_runs}/{len(scripts)} scripts completed successfully")
    print(f"Charts saved to: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_analysis()
