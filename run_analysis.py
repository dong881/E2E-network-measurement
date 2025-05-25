"""
Network Measurement Analysis Runner
Executes both throughput and loss rate analyses
"""

import subprocess
import sys
from pathlib import Path

def run_analysis():
    """Run all analysis scripts"""
    script_dir = Path(__file__).parent
    
    scripts = [
        script_dir / "analyze_throughput.py",
        script_dir / "analyze_packet_count.py",
        script_dir / "analyze_loss_rate.py",
        script_dir / "analyze_ping.py"
    ]
    
    for script in scripts:
        if script.exists():
            print(f"Running {script.name}...")
            try:
                subprocess.run([sys.executable, str(script)], check=True)
                print(f"✓ {script.name} completed successfully\n")
            except subprocess.CalledProcessError as e:
                print(f"✗ Error running {script.name}: {e}\n")
        else:
            print(f"✗ Script not found: {script}\n")

if __name__ == "__main__":
    run_analysis()
