# `run_gNB.sh` - Detailed Functions

This script manages the lifecycle of gNodeB (gNB) processes running on one or more remote servers. It handles starting and stopping different gNB configurations (e.g., split VNF/PNF, monolithic).

## Functions

### `start_split_setup <bandwidth_config>`

*   **Purpose**: Starts the gNB components in a split configuration (e.g., separate VNF/CU and PNF/DU).
*   **Parameters**:
    *   `$1` (bandwidth\_config): A string identifier for the current bandwidth configuration (e.g., "100M"). This might be used for logging or potentially selecting configuration files if needed, although its direct use isn't shown in `main.sh`.
*   **Actions**:
    1.  Connects via SSH to the VNF/gNB server (`VNF_GNB_SERVER_USER@VNF_GNB_SERVER_HOST`) using credentials from `variable.sh`.
    2.  Executes commands to start the VNF/CU component (e.g., running a specific script within a `screen` session).
    3.  Connects via SSH to the PNF/gNB server (`GNB_SERVER_USER@GNB_SERVER_HOST`).
    4.  Executes commands to start the PNF/DU component (e.g., running another script in `screen`).
    5.  Waits for a specified duration (`WAIT_AFTER_GNB` from `run_config.sh`) to allow gNB components to initialize.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `VNF_GNB_SERVER_USER`, `VNF_GNB_SERVER_HOST`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`, `WAIT_AFTER_GNB`.

### `stop_split_setup <bandwidth_config>`

*   **Purpose**: Stops the gNB components running in a split configuration.
*   **Parameters**:
    *   `$1` (bandwidth\_config): String identifier (e.g., "100M"). Primarily for logging or consistency.
*   **Actions**:
    1.  Connects via SSH to the VNF/gNB server.
    2.  Sends commands to terminate the VNF/CU process (e.g., killing a `screen` session or running a stop script).
    3.  Connects via SSH to the PNF/gNB server.
    4.  Sends commands to terminate the PNF/DU process.
*   **Called By**: `main.sh`.
*   **Environment Variables Used**: `SERVER_PASSWORD`, `VNF_GNB_SERVER_USER`, `VNF_GNB_SERVER_HOST`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`.

### `start_single_setup <bandwidth_config> <mode>`

*   **Purpose**: Starts the gNB in a monolithic (single server) configuration.
*   **Parameters**:
    *   `$1` (bandwidth\_config): String identifier (e.g., "100M").
    *   `$2` (mode): String identifier for the mode (e.g., "MONO").
*   **Actions**:
    1.  Connects via SSH to the designated gNB server (`GNB_SERVER_USER@GNB_SERVER_HOST`).
    2.  Executes commands to start the monolithic gNB process (e.g., within a `screen` session).
    3.  Waits for `WAIT_AFTER_GNB`.
*   **Called By**: `main.sh` (commented out).
*   **Environment Variables Used**: `SERVER_PASSWORD`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`, `WAIT_AFTER_GNB`.

### `stop_single_setup <bandwidth_config> <mode>`

*   **Purpose**: Stops the gNB running in a monolithic configuration.
*   **Parameters**:
    *   `$1` (bandwidth\_config): String identifier.
    *   `$2` (mode): String identifier.
*   **Actions**:
    1.  Connects via SSH to the gNB server.
    2.  Sends commands to terminate the monolithic gNB process.
*   **Called By**: `main.sh` (commented out).
*   **Environment Variables Used**: `SERVER_PASSWORD`, `GNB_SERVER_USER`, `GNB_SERVER_HOST`.
