# `set_ru_bandwidth.sh` - Detailed Functions

This script contains functions for interacting with and configuring the Radio Unit (RU) device, primarily via SSH.

## Functions

### `set_ru_bandwidth <bandwidth_bps>`

*   **Purpose**: Configures the bandwidth setting on the RU device and potentially reboots it.
*   **Parameters**:
    *   `$1` (bandwidth\_bps): The desired bandwidth in bits per second (e.g., "100000000" for 100 Mbps).
*   **Actions**:
    1.  Connects to the RU device using SSH credentials defined in `variable.sh` (`RU_USER`, `RU_IP`, `RU_PASSWORD`, `RU_ENABLE_PASSWORD`).
    2.  Uses `expect` to automate the login process and enter enable mode.
    3.  Executes RU-specific commands to set the desired bandwidth. (Note: Actual commands depend on the RU model/firmware).
    4.  May include a command to save the configuration and reboot the RU.
    5.  Waits for a specified duration (`WAIT_AFTER_REBOOT` from `run_config.sh`) after rebooting.
*   **Called By**: `main.sh` (potentially, based on comments).
*   **Environment Variables Used**: `RU_IP`, `RU_USER`, `RU_PASSWORD`, `RU_ENABLE_PASSWORD`, `WAIT_AFTER_REBOOT`.

*Note: The exact implementation within the `expect` block needs to be tailored to the specific command-line interface of the target RU device.*
