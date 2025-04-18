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
    2.  Parses the output (e.g., using `grep` and `awk` or `sed`) to find the IP address associated with the mobile data interface.
    3.  Exports the found IP address to the `UE_IP` environment variable, making it available to the calling script (`main.sh`). If no IP is found, `UE_IP` remains empty or is explicitly cleared.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `ADB_DEVICE`.
*   **Environment Variables Set**: `UE_IP`.

### `run_iperf <client|server> <target_ip> "<params>" <output_file>`

*   **Purpose**: Executes the iPerf3 client on the UE.
*   **Parameters**:
    *   `$1`: Mode - Should be "client" when called from `main.sh` to run the UE as the iPerf client.
    *   `$2` (target\_ip): The IP address of the iPerf3 server (e.g., `TEST_SERVER_IP` from `variable.sh`).
    *   `$3` (params): A string containing the iPerf3 command-line parameters (e.g., `-b 100M -t 30 -J -R`).
    *   `$4` (output\_file): The path on the **Control PC** where the iPerf3 JSON output should be saved.
*   **Actions**:
    1.  Constructs the iPerf3 command to be run on the UE: `/data/local/tmp/iperf3 -c <target_ip> <params>`.
    2.  Uses `adb -s $ADB_DEVICE shell` to execute the iPerf3 command on the UE.
    3.  Redirects the standard output (which contains the JSON results when `-J` is used) from the `adb shell` command to the specified local output file (`> "$output_file"`).
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `ADB_DEVICE`.
