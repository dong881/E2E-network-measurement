"""
Data Folder Selection Utility
Provides terminal UI for selecting data folders
"""

from pathlib import Path
import json
import datetime
import sys
import os

# Configuration file to store the last selected data directory
CONFIG_FILE = Path.home() / '.e2e_network_measurement_config.json'
BASE_DATA_DIR = Path("/home/ming/E2E-network-measurement/data")  # Convert to Path object
BASE_ANALYSIS_DIR = Path("/home/ming/E2E-network-measurement/Analysis")  # Convert to Path object

def save_last_data_dir(data_dir):
    """Save the last selected data directory to config file"""
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except:
            config = {}
    
    config['last_data_dir'] = str(data_dir)
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save configuration: {e}")

def load_last_data_dir():
    """Load the last selected data directory from config file"""
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        last_dir = config.get('last_data_dir')
        if last_dir and Path(last_dir).exists():
            return Path(last_dir)
    except:
        pass
    return None

def extract_mode_from_folder(folder_name):
    """Extract mode from folder name pattern: YYYYMMDD-MODE(bandwidth)"""
    try:
        # Pattern: 20250528-nFAPI(100-500M)
        if '-' in folder_name and '(' in folder_name:
            # Split by '-' and take the part before '('
            parts = folder_name.split('-')
            if len(parts) >= 2:
                mode_part = parts[1].split('(')[0]
                return mode_part
        return "Unknown"
    except:
        return "Unknown"

def get_available_data_directories():
    """Get list of available data directories"""
    try:
        if not BASE_DATA_DIR.exists():
            print(f"Error: Base data directory not found: {BASE_DATA_DIR}")
            return []
        
        available_dirs = sorted([
            d for d in BASE_DATA_DIR.iterdir() 
            if d.is_dir() and not d.name.startswith('.')
        ])
        return available_dirs
    except Exception as e:
        print(f"Error reading data directories: {e}")
        return []

def get_data_folder_interactive():
    """Interactive data folder selection with menu"""
    available_dirs = get_available_data_directories()
    
    if not available_dirs:
        print(f"No data directories found in {BASE_DATA_DIR}")
        return None
    
    print("\n" + "="*60)
    print("📁 Available Data Directories:")
    print("="*60)
    
    for i, dir_path in enumerate(available_dirs):
        mode = extract_mode_from_folder(dir_path.name)
        print(f"{i + 1:2d}: {dir_path.name} [{mode} Mode]")
    
    print("="*60)
    
    while True:
        try:
            choice = input(f"🔍 Select a directory number (1-{len(available_dirs)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("❌ Analysis cancelled by user.")
                return None
            
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(available_dirs):
                selected_dir = available_dirs[choice_index]
                mode = extract_mode_from_folder(selected_dir.name)
                print(f"✅ Selected: {selected_dir.name} [{mode} Mode]")
                return selected_dir
            else:
                print(f"❌ Invalid choice. Please enter a number from 1 to {len(available_dirs)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n❌ Analysis cancelled by user.")
            return None

def get_mode_from_data_dir(data_dir):
    """Extract testing mode from directory name"""
    dir_name = data_dir.name.lower()
    
    if 'nfapi' in dir_name:
        return 'NFAPI'
    elif 'monolithic' in dir_name or 'Monolithic' in dir_name:
        return 'Monolithic'
    else:
        return 'Unknown'

def get_analysis_output_dir(data_dir):
    """Generate analysis output directory based on selected data folder"""
    # Check for centralized output directory
    if 'CENTRALIZED_OUTPUT_DIR' in os.environ:
        return Path(os.environ['CENTRALIZED_OUTPUT_DIR'])
    
    if isinstance(data_dir, str):
        data_dir = Path(data_dir)
    
    # Create analysis directory name based on data folder name
    analysis_dir_name = f"analysis-{data_dir.name}"
    analysis_output_dir = BASE_ANALYSIS_DIR / analysis_dir_name
    
    # Create the directory if it doesn't exist (but not logs subdirectory automatically)
    analysis_output_dir.mkdir(parents=True, exist_ok=True)
    
    return analysis_output_dir

def setup_logging(output_dir, script_name):
    """Setup logging to file and return log file path"""
    
    # Create logs directory
    log_dir = output_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)  # Always create logs directory
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{script_name}_{timestamp}.log"
    
    print(f"📝 Log file will be saved to: {log_file}")
    
    return log_file

class OutputRedirector:
    """Redirect output to both console and log file"""
    def __init__(self, log_file):
        self.terminal = sys.stdout
        try:
            self.log = open(log_file, "w", encoding='utf-8')
            print(f"✅ Log file opened successfully: {log_file}")
        except Exception as e:
            print(f"❌ Error opening log file {log_file}: {e}")
            self.log = None

    def write(self, message):
        # Always write to terminal
        self.terminal.write(message)
        self.terminal.flush()
        
        # Write to log file if available
        if self.log:
            try:
                self.log.write(message)
                self.log.flush()
            except Exception as e:
                pass  # Silent fail for log writing

    def flush(self):
        self.terminal.flush()
        if self.log:
            try:
                self.log.flush()
            except:
                pass
        
    def close(self):
        if self.log:
            try:
                self.log.close()
            except Exception as e:
                pass

def redirect_output_to_log(log_file):
    """Redirect stdout to both console and log file"""
    # Ensure the log file directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    redirector = OutputRedirector(log_file)
    sys.stdout = redirector
    return redirector

def restore_stdout(redirector):
    """Restore original stdout and close log file"""
    if redirector:
        sys.stdout = redirector.terminal
        redirector.close()

if __name__ == "__main__":
    selected = get_data_folder_interactive()
    if selected:
        print(f"You selected: {selected}")
    else:
        print("No directory selected.")
