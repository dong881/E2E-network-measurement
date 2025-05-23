# `core_network_utils.sh` - Detailed Functions

This script contains functions for managing data collection processes (like iPerf server and ping) typically run on the Core Network (CN) server or another designated test server.

## Overview

The `core_network_utils.sh` script provides functions to start and stop network measurement tools (iPerf3 and ping) on the CN server, and retrieve their output. It uses SSH to remotely control processes and `screen` sessions for persistent execution.

## Functions

### `ping-start <target_ip>`

*   **Purpose**: Starts a continuous ping process on the CN server targeting the UE's IP address, running in a `screen` session.
*   **Parameters**:
    *   `$1` (target\_ip): The IP address to ping (typically the UE's IP stored in `$UE_IP`).
*   **Actions**:
    1.  Connects to the CN server (`CN_SERVER_USER@CN_SERVER_HOST`) via SSH using credentials from `variable.sh`.
    2.  Creates a screen session named "ping-session" that runs a continuous ping command.
    3.  The ping command uses the interface specified in `$INTERFACE` (from `variable.sh`).
    4.  Each ping output line is timestamped using `date +"%s"` to add epoch timestamps.
    5.  The output is redirected to `~/ping_value.log` on the CN server.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`, `INTERFACE`.
*   **Example Call**:
    ```bash
    ping-start "10.45.0.2"
    ```
*   **Log Output**: No direct console output, but creates a timestamped ping log on the CN server.

### `ping-stop <output_file>`

*   **Purpose**: Stops the ping process running in the `screen` session on the CN server and retrieves the ping output log.
*   **Parameters**:
    *   `$1` (output\_file): The path on the local machine where the collected ping results should be saved.
*   **Actions**:
    1.  Connects to the CN server via SSH.
    2.  Terminates the "ping-session" screen: `screen -X -S ping-session quit`.
    3.  Uses `sshpass scp` to copy the ping log file (`~/ping_value.log`) from the CN server to the specified local output file (`$output_file`).
    4.  If no output file is specified, defaults to `~/ping_results.log`.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`.
*   **Example Call**:
    ```bash
    ping-stop "/home/ming/E2E-network-measurement/data/ping-dl-udp-100M.log"
    ```
*   **Log Output**: No direct console output, but transfers the ping log to the specified file.

### `iperf-start`

*   **Purpose**: Starts an iPerf3 server process on the CN server within a `screen` session for background execution.
*   **Parameters**: None.
*   **Actions**:
    1.  Connects to the CN server via SSH.
    2.  Creates a processing script on the CN server that:
        - Records the current timestamp using `date +"%s"`
        - Starts iPerf3 server with JSON output (`-J` option)
        - Uses `sed` to insert the start timestamp into the JSON output
        - Saves the result to `~/iperf-server.json`
    3.  Makes the script executable
    4.  Starts the script in a detached screen session named "iperf-server"
    5.  Waits 1 second for the server to start
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`.
*   **Example Call**:
    ```bash
    iperf-start
    ```
*   **Log Output**: No direct console output, but creates an iPerf server process on the CN server.

### `iperf-stop <output_file>`

*   **Purpose**: Stops the iPerf3 server process running in the `screen` session on the CN server and optionally retrieves its output.
*   **Parameters**:
    *   `$1` (output\_file): Optional. The path on the local machine where the iPerf3 server's output should be saved.
*   **Actions**:
    1.  If an output file is specified, copies the iPerf server's JSON output from the CN server to the local machine.
    2.  Connects to the CN server via SSH.
    3.  Executes `screen -X -S iperf-server quit` to terminate the screen session named "iperf-server", thus stopping the iPerf3 server process.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`.
*   **Example Call**:
    ```bash
    iperf-stop "/home/ming/E2E-network-measurement/data/iperf-dl-udp-100M-CN.json"
    ```
*   **Log Output**: No direct console output, but may transfer the iPerf server log to the specified file.

## Implementation Details

The script uses:

1. **SSH** for remote command execution on the CN server
2. **Screen** for background process management
3. **SCP** for file transfer back to the local machine
4. **Custom shell scripts** generated on-the-fly for timestamp handling and data processing

Key techniques employed:
- Using `screen` sessions to keep processes running after SSH disconnects
- Adding timestamps to ping data for correlation with throughput measurements
- Using JSON format for iPerf output to enable structured data analysis
- Modifying JSON files on-the-fly to add metadata like start timestamps

## Usage Notes

- The script requires SSH access to the CN server with password authentication via `sshpass`
- The CN server must have `screen` and `iperf3` installed
- For ping tests, the specified interface must exist and be properly configured
- Sufficient disk space must be available on both CN server and local machine for logs
