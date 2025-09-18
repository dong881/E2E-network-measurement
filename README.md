# E2E Network Measurement

## Project Summary

This framework automates End-to-End (E2E) network performance testing using shell scripts and Python analysis tools. It coordinates actions across multiple devices (Control PC, RU, gNB, CN, UE) via SSH and ADB, collecting comprehensive performance metrics including throughput, latency, packet loss, jitter, and CPU utilization. Key features include configurable test parameters (bandwidth, protocol, direction), automated setup/teardown of network components, data collection, and advanced visualizations with individual analysis scripts for each metric type. The modular design separates configuration into `variable.sh` (environment) and `run_config.sh` (test parameters), while `main.sh` orchestrates the entire process.

## Overview

This project provides an automated framework for end-to-end (E2E) network performance measurement. It leverages SSH, ADB, iPerf3, and ping to systematically evaluate network throughput and latency across various configurations. The framework is designed to be modular, allowing for easy configuration and execution of complex test scenarios involving Radio Units (RU), gNodeB (gNB), Core Network (CN), and User Equipment (UE).

The core workflow involves setting up the network components (RU bandwidth, gNB), managing the UE connection, executing performance tests (iPerf3 and ping) based on defined parameters, collecting results, and cleaning up the environment. Configuration is managed through separate files (`variable.sh`, `run_config.sh`) for clarity and ease of modification.

**Enhanced Analysis Features:**
- **Automatic Data Source Selection**: The system remembers your last data directory selection for streamlined analysis
- **Comprehensive Logging**: All analysis output is saved to log files with only status messages shown to users
- **Mode Auto-Detection**: Automatically extracts testing mode (e.g., "NFAPI", "NFAPI-SingleMachine", "Monolithic") from folder names
- **Professional Visualizations**: Enhanced color schemes and styling suitable for academic presentations and publications
- **Interactive Analysis Menu**: Comprehensive analysis runner with selectable individual or grouped analyses

## Features

- **Modular Design**: Scripts are separated by function (`radio_unit_utils.sh`, `gnb_utils.sh`, `user_equipment_utils.sh`, `core_network_utils.sh`).
- **Centralized Configuration**:
    - `variable.sh`: Stores network addresses, user credentials, and device identifiers.
    - `run_config.sh`: Stores test execution parameters like duration, bandwidth ranges, protocols, and retry counts.
- **Automated Setup**:
    - Configures RU bandwidth via SSH (`radio_unit_utils.sh`).
    - Starts/stops gNB processes on remote servers (`gnb_utils.sh`).
    - Manages CN-side processes like iPerf server and ping (`core_network_utils.sh`).
- **UE Control**: Uses ADB to toggle airplane mode, retrieve UE IP address, and run iPerf client (`user_equipment_utils.sh`).
- **Parametric Testing**: `main.sh` orchestrates tests across specified ranges of bandwidth, protocols (TCP/UDP), and directions (Uplink/Downlink).
- **Data Collection**: Saves iPerf JSON results and ping logs for each test run.
- **Robust Execution**: Includes retry logic for establishing UE connection.
- **Flexible Deployment Modes**: 
    - **Monolithic Mode**: Single gNB process handling all functions
    - **NFAPI Split Mode**: Separate VNF and PNF processes across different servers
    - **NFAPI Single-Machine Mode**: Separate VNF and PNF processes on the same server with isolated log files
- **Advanced Analytics**:
    - Network packet loss analysis (`VNF-lossPacket.py`) with interactive data folder selection
    - Comprehensive performance data processing (`network_analysis.py`)
    - Log analysis for timestamp differences (`Measure/analyze_logs.py`) 
    - Latency comparison across deployment models (`Measure/compare_latency.py`)
    - Ping latency analysis (`Measure/analyze_ping_latency.py`)
- **Visualization**: Various plots and charts help interpret test results. [See Visualization Guide](docs/visualization_guide.md)

## Installation

### Prerequisites

- Linux environment (Ubuntu recommended)
- Git for cloning the repository
- Python 3.6+ with pip

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/E2E-network-measurement.git
cd E2E-network-measurement
```

### Step 2: Install Dependencies

```bash
# System packages
sudo apt update
sudo apt install -y sshpass screen expect adb iperf3

# Python dependencies
pip install matplotlib numpy pandas seaborn

# Make scripts executable
chmod +x *.sh
chmod +x Measure/result/*.sh
```

### Step 3: Verify Installation

```bash
# Check if required tools are available
command -v sshpass >/dev/null 2>&1 && echo "✅ sshpass installed" || echo "❌ sshpass missing"
command -v screen >/dev/null 2>&1 && echo "✅ screen installed" || echo "❌ screen missing"
command -v expect >/dev/null 2>&1 && echo "✅ expect installed" || echo "❌ expect missing"
command -v adb >/dev/null 2>&1 && echo "✅ adb installed" || echo "❌ adb missing"
command -v iperf3 >/dev/null 2>&1 && echo "✅ iperf3 installed" || echo "❌ iperf3 missing"

# Check Python dependencies
python3 -c "import matplotlib, numpy, pandas, seaborn; print('✅ Python dependencies installed')" || echo "❌ Some Python dependencies are missing"
```

### Step 4: Configure Environment

1. Edit `variable.sh` to set your network configuration
2. Edit `run_config.sh` to set test parameters
3. Create required output directories:
```bash
mkdir -p data results Measure/log Measure/result
```

## Prerequisites

### Software Requirements
- **Linux Environment**: Tested on Ubuntu or similar distributions.
- **Installed Tools**:
  - `sshpass`: For non-interactive SSH password authentication (`sudo apt install sshpass`).
  - `adb`: Android Debug Bridge, added to PATH ([Download](https://dl.google.com/android/repository/platform-tools-latest-linux.zip)).
  - `iperf3`: Network performance tool (`sudo apt install iperf3`).
  - `ping`: Standard network utility (usually pre-installed).
  - `screen`: Terminal multiplexer (`sudo apt install screen`).
  - `expect`: For automating interactive SSH sessions (e.g., RU configuration) (`sudo apt install expect`).
  - **For Analysis**: Python with matplotlib, numpy, pandas, seaborn libraries. Install with: `pip install matplotlib numpy pandas seaborn`.

### Hardware Requirements
- **Control PC**: The machine running these scripts.
- **RU Device**: Accessible via SSH.
- **gNB Server(s)**: Accessible via SSH (supports separate VNF and PNF servers if needed).
- **CN Server**: Accessible via SSH, runs iPerf3 server and potentially ping target.
- **UE Device**: Connected via ADB to the Control PC, with iPerf3 binary installed (`/data/local/tmp/iperf3`).

### Pre-Configuration
1.  **SSH Access**: Ensure the Control PC can SSH into the RU, gNB, and CN servers using `sshpass` (password provided in `variable.sh`) or passwordless SSH keys.
2.  **ADB Setup**:
    - Connect UE to the Control PC and enable USB debugging.
    - Verify connection: `adb devices`. Update `ADB_DEVICE` in `run_config.sh` if necessary.
    - Install iPerf3 on UE:
      ```bash
      adb push /path/to/iperf3 /data/local/tmp/iperf3
      adb shell chmod +x /data/local/tmp/iperf3
      ```
3.  **iPerf3 Server on CN**: Ensure iPerf3 can be started on the CN server (script handles starting/stopping via `screen`).
4.  **Network Interfaces**: Ensure the network interfaces used (e.g., `ogstun` for ping, specified in `variable.sh`) are correctly configured on the relevant machines.

## Configuration

Modify the following files to match your environment:

1.  **`/home/ming/E2E-network-measurement/variable.sh`**:
    - Set IP addresses, usernames, and passwords for RU, gNB, CN servers, and the Control PC.
    - Define the network interface (`INTERFACE`) used for specific tests (e.g., ping).
    - Set the main `SERVER_IP` (likely the Control PC's IP on the test network) and `TEST_SERVER_IP` (IP address for iPerf/ping tests, often the CN server).

2.  **`/home/ming/E2E-network-measurement/run_config.sh`**:
    - Set `ADB_DEVICE` serial number.
    - Configure test parameters: `TEST_DURATION`, `MAX_RETRIES` (for UE connection), protocol flags (`TEST_UDP`, `TEST_TCP`), bandwidth ranges (`DL_START`, `DL_END`, `DL_STEP`, `UL_START`, `UL_END`, `UL_STEP`), uplink enable flag (`ENABLE_UL`), and wait times (`WAIT_AFTER_REBOOT`, `WAIT_AFTER_GNB`, `SLEEP_WINDOW`).

## Usage

### Data Collection

1.  **Navigate to Directory**:
    ```bash
    cd /home/ming/E2E-network-measurement
    ```
2.  **Ensure Scripts are Executable**:
    ```bash
    chmod +x *.sh
    ```
3.  **Run the Main Script**:
    ```bash
    # Standard mode
    ./main.sh
    
    # Manual mode (requires UE IP input)
    ./main.sh --manual-mode
    
    # Specify gNB mode (Monolithic or NFAPI)
    ./main.sh --mode Monolithic
    ./main.sh --mode NFAPI
    
    # NFAPI single-machine mode (both VNF and PNF on same server)
    ./main.sh --mode NFAPI --single-machine
    
    # Combined options
    ./main.sh --mode NFAPI --single-machine --manual-mode
    ```
    The script will:
    - Source configuration variables.
    - Set RU bandwidth (if implemented in `radio_unit_utils.sh`).
    - Stop any existing test processes on the CN server.
    - Start the gNB components (`gnb_utils.sh`).
    - Attempt to connect the UE (`user_equipment_utils.sh`).
    - Execute the iPerf3 and ping test loop defined in `main.sh`.
    - Save results to `./data/YYYYMMDD/`.
    - Stop gNB components and clean up CN processes.
    - Fetch and analyze logs.
    - Turn off UE radio (airplane mode).

4.  **Output**:
    - Test results (iPerf JSON files, ping logs) are saved in `./data/YYYYMMDD/`, organized by test parameters (e.g., `iperf-dl-udp-100M-UE.json`, `ping-ul-tcp-50M.log`).
    - Console output provides real-time status updates.

### Data Analysis

After collecting test data, you can analyze the results using the provided Python scripts. Each script focuses on a specific aspect of network performance:

1. **Individual Metric Analysis**:
   ```bash
   # Throughput analysis
   python3 scripts/analyze_throughput.py
   
   # Packet loss analysis
   python3 scripts/analyze_packet_loss.py
   
   # Jitter analysis
   python3 scripts/analyze_jitter.py
   
   # CPU utilization analysis
   python3 scripts/analyze_cpu_utilization.py
   
   # Packet count analysis
   python3 scripts/analyze_packet_count.py
   ```

2. **Comprehensive Network Analysis**:
   ```bash
   python3 network_analysis.py
   ```
   When prompted, select a test directory. The script will:
   - Process all test files in the selected directory
   - Generate visualizations and statistics
   - Save results to `./results/YYYYMMDD/`

3. **VNF-PNF Communication Analysis**:
   ```bash
   python3 Measure/analyze_logs.py /path/to/vnf/log /path/to/pnf/log
   ```

4. **Deployment Model Comparison**:
   ```bash
   python3 Measure/compare_latency.py
   ```

5. **Clean iPerf JSON Files (if needed)**:
   ```bash
   python3 clean_iperf_json.py
   ```

Each analysis script creates organized output in separate directories under `Analysis/analysis-<folder_name>/` for better organization and focused analysis.

## Python End-to-End Orchestrator

A single Python runner now handles automated collection (ping + iperf) and analysis without shell wrappers.

- Configure servers via environment variables:
  - SERVER_PASSWORD
  - CN_SERVER_USER, CN_SERVER_HOST
  - GNB_SERVER_USER, GNB_SERVER_HOST
  - VNF_GNB_SERVER_USER, VNF_GNB_SERVER_HOST (for NFAPI split)
  - ADB_DEVICE
  - INTERFACE (CN egress for ping)
  - TEST_SERVER_IP (CN IP iperf server)
- Optional: CENTRALIZED_OUTPUT_DIR to centralize analysis outputs

Quick start:
```bash
# Export your server/test environment
export SERVER_PASSWORD=...
export CN_SERVER_USER=... CN_SERVER_HOST=...
export GNB_SERVER_USER=... GNB_SERVER_HOST=...
export VNF_GNB_SERVER_USER=... VNF_GNB_SERVER_HOST=...   # NFAPI split only
export ADB_DEVICE=0123456789ABCDEF
export INTERFACE=ogstun
export TEST_SERVER_IP=10.45.0.1

# Run full collection + analysis (Monolithic)
python3 run_analysis.py --collect --mode Monolithic --dl 100:500:100 --duration 15

# NFAPI single-machine example
python3 run_analysis.py --collect --mode NFAPI --single-machine --dl 100:500:100

# Analyze existing data directory
python3 run_analysis.py --data ./data/20250101-NFAPI(100-500M)-15sec-12
```

Outputs:
- Data: ./data/<date>-<mode>(...)/...
- Analyses: ./Analysis/analysis-<folder>/ (also set via CENTRALIZED_OUTPUT_DIR)

Notes:
- CENTRALIZED_OUTPUT_DIR can be set to force all analysis outputs into a single directory.
- When mode is NFAPI, set SINGLE_MACHINE_MODE=true if VNF/PNF are on the same server.
- No local adb required: if CONTROL_PC_USER and CONTROL_PC_IP are set, the orchestrator runs ADB on the Control PC via SSH and streams output back. Otherwise, install adb locally.

### One-shot environment export with .env
Use a single .env file to export all variables at once for the Python orchestrator and analysis scripts.

```bash
# At project root
set -a; source .env; set +a
# Verify a few vars
env | grep -E 'CN_SERVER_HOST|GNB_SERVER_HOST|ADB_DEVICE|TEST_SERVER_IP'
```

Then run:
```bash
# Full collection + analysis
python3 run_analysis.py --collect --mode "$CURRENT_MODE" --duration "$TEST_DURATION"

# Analyze an existing directory
python3 run_analysis.py --data ./data/<your-folder>

# Show CLI options
python3 run_analysis.py --help
```

Troubleshooting:
- Missing tools: adb
  - Option A: install adb locally (sudo apt install -y android-tools-adb).
  - Option B: set CONTROL_PC_USER and CONTROL_PC_IP to enable remote ADB over SSH:
    ```bash
    export CONTROL_PC_USER=sshuser
    export CONTROL_PC_IP=140.118.162.81
    ```
  - Ensure SERVER_PASSWORD allows SSH to the Control PC.

### File naming conventions (data)
- Throughput (iPerf JSON):
  - CN: iperf-<dl|ul>-<udp|tcp>-<BW>M-CN.json
  - UE: iperf-<dl|ul>-<udp|tcp>-<BW>M-UE.json
- Ping logs:
  - ping-<dl|ul>-<udp|tcp>-<BW>M.log
  - idle ping: ping-<dl|ul>-<udp|tcp>-idle.log
- CPU sampling (mpstat/top fallback), created by run_analysis.py:
  - cpu-<role>-<dl|ul>-<udp|tcp>-<BW>M.log
  - roles: cn, gnb (Monolithic), vnf (NFAPI), pnf (NFAPI)

### Figure meanings (what each plot conveys)
- throughput_comparison.png
  - CN sent vs UE received throughput across bandwidths, with efficiency label (% UE/CN). Quickly shows transport efficiency gaps.
- cpu_total_utilization_stacked_comparison.png
  - CPU utilization comparison; stacked bars show User+System usage for CN and UE (or aggregated VNF+PNF under NFAPI). Reveals compute scaling vs traffic.
- cpu_utilization_enhanced_summary_table.png
  - Tabular CPU stats per bandwidth (CN/UE totals and breakdown), with CN–UE difference column for quick deltas.
- merged_loss_rate_analysis.png
  - CN vs UE loss rates with bars and trend lines. Highlights sender vs receiver loss asymmetry and scaling behavior.
- ping_latency_boxplot_dl.png / ping_latency_boxplot_ul.png
  - Box plots (per bandwidth) of ping RTT with Q2 (median) trend line; background bars show received throughput. Shows latency distribution vs offered load.
- ping_latency_quality_dl.png / ping_latency_quality_ul.png
  - Outlier percentage per bandwidth with quality color coding. Indicates network stability across loads.
- ue_jitter_analysis.png
  - UE jitter per bandwidth with color-coded quality levels. Displays timing variation sensitivity to throughput.
- packet_count_comparison.png
  - CN transmitted vs UE received packet counts. Visualizes packet delivery discrepancy by bandwidth.

## Script Details

- **`main.sh`**: Orchestrates the entire test flow. Defines the test matrix (protocols, directions, bandwidths) and calls helper scripts.
- **`variable.sh`**: Stores environment-specific variables (IPs, credentials). Sourced by `main.sh`.
- **`run_config.sh`**: Stores test execution parameters (duration, ranges, flags). Sourced by `variable.sh`.
- **[`radio_unit_utils.sh`](docs/radio_unit_utils_details.md)**: Contains functions to configure the RU (e.g., set bandwidth via SSH/expect). Called by `main.sh`. [See Details](docs/radio_unit_utils_details.md)
- **[`gnb_utils.sh`](docs/run_gNB_details.md)**: Contains functions (`start_split_setup`, `stop_split_setup`, etc.) to manage gNB processes on remote servers via SSH. Called by `main.sh`. [See Details](docs/run_gNB_details.md)
- **[`user_equipment_utils.sh`](docs/modify_UE_details.md)**: Contains functions (`toggle_airplane_mode`, `get_ue_ip`, `run_iperf`) to interact with the UE via ADB. Called by `main.sh`. [See Details](docs/modify_UE_details.md)
- **[`core_network_utils.sh`](docs/collect_data_fromCN_details.md)**: Contains functions (`ping-start`, `ping-stop`, `iperf-start`, `iperf-stop`) to manage test processes (ping, iperf3 server) on the CN server via SSH. Called by `main.sh`. [See Details](docs/collect_data_fromCN_details.md)
- **`network_analysis.py`**: Python script for post-processing test results and generating visualizations. [See Details](docs/python_analysis.md)
- **`VNF-lossPacket.py`**: Analyzes packet loss from VNF logs with comprehensive statistical analysis.
- **`scripts/analyze_loss_rate.py`**: Advanced loss rate analysis with merged CN vs UE comparison and trend analysis with enhanced output organization.
- **`scripts/analyze_packet_loss.py`**: Publication-quality UE packet loss analysis with enhanced color coding and categorization.
- **`scripts/analyze_packet_count.py`**: Network packet count analysis comparing CN transmission vs UE reception.
- **`scripts/analyze_ping_latency.py`**: Comprehensive ping latency analysis with quartile statistics and organized output structure.
- **`clean_iperf_json.py`**: Cleans iPerf JSON output files to fix parsing issues.
- **`Measure/analyze_logs.py`**: Calculates timestamp differences between VNF and PNF logs.
- **`Measure/compare_latency.py`**: Compares latency across different deployment models.
- **`Measure/result/add_prefix.sh`**: Adds prefixes to result files for organization.

## Notes and Troubleshooting

- **Installation Verification**: Use the verification commands in the installation section to confirm all dependencies are installed correctly. Look for ✅ indicators for each requirement.
- **Log Files**: Examine these logs for debugging:
  - VNF/PNF logs: Usually found at `~/oai_mp_f_ming/openairinterface5g/cmake_targets/ran_build/build/VNF.txt` and `PNF.txt`
  - iPerf logs: Found in the `data/YYYYMMDD/` directory
  - Analysis logs: Output to the console and `Measure/result/` directory
- **Dependencies**: Ensure all required tools (`sshpass`, `adb`, `iperf3`, `screen`, `expect`) are installed and in the system's PATH.
- **Permissions**: Scripts need execute permissions (`chmod +x *.sh`).
- **SSH Failures**: Verify credentials in `variable.sh` and network connectivity. Check if `sshpass` is installed or configure passwordless SSH.
- **ADB Issues**: Ensure the UE is connected, authorized, and the correct `ADB_DEVICE` is set in `run_config.sh`. Check if iPerf3 binary exists and is executable on the UE at `/data/local/tmp/iperf3`.
- **Configuration Errors**: Double-check IP addresses, usernames, passwords, and interface names in `variable.sh` and `run_config.sh`.
- **Screen Sessions**: If scripts fail unexpectedly, check for lingering `screen` sessions on the CN and gNB servers (`screen -ls`) and terminate them (`screen -X -S <session_name> quit`).
- **Python Dependencies**: For the analysis script, make sure you have the required Python libraries installed.

## Manual ADB Command Reference

For debugging or manual testing, you can use these ADB commands directly:

### List Files in UE's Temp Directory
```bash
adb -s 0123456789ABCDEF shell ls /data/local/tmp/
```

### Manually Run iPerf3 on UE
```bash
adb -s 0123456789ABCDEF shell "/data/local/tmp/iperf3 -c 10.45.0.1 -u -b 100M -t 15 -p 5201"
```

### Clean Up Temporary Files on UE
To delete all files in the `/data/local/tmp/` directory except the iperf3 executable:
```bash
adb -s 0123456789ABCDEF shell 'cd /data/local/tmp/ && ls | grep -v "^iperf3$" | xargs rm -f'
```

### Common UE IP Address Commands
```bash
# Get IP address from ccmni0 interface
adb -s 0123456789ABCDEF shell ip -f inet addr show ccmni0

# Get IP address from rmnet_data interface
adb -s 0123456789ABCDEF shell ip -f inet addr show rmnet_data0
```

### Check UE Network Connection Status
```bash
adb -s 0123456789ABCDEF shell ping -c 4 8.8.8.8
adb -s 0123456789ABCDEF shell getprop | grep -e net -e dns
```

### Toggle Airplane Mode Manually
```bash
# Turn airplane mode ON
adb -s 0123456789ABCDEF shell settings put global airplane_mode_on 1
adb -s 0123456789ABCDEF shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true

# Turn airplane mode OFF
adb -s 0123456789ABCDEF shell settings put global airplane_mode_on 0
adb -s 0123456789ABCDEF shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false
```
