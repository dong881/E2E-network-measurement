# E2E Network Measurement

## Overview

This project provides an automated, end-to-end (E2E) network measurement tool designed to evaluate network performance across various configurations. It integrates SSH, ADB, iPerf3, and ping to measure throughput and round-trip time (RTT) under different bandwidth settings, protocols (TCP/UDP), directions (Uplink/Downlink), and packet sizes. The tool generates comprehensive data, visualizes results in a scatter plot (Throughput vs. RTT), and produces a Markdown report.

The workflow includes configuring a Radio Unit (RU), starting a gNB server, controlling a User Equipment (UE) via ADB, running performance tests, and analyzing results—all in a single script for a seamless "one-click" experience.

## Features

- **Automated Configuration**: Configures RU bandwidth (e.g., 40M, 100M) via SSH and reboots the device.
- **gNB Server Control**: Starts gNB in nFAPI or FAPI mode on a remote server.
- **UE Management**: Uses ADB to toggle airplane mode and fetch UE IP dynamically.
- **Performance Testing**:
  - Measures throughput with iPerf3 (TCP/UDP, Uplink/Downlink, varying packet sizes).
  - Measures RTT with `ping -I ogstun` for precise latency tracking.
- **Comprehensive Analysis**: Generates a CSV file with test results, a scatter plot, and a Markdown report.
- **Error Handling**: Includes detailed logging and status checks to ensure uninterrupted execution.

## Prerequisites

Before running the script, ensure the following are set up:

### Software Requirements
- **Linux Environment**: Tested on Ubuntu or similar distributions.
- **Installed Tools**:
  - `expect`: For SSH automation (`sudo apt install expect`).
  - `adb`: Android Debug Bridge, added to PATH ([Download](https://dl.google.com/android/repository/platform-tools-latest-linux.zip)).
  - `python3` and `python3-venv`: For virtual environment and plotting (`sudo apt install python3 python3-venv`).
- **Network Tools**: `ping` (pre-installed on most systems).

### Hardware Requirements
- **RU Device**: Accessible via SSH at `192.168.8.77` (configurable).
- **gNB Server**: Accessible via SSH at `R750-OAI-BBU/CUDU` (configurable).
- **UE Device**: Connected via ADB with iPerf3 binary installed (`/data/local/tmp/iperf3`).
- **Control PC**: Running iPerf3 server at `192.168.70.135` (configurable).

### Pre-Configuration
1. **SSH Key Authentication**:
   - Set up passwordless SSH for RU and gNB server:
     ```bash
     ssh-keygen -t rsa
     ssh-copy-id user@192.168.8.77
     ssh-copy-id R750-OAI-BBU/CUDU
     ```
   - If not using keys, modify the script to handle passwords with `expect`.

2. **ADB Setup**:
   - Connect UE to the host machine and enable USB debugging.
   - Verify connection: `adb devices` (update `ADB_DEVICE` in script with the serial number).
   - Install iPerf3 on UE:
     ```bash
     adb push /path/to/iperf3 /data/local/tmp/iperf3
     adb shell chmod +x /data/local/tmp/iperf3
     ```

3. **iPerf3 Server**:
   - Start iPerf3 server on `192.168.70.135`:
     ```bash
     iperf3 -s
     ```

4. **Network Interface**:
   - Ensure `ogstun` is a valid interface on the machine running the script. If not, adjust the `ping` command accordingly.

## Usage

1. **Download the Script**:
   - Save the script as `run_network_test.sh` from this repository.

2. **Configure Parameters**:
   - Edit the top section of `run_network_test.sh` to match your environment:
     ```bash
     RU_IP="192.168.8.77"
     RU_USER="user"
     RU_PASSWORD="user"
     RU_ENABLE_PASSWORD="liteon168"
     GNB_SERVER="R750-OAI-BBU/CUDU"
     CONTROL_PC_IP="192.168.8.118"
     CONTROL_PC_USER="sshuser"
     CONTROL_PC_PASSWORD="bmwlab"
     SERVER_IP="192.168.70.135"
     ADB_DEVICE="0123456789ABCDEF"
     ```
   - Adjust `TEST_DURATION`, `WAIT_AFTER_REBOOT`, and `WAIT_AFTER_GNB` if needed.

3. **Run the Script**:
   ```bash
   chmod +x run_network_test.sh
   ./run_network_test.sh
   ```

4. **Output**:
   - Results are saved in a directory named `test_results_YYYYMMDD_HHMMSS` (e.g., `test_results_20250409_123456`), containing:
     - `results.csv`: Test data (Test ID, Bandwidth, Protocol, Direction, Settings, Throughput, RTT).
     - `scatter_plot.png`: Throughput vs. RTT scatter plot.
     - `report.md`: Summary report with plot and data table.
     - `test.log`: Detailed execution log.
     - Individual iPerf3 and ping logs for each test.

## Script Details

### Workflow
1. **RU Configuration**: Sets bandwidth (40M or 100M bps) via SSH and reboots the RU.
2. **gNB Startup**: Launches gNB in nFAPI mode (VNF then PNF).
3. **UE Preparation**: Disables airplane mode and retrieves UE IP via ADB.
4. **Testing Loop**:
   - Runs iPerf3 and ping for each combination:
     - TCP: Uplink/Downlink, full speed.
     - UDP: Uplink/Downlink, small (256B) and large (1470B) packets, 1Gbps bandwidth.
   - Extracts throughput and RTT, saving to CSV.
5. **Cleanup**: Enables airplane mode after tests.
6. **Analysis**: Sets up a Python virtual environment, installs dependencies, generates a scatter plot, and creates a Markdown report.

### Test Combinations
| Protocol | Direction | Settings             |
|----------|-----------|----------------------|
| TCP      | Downlink  | Full speed           |
| TCP      | Uplink    | Full speed           |
| UDP      | Downlink  | 256B packet, 1Gbps   |
| UDP      | Downlink  | 1470B packet, 1Gbps  |
| UDP      | Uplink    | 256B packet, 1Gbps   |
| UDP      | Uplink    | 1470B packet, 1Gbps  |

## Notes and Troubleshooting

- **SSH Issues**: If SSH connections fail, ensure keys are set up or modify the script to handle passwords.
- **ADB Connection**: Verify UE is detected (`adb devices`) and iPerf3 is executable.
- **Ping Interface**: If `ogstun` is not on the host machine, modify the `run_test` function to run ping on the appropriate device (e.g., via `adb shell`).
- **Python Errors**: Ensure `python3-venv` is installed; check `test.log` for pip installation issues.
- **Network Stability**: Unstable networks may lead to missing data points; review `test.log` for warnings.

## Example Output

### `results.csv`
```
Test_ID,Bandwidth,Protocol,Direction,Settings,Throughput,RTT
40000000_TCP_DL_,40000000,TCP,DL,,500,10
40000000_UDP_DL_-l_256_-b_1G,40000000,UDP,DL,-l 256 -b 1G,450,12
...
```

### `scatter_plot.png`
![Sample Scatter Plot](example/scatter_plot.png)

### `report.md`
```markdown
# Network Test Report
Generated on: Wed Apr 09 12:34:56 2025

## Test Results
![Scatter Plot](scatter_plot.png)

## Data
Test_ID                       Bandwidth  Protocol  Direction  Settings      Throughput  RTT
40000000_TCP_DL_             40000000   TCP       DL                    500         10
40000000_UDP_DL_-l_256_-b_1G 40000000   UDP       DL         -l 256 -b 1G  450         12
...
```

## Contributing

Feel free to fork this repository, submit issues, or contribute improvements via pull requests. For specific feature requests, please detail your use case.
