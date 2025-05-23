# `user_equipment_utils.sh` - Detailed Functions

This script contains functions for interacting with the connected Android User Equipment (UE) via the Android Debug Bridge (ADB).

## Overview

The `user_equipment_utils.sh` script provides functions to control and interact with the User Equipment (UE), which is typically an Android smartphone or device connected via ADB. It handles connectivity management (airplane mode), IP address retrieval, and performance testing (running iPerf3 client).

## Functions

### `toggle_airplane_mode <on|off>`

*   **Purpose**: Enables or disables airplane mode on the UE. This is often used to force the UE to disconnect and reconnect to the network.
*   **Parameters**:
    *   `$1`: The desired state - "on" to enable airplane mode, "off" to disable it.
*   **Actions**:
    1.  Connects to the Control PC where the UE is attached via USB.
    2.  Uses `adb -s $ADB_DEVICE shell` to execute commands on the target UE.
    3.  Sets the global airplane mode setting (`settings put global airplane_mode_on 0/1`).
    4.  Broadcasts an intent to update the airplane mode state (`am broadcast -a android.intent.action.AIRPLANE_MODE`).
    5.  Waits 5 seconds for the change to take effect.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `CONTROL_PC_USER`, `CONTROL_PC_IP`, `SERVER_PASSWORD`, `ADB_DEVICE`, `SSH_OPTIONS`.
*   **Example Call**:
    ```bash
    toggle_airplane_mode "on"   # Enable airplane mode
    toggle_airplane_mode "off"  # Disable airplane mode
    ```
*   **Log Output Example**:
    ```
    Setting airplane mode to on on sshuser@140.118.162.81
    Setting airplane mode to off on sshuser@140.118.162.81
    ```

### `get_ue_ip`

*   **Purpose**: Retrieves the IP address assigned to the UE's mobile data interface and stores it in the `UE_IP` variable.
*   **Parameters**: None.
*   **Actions**:
    1.  Connects to the Control PC via SSH.
    2.  Executes `adb -s $ADB_DEVICE shell ip -f inet addr show` to list network interfaces on the UE.
    3.  Uses `awk` and `cut` to extract the IP address from the appropriate interface (ccmni0 or ccmni1).
    4.  Stores the found IP address in the `UE_IP` environment variable.
    5.  Displays the UE IP to console for confirmation.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `CONTROL_PC_USER`, `CONTROL_PC_IP`, `SERVER_PASSWORD`, `ADB_DEVICE`, `SSH_OPTIONS`.
*   **Environment Variables Set**: `UE_IP`.
*   **Example Call**:
    ```bash
    get_ue_ip
    echo "UE IP address is $UE_IP"
    ```
*   **Log Output Example**:
    ```
    UE IP: 10.45.0.2
    ```

### `run_iperf <client|server> <target_ip> "<params>" <output_file>`

*   **Purpose**: Executes the iPerf3 client or server on the UE device.
*   **Parameters**:
    *   `$1`: Mode - "client" to run as an iPerf client, "server" to run as an iPerf server.
    *   `$2` (target\_ip): The IP address of the iPerf3 server when in client mode.
    *   `$3` (params): String containing iPerf3 command-line parameters.
    *   `$4` (output\_file): Path on the local machine where to save the iPerf3 output (optional).
*   **Actions**:
    1.  Connects to the Control PC via SSH.
    2.  Checks if the iPerf3 binary exists on the UE at `/data/local/tmp/iperf3`.
    3.  If not found, uploads it from the control PC to the UE.
    4.  Makes the binary executable on the UE.
    5.  If in server mode, starts the iPerf3 server on the UE.
    6.  If in client mode:
        - Runs the iPerf3 client against the specified server IP.
        - If an output file is specified:
          - Saves the output to a temporary file on the UE
          - Pulls the file to the Control PC
          - Copies it from the Control PC to the local machine
          - Cleans up the temporary file on the UE
    7.  Ensures the UE IP is available by calling `get_ue_ip` if it's not already set.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `CONTROL_PC_USER`, `CONTROL_PC_IP`, `SERVER_PASSWORD`, `ADB_DEVICE`, `UE_IP`, `control_pc_iperf_path`, `SSH_OPTIONS`.
*   **Example Calls**:
    ```bash
    # Run iPerf server on UE
    run_iperf "server" "" "-p 5201"
    
    # Run iPerf client on UE with specified parameters
    run_iperf "client" "10.45.0.1" "-u -b 100M -t 30" "/home/ming/E2E-network-measurement/data/iperf_results.json"
    ```
*   **Log Output Example**:
    ```
    Running iperf3 in client mode…
    UE IP: 10.45.0.2
    Running iperf3 client on UE device...
    Results saved to /home/ming/E2E-network-measurement/data/iperf_results.json
    ```

## Implementation Details

The script uses a combination of:
1. SSH to connect to the Control PC
2. ADB commands executed on the Control PC to control the UE
3. File transfers between the UE, Control PC, and local machine

It handles multiple error cases, such as:
- UE IP not being available
- iPerf3 binary not existing on the UE
- ADB connection issues

## Usage Notes

- The script requires the ADB device ID to be correctly set in `run_config.sh`
- The Control PC must have ADB installed and accessible in its PATH
- The UE must be connected to the Control PC via USB with debugging enabled
- For file transfers to work, the Control PC must have sufficient permissions and disk space
- The `control_pc_iperf_path` variable should point to the location of the iPerf3 binary on the Control PC
