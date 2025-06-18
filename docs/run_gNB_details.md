# `gnb_utils.sh` - Detailed Functions

This script manages the lifecycle of gNodeB (gNB) processes running on one or more remote servers. It handles starting and stopping different gNB configurations (e.g., split VNF/PNF, monolithic, single-machine NFAPI).

## Overview

The `gnb_utils.sh` script provides functions to manage the 5G gNodeB (gNB) components, supporting three deployment modes:
1. **Monolithic**: Single-server deployment with all gNB functions in one process
2. **NFAPI Split**: Separate VNF/CU and PNF/DU processes on different servers
3. **NFAPI Single-Machine**: Separate VNF/CU and PNF/DU processes on the same server with isolated log files

It uses SSH to remotely control processes and `screen` sessions for persistent execution.

## Configuration Variables

The script defines multiple configuration variables:
- **Server credentials**: Password, user and host information for VNF/PNF servers
- **Base paths**: Locations of OpenAirInterface (OAI) installations on different servers
- **Configuration files**: Paths to different gNB configuration files for various bandwidths and modes
- **Command templates**: Pre-configured command strings for different deployment scenarios

## Core Functions

### General Functions

#### `start_session <session_name> <command> <target_user> <target_host>`
- **Purpose**: Starts a command in a detached screen session on a remote server
- **Parameters**:
  - `$1` (session_name): Name for the screen session
  - `$2` (command): Command to execute
  - `$3` (target_user): SSH username
  - `$4` (target_host): SSH host
- **Actions**: Uses `sshpass` and `ssh` to create a detached screen session running the specified command

#### `stop_session <session_name> <target_user> <target_host>`
- **Purpose**: Stops a screen session on a remote server
- **Parameters**:
  - `$1` (session_name): Name of the screen session to stop
  - `$2` (target_user): SSH username
  - `$3` (target_host): SSH host
- **Actions**: Uses `sshpass` and `ssh` to send a quit command to the specified screen session

### Split Machine Setup Functions

#### `start_split_setup <bandwidth_config>`

*   **Purpose**: Starts the gNB components in a split configuration (e.g., separate VNF/CU and PNF/DU).
*   **Parameters**:
    *   `$1` (bandwidth\_config): A string identifier for the current bandwidth configuration (e.g., "100M" or "40M").
*   **Actions**:
    1.  Connects via SSH to the VNF/gNB server (`VNF_GNB_SERVER_USER@VNF_GNB_SERVER_HOST`) using credentials from `variable.sh`.
    2.  Executes commands to start the VNF/CU component (e.g., running a specific script within a `screen` session).
    3.  Connects via SSH to the PNF/gNB server (`GNB_SERVER_USER@GNB_SERVER_HOST`).
    4.  Executes commands to start the PNF/DU component (e.g., running another script in `screen`).
    5.  The specific commands executed depend on the bandwidth configuration (100M or 40M).
*   **Called By**: `start_gNB` or directly from `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `VNF_GNB_SERVER_USER`, `VNF_GNB_SERVER_HOST`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`.

#### `stop_split_setup <bandwidth_config>`

*   **Purpose**: Stops the gNB components running in a split configuration.
*   **Parameters**:
    *   `$1` (bandwidth\_config): String identifier (e.g., "100M" or "40M").
*   **Actions**:
    1.  Connects via SSH to the VNF/gNB server.
    2.  Sends commands to terminate the VNF/CU process (stopping the appropriate screen session).
    3.  Connects via SSH to the PNF/gNB server.
    4.  Sends commands to terminate the PNF/DU process.
*   **Called By**: `stop_gNB` or directly from `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `VNF_GNB_SERVER_USER`, `VNF_GNB_SERVER_HOST`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`.

### Single Machine NFAPI Setup Functions

#### `start_single_machine_nfapi_setup <bandwidth_config>`

*   **Purpose**: Starts the gNB components in NFAPI mode on a single server with separate log files.
*   **Parameters**:
    *   `$1` (bandwidth\_config): A string identifier for the current bandwidth configuration (e.g., "100M" or "40M").
*   **Actions**:
    1.  Connects via SSH to the gNB server (`GNB_SERVER_USER@GNB_SERVER_HOST`).
    2.  Executes commands to start the VNF/CU component in a separate screen session with isolated log file.
    3.  Executes commands to start the PNF/DU component in another screen session with its own log file.
    4.  Uses single-machine specific configuration files to ensure proper local communication.
*   **Log Files**: Uses `$VNF_LOG_FILE_SINGLE` and `$PNF_LOG_FILE_SINGLE` to avoid conflicts.
*   **Called By**: `start_gNB` when `SINGLE_MACHINE_MODE=true`.

#### `stop_single_machine_nfapi_setup <bandwidth_config>`

*   **Purpose**: Stops the gNB components running in single-machine NFAPI mode.
*   **Parameters**:
    *   `$1` (bandwidth\_config): String identifier (e.g., "100M" or "40M").
*   **Actions**:
    1.  Connects via SSH to the gNB server.
    2.  Sends commands to terminate both VNF/CU and PNF/DU processes running in separate screen sessions.
*   **Called By**: `stop_gNB` when `SINGLE_MACHINE_MODE=true`.

### Single Machine Setup Functions

#### `start_single_setup <bandwidth_config> <mode>`

*   **Purpose**: Starts the gNB in a monolithic (single server) configuration or single-machine NFAPI mode.
*   **Parameters**:
    *   `$1` (bandwidth\_config): String identifier (e.g., "100M" or "40M").
    *   `$2` (mode): String identifier for the mode (e.g., "NFAPI", "NFAPI-SingleMachine", or "Monolithic").
*   **Actions**:
    1.  Connects via SSH to the designated gNB server (`GNB_SERVER_USER@GNB_SERVER_HOST`).
    2.  Executes commands to start the appropriate gNB process (VNF, PNF, or monolithic) based on mode and bandwidth.
*   **Called By**: `start_gNB` or directly from `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`.

#### `stop_single_setup <bandwidth_config> <mode>`

*   **Purpose**: Stops the gNB running in a monolithic configuration or single-machine NFAPI mode.
*   **Parameters**:
    *   `$1` (bandwidth\_config): String identifier (e.g., "100M" or "40M").
    *   `$2` (mode): String identifier for the mode (e.g., "NFAPI", "NFAPI-SingleMachine", or "Monolithic").
*   **Actions**:
    1.  Connects via SSH to the gNB server.
    2.  Sends commands to terminate the appropriate gNB process based on mode and bandwidth.
*   **Called By**: `stop_gNB` or directly from `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`.

### High-Level Wrapper Functions

#### `start_gNB [mode]`
- **Purpose**: High-level function to start gNB based on mode
- **Parameters**:
  - `$1` (mode): Optional. Mode to use (Monolithic or NFAPI). Defaults to CURRENT_MODE.
- **Actions**: Calls either `start_single_setup` for Monolithic mode or `start_split_setup` for other modes

#### `stop_gNB [mode]`
- **Purpose**: High-level function to stop gNB based on mode
- **Parameters**:
  - `$1` (mode): Optional. Mode to stop (Monolithic or NFAPI). Defaults to CURRENT_MODE.
- **Actions**: Calls either `stop_single_setup` for Monolithic mode or `stop_split_setup` for other modes

### Log Management Functions

#### `reset_all [mode]`
- **Purpose**: Comprehensive reset function that stops all processes and cleans logs
- **Parameters**:
  - `$1` (mode): Optional. Mode to reset. If not specified, attempts to reset all modes.
- **Actions**:
  1. Stops gNB processes
  2. Cleans log files
  3. Stops sessions on CN server
  4. Executes any required remote scripts on the main host

## Usage Examples

```bash
# Start gNB in monolithic mode
start_gNB "Monolithic"

# Stop gNB in NFAPI mode
stop_gNB "NFAPI"

# Start gNB in single-machine NFAPI mode
SINGLE_MACHINE_MODE=true start_gNB "NFAPI"

# Reset all components
reset_all
```

## Important Notes

- The script relies on several environment variables defined in `variable.sh` and `run_config.sh`
- The `screen` utility must be installed on all remote servers
- SSH access must be configured correctly for password authentication via `sshpass`
- Proper path configuration is essential for finding executables and configuration files on remote servers
- The script assumes specific directory structures for OpenAirInterface installations
- **Single-Machine Mode**: Uses separate log files (`$VNF_LOG_FILE_SINGLE` and `$PNF_LOG_FILE_SINGLE`) to avoid conflicts
- **Configuration Files**: Single-machine mode requires specific config files with local IP addresses for VNF-PNF communication
