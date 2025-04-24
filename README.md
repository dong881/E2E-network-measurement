# E2E Network Measurement

## Project Summary

This framework automates End-to-End (E2E) network performance testing using shell scripts. It coordinates actions across multiple devices (Control PC, RU, gNB, CN, UE) via SSH and ADB. Key features include configurable test parameters (bandwidth, protocol, direction), automated setup/teardown of network components (gNB, iPerf server), UE connection management, and collection of iPerf/ping results. Configuration is separated into `variable.sh` (environment) and `run_config.sh` (test parameters) for easy management. The `main.sh` script orchestrates the entire process.

## Overview

This project provides an automated framework for end-to-end (E2E) network performance measurement. It leverages SSH, ADB, iPerf3, and ping to systematically evaluate network throughput and latency across various configurations. The framework is designed to be modular, allowing for easy configuration and execution of complex test scenarios involving Radio Units (RU), gNodeB (gNB), Core Network (CN), and User Equipment (UE).

The core workflow involves setting up the network components (RU bandwidth, gNB), managing the UE connection, executing performance tests (iPerf3 and ping) based on defined parameters, collecting results, and cleaning up the environment. Configuration is managed through separate files (`variable.sh`, `run_config.sh`) for clarity and ease of modification.

## Features

- **Modular Design**: Scripts are separated by function (`set_ru_bandwidth.sh`, `run_gNB.sh`, `modify_UE.sh`, `collect_data_fromCN.sh`).
- **Centralized Configuration**:
    - `variable.sh`: Stores network addresses, user credentials, and device identifiers.
    - `run_config.sh`: Stores test execution parameters like duration, bandwidth ranges, protocols, and retry counts.
- **Automated Setup**:
    - Configures RU bandwidth via SSH (`set_ru_bandwidth.sh`).
    - Starts/stops gNB processes on remote servers (`run_gNB.sh`).
    - Manages CN-side processes like iPerf server and ping (`collect_data_fromCN.sh`).
- **UE Control**: Uses ADB to toggle airplane mode, retrieve UE IP address, and run iPerf client (`modify_UE.sh`).
- **Parametric Testing**: `main.sh` orchestrates tests across specified ranges of bandwidth, protocols (TCP/UDP), and directions (Uplink/Downlink).
- **Data Collection**: Saves iPerf JSON results and ping logs for each test run.
- **Robust Execution**: Includes retry logic for establishing UE connection.

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
    ./main.sh
    ```
    The script will:
    - Source configuration variables.
    - Set RU bandwidth (if implemented in `set_ru_bandwidth.sh`).
    - Stop any existing test processes on the CN server.
    - Start the gNB components (`run_gNB.sh`).
    - Attempt to connect the UE (`modify_UE.sh`).
    - Execute the iPerf3 and ping test loop defined in `main.sh`.
    - Save results to `./data/YYYYMMDD/`.
    - Stop gNB components and clean up CN processes.
    - Turn off UE radio (airplane mode).

4.  **Output**:
    - Test results (iPerf JSON files, ping logs) are saved in `./data/YYYYMMDD/`, organized by test parameters (e.g., `iperf-dl-udp-100M-UE.json`, `ping-ul-tcp-50M.log`).
    - Console output provides real-time status updates.

## Script Details

- **`main.sh`**: Orchestrates the entire test flow. Defines the test matrix (protocols, directions, bandwidths) and calls helper scripts.
- **`variable.sh`**: Stores environment-specific variables (IPs, credentials). Sourced by `main.sh`.
- **`run_config.sh`**: Stores test execution parameters (duration, ranges, flags). Sourced by `variable.sh`.
- **[`set_ru_bandwidth.sh`](docs/set_ru_bandwidth_details.md)**: Contains functions to configure the RU (e.g., set bandwidth via SSH/expect). Called by `main.sh`. [See Details](docs/set_ru_bandwidth_details.md)
- **[`run_gNB.sh`](docs/run_gNB_details.md)**: Contains functions (`start_split_setup`, `stop_split_setup`, etc.) to manage gNB processes on remote servers via SSH. Called by `main.sh`. [See Details](docs/run_gNB_details.md)
- **[`modify_UE.sh`](docs/modify_UE_details.md)**: Contains functions (`toggle_airplane_mode`, `get_ue_ip`, `run_iperf`) to interact with the UE via ADB. Called by `main.sh`. [See Details](docs/modify_UE_details.md)
- **[`collect_data_fromCN.sh`](docs/collect_data_fromCN_details.md)**: Contains functions (`ping-start`, `ping-stop`, `iperf-start`, `iperf-stop`) to manage test processes (ping, iperf3 server) on the CN server via SSH. Called by `main.sh`. [See Details](docs/collect_data_fromCN_details.md)

## Notes and Troubleshooting

- **Dependencies**: Ensure all required tools (`sshpass`, `adb`, `iperf3`, `screen`, `expect`) are installed and in the system's PATH.
- **Permissions**: Scripts need execute permissions (`chmod +x *.sh`).
- **SSH Failures**: Verify credentials in `variable.sh` and network connectivity. Check if `sshpass` is installed or configure passwordless SSH.
- **ADB Issues**: Ensure the UE is connected, authorized, and the correct `ADB_DEVICE` is set in `run_config.sh`. Check if iPerf3 binary exists and is executable on the UE at `/data/local/tmp/iperf3`.
- **Configuration Errors**: Double-check IP addresses, usernames, passwords, and interface names in `variable.sh` and `run_config.sh`.
- **Screen Sessions**: If scripts fail unexpectedly, check for lingering `screen` sessions on the CN and gNB servers (`screen -ls`) and terminate them (`screen -X -S <session_name> quit`).

## Contributing

Contributions, bug reports, and feature requests are welcome. Please open an issue or submit a pull request.

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
