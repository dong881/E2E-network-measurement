# `modify_UE.sh` - Detailed Functions

This script contains functions for interacting with the connected Android User Equipment (UE) via the Android Debug Bridge (ADB).

## Functions

### `toggle_airplane_mode <on|off>`

*   **Purpose**: Enables or disables airplane mode on the UE. This is often used to force the UE to disconnect and reconnect to the network.
*   **Parameters**:
    *   `$1`: The desired state - "on" to enable airplane mode, "off" to disable it.
*   **Actions**:
    1.  Uses `adb -s $ADB_DEVICE shell` to execute commands on the target UE.
    2.  Broadcasts an intent to change the airplane mode state (`am broadcast -a android.settings.AIRPLANE_MODE_SETTINGS`).
    3.  Sends key events (`input keyevent`) to simulate button presses for confirming the change if necessary (specific keycodes might vary by Android version/device).
    4.  Sets the global airplane mode setting (`settings put global airplane_mode_on`).
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `ADB_DEVICE`.

### `get_ue_ip`

*   **Purpose**: Retrieves the IP address assigned to the UE's mobile data interface (typically `rmnet_data0` or similar).
*   **Actions**:
    1.  Uses `adb -s $ADB_DEVICE shell ip addr show` to list network interfaces and their addresses on the UE.
    2.  Filters the output to find and extract the IP address associated with the mobile data interface.
    3.  Stores the found IP address in the `UE_IP` environment variable.
    4.  If no IP is found, displays an error message.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `ADB_DEVICE`.
*   **Environment Variables Set**: `UE_IP`.

### `run_iperf <client|server> <target_ip> "<params>" <output_file>`

*   **Purpose**: Executes the iPerf3 client or server on the UE device.
*   **Parameters**:
    *   `$1`: Mode - "client" to run as an iPerf client, "server" to run as an iPerf server.
    *   `$2` (target\_ip): The IP address of the iPerf3 server when in client mode.
    *   `$3` (params): String containing iPerf3 command-line parameters.
    *   `$4` (output\_file): Path on the Control PC where to save the iPerf3 output (optional).
*   **Actions**:
    1.  Checks if the iPerf3 binary exists on the UE at `/data/local/tmp/iperf3`.
    2.  If not found, uploads it from the control PC to the UE.
    3.  Makes the binary executable on the UE.
    4.  If in server mode, starts the iPerf3 server on the UE.
    5.  If in client mode, runs the iPerf3 client against the specified server IP.
    6.  If an output file is specified, saves the results to that file on the control PC.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `ADB_DEVICE`, `UE_IP`.
