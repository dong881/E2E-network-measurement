# `collect_data_fromCN.sh` - Detailed Functions

This script contains functions for managing data collection processes (like iPerf server and ping) typically run on the Core Network (CN) server or another designated test server.

## Functions

### `iperf-start`

*   **Purpose**: Starts an iPerf3 server process on the CN server within a `screen` session for background execution.
*   **Parameters**: None.
*   **Actions**:
    1.  Connects to the CN server (`CN_SERVER_USER@CN_SERVER_HOST`) via SSH using credentials from `variable.sh`.
    2.  Executes `screen -dmS iperf-server iperf3 -s` to start an iPerf3 server in a detached screen session named "iperf-server".
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`.

### `iperf-stop <output_file>`

*   **Purpose**: Stops the iPerf3 server process running in the `screen` session on the CN server and optionally retrieves its output.
*   **Parameters**:
    *   `$1` (output\_file): The path on the **Control PC** where the iPerf3 server's output (if any) should be saved. *Note: Standard iPerf3 server output isn't typically saved to a file this way; this parameter might be intended for future use or adapted from client-side logic. The primary action is stopping the server.*
*   **Actions**:
    1.  Connects to the CN server via SSH.
    2.  Executes `screen -X -S iperf-server quit` to terminate the screen session named "iperf-server", thus stopping the iPerf3 server process.
    *   *(Optional/Potential Action): Could potentially retrieve logs if the server was started with logging options, but the current implementation likely just stops it.*
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`.

### `ping-start <target_ip>`

*   **Purpose**: Starts a continuous ping process on the CN server targeting the UE's IP address, running in a `screen` session.
*   **Parameters**:
    *   `$1` (target\_ip): The IP address to ping (typically the UE's IP stored in `$UE_IP`).
*   **Actions**:
    1.  Connects to the CN server via SSH.
    2.  Constructs the ping command. It might use a specific interface if required (e.g., `ping -I <interface> $target_ip`). The interface could be sourced from `variable.sh`. The output is redirected to a temporary file within the CN server's filesystem (e.g., `/tmp/ping_output.log`).
    3.  Executes the ping command within a detached `screen` session named "ping-session": `screen -dmS ping-session bash -c 'ping <options> $target_ip > /tmp/ping_output.log'`.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`, `INTERFACE` (potentially, for ping command).

### `ping-stop <output_file>`

*   **Purpose**: Stops the ping process running in the `screen` session on the CN server and retrieves the ping output log.
*   **Parameters**:
    *   `$1` (output\_file): The path on the **Control PC** where the collected ping results should be saved.
*   **Actions**:
    1.  Connects to the CN server via SSH.
    2.  Terminates the "ping-session" screen: `screen -X -S ping-session quit`. *Note: Need to ensure ping stops writing before retrieving the file. A small delay might be needed, or the stop command should handle this.*
    3.  Uses `sshpass scp` to copy the temporary ping log file (e.g., `/tmp/ping_output.log`) from the CN server to the specified local output file (`$output_file`).
    4.  (Optional but recommended) Removes the temporary ping log file from the CN server.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `CN_SERVER_USER`, `CN_SERVER_HOST`.
