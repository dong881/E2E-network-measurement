# `radio_unit_utils.sh` - Detailed Functions

This script contains functions for interacting with and configuring the Radio Unit (RU) device, primarily via SSH.

## Overview

The `radio_unit_utils.sh` script provides automation for configuring bandwidth settings on Radio Units. It uses the `expect` utility to handle interactive SSH sessions, making it possible to automate the configuration process that would normally require manual CLI interaction.

## Functions

### `radio_unit_utils <bandwidth_bps>`

*   **Purpose**: Configures the bandwidth setting on the RU device and potentially reboots it.
*   **Parameters**:
    *   `$1` (bandwidth\_bps): The desired bandwidth in bits per second (e.g., "100000000" for 100 Mbps).
*   **Actions**:
    1.  Connects to the RU device using SSH credentials defined in `variable.sh` (`RU_USER`, `RU_IP`, `RU_PASSWORD`, `RU_ENABLE_PASSWORD`).
    2.  Uses `expect` to automate the login process and enter enable mode.
    3.  Executes RU-specific commands to set the desired bandwidth. (Note: Actual commands depend on the RU model/firmware).
    4.  Checks if the bandwidth was changed by comparing with the previous value.
    5.  If the bandwidth was changed, it reboots the RU and waits for the reboot to complete.
    6.  Waits for a specified duration (`WAIT_AFTER_REBOOT` from `run_config.sh`) after rebooting.
*   **Called By**: `main.sh` (potentially, based on comments).
*   **Environment Variables Used**: `RU_IP`, `RU_USER`, `RU_PASSWORD`, `RU_ENABLE_PASSWORD`, `WAIT_AFTER_REBOOT`, `OUTPUT_DIR`.

## Implementation Details

The function creates and executes an `expect` script to handle the interactive SSH session. The expect script:

1. Spawns an SSH connection to the RU
2. Handles username/password authentication
3. Enters enable mode with the appropriate password
4. Checks current configuration
5. Enters configuration terminal mode
6. Sets the requested bandwidth
7. Checks if the bandwidth was changed
8. Reboots the RU if the bandwidth was changed
9. Waits for the reboot process to complete

## Usage Example

```bash
# Set RU bandwidth to 100 Mbps
radio_unit_utils "100000000"

# Set RU bandwidth to 40 Mbps
radio_unit_utils "40000000"
```

## Error Handling

The script includes several error handling mechanisms:

1. Creates the output directory if it doesn't exist to store logs
2. Properly sets executable permissions on the generated expect script
3. Exports all necessary environment variables to the expect script
4. Checks if the RU is rebooting and provides appropriate messaging
5. Waits for the specified duration after reboot to ensure the RU is fully operational

## Output

The script generates two output files in the `$OUTPUT_DIR` directory:
- `set_bandwidth.exp`: The generated expect script
- `set_bandwidth.out`: The output log from the expect script execution

These files can be examined for troubleshooting if the bandwidth setting process fails.

## Notes

- The exact implementation within the `expect` block needs to be tailored to the specific command-line interface of the target RU device
- The `WAIT_AFTER_REBOOT` variable should be set to a reasonable value based on the RU's typical reboot time
- The script assumes the RU has a command-line interface accessible via SSH
- Valid bandwidth values depend on the specific RU hardware capabilities
