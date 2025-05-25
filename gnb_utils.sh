#!/bin/bash

# Global variables
source variable.sh

# Commands for Single Machine Setup
# Define common paths and options
BUILD_DIR="$PNF_BASE_PATH/cmake_targets/ran_build/build"
CONF_DIR="$PNF_BASE_PATH/targets/PROJECTS/GENERIC-NR-5GC/CONF"

# Common options
SUDO_PREFIX="echo '$SERVER_PASSWORD' | sudo -S"
THREAD_OPTS="--thread-pool 1,3,5,7,9,11,13,15"
NFAPI_TRACE="NFAPI_TRACE_LEVEL=info"
COMMON_CMD="cd $BUILD_DIR && $SUDO_PREFIX"

# Mode-specific options
VNF_OPTS="--nfapi VNF"
PNF_OPTS="--nfapi PNF --reorder-thread-disable 1 $THREAD_OPTS"
MONO_OPTS="$THREAD_OPTS"

# Config files
CONF_VNF_100M="gnb-vnf.sa.band78.273prb.nfapi.conf"
CONF_VNF_40M="gnb-vnf.sa.band78.106prb.nfapi.conf"
CONF_MONO_100M="gnb.sa.band78.273prb.fhi72.4x4-liteon_new.conf"
CONF_MONO_100M_JURA="gnb.sa.band78.273prb.fhi72.4x4-metanoia.conf"
CONF_MONO_40M="gnb.sa.band78.106prb.fhi72.4x4-liteon_new.conf"
# CONF_PNF="gnb-pnf.band78.fhi72.4x4-liteon_new.conf"
CONF_PNF="gnb-pnf.sa.band78.fhi72.nfapi.4x4-metanoia.conf"

# Commands for Single Machine Setup
CMD_VNF_100M_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_VNF_100M $VNF_OPTS"
CMD_VNF_40M_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_VNF_40M $VNF_OPTS"
CMD_MONO_100M_SINGLE="$COMMON_CMD ./nr-softmodem -O $CONF_DIR/$CONF_MONO_100M $MONO_OPTS"
CMD_MONO_40M_SINGLE="$COMMON_CMD ./nr-softmodem -O $CONF_DIR/$CONF_MONO_40M $MONO_OPTS"
CMD_MONO_100M_JURA_SINGLE="$COMMON_CMD ./nr-softmodem -O $CONF_DIR/$CONF_MONO_100M_JURA $MONO_OPTS"
CMD_PNF_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_PNF $PNF_OPTS"

# Additional config files
CONF_PNF_SPLIT="gnb-pnf.sa.band78.fhi72.nfapi.4x4-metanoia.conf"

# Common command prefixes for split setup
VNF_SPLIT_CMD_PREFIX="cd $VNF_BASE_PATH/cmake_targets/ran_build/build && echo '$SERVER_PASSWORD' | sudo -S $NFAPI_TRACE"
PNF_SPLIT_CMD_PREFIX="cd $PNF_BASE_PATH/cmake_targets/ran_build/build && echo '$SERVER_PASSWORD' | sudo -S $NFAPI_TRACE"

# Commands for Split Machine Setup (Two Machines)
CMD_VNF_100M_SPLIT="$VNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_100M $VNF_OPTS"
CMD_VNF_40M_SPLIT="$VNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_40M $VNF_OPTS"
CMD_PNF_SPLIT="$PNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_PNF_SPLIT $PNF_OPTS"

# Function to start a screen session
start_session() {
    local session_name=$1
    local command=$2
    local target_user=$3
    local target_host=$4
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "screen -dmS $session_name bash -c '$command &> ~/ming.log'"
}

# Function to stop a screen session
stop_session() {
    local session_name=$1
    local target_user=$2
    local target_host=$3
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "screen -X -S $session_name quit"
}

# Function to start split machine setup
start_split_setup() {
    local bandwidth=$1  # 100M or 40M
    
    if [ "$bandwidth" = "100M" ]; then
        start_session "VNF_100M" "$CMD_VNF_100M_SPLIT" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        start_session "PNF" "$CMD_PNF_SPLIT" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    elif [ "$bandwidth" = "40M" ]; then
        start_session "VNF_40M" "$CMD_VNF_40M_SPLIT" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        start_session "PNF" "$CMD_PNF_SPLIT" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    fi
}

# Function to start single machine setup
start_single_setup() {
    local bandwidth=$1  # 100M or 40M
    local mode=$2      # NFAPI or MONO
    
    if [ "$bandwidth" = "100M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            start_session "VNF_100M" "$CMD_VNF_100M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            start_session "PNF" "$CMD_PNF_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            # start_session "MONO_100M" "$CMD_MONO_100M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            start_session "MONO_100M" "$CMD_MONO_100M_JURA_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    elif [ "$bandwidth" = "40M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            start_session "VNF_40M" "$CMD_VNF_40M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            start_session "PNF" "$CMD_PNF_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            start_session "MONO_40M" "$CMD_MONO_40M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    fi
}

### ------------------------------------------------------------------------------------------------

# Example usage of all possible function combinations

# Split machine setup (VNF + PNF)
# start_split_setup "100M"    # 100M bandwidth
# start_split_setup "40M"     # 40M bandwidth

# Single machine setup (NFAPI mode)
# start_single_setup "100M" "NFAPI"    # 100M bandwidth
# start_single_setup "40M" "NFAPI"     # 40M bandwidth

# Single machine setup (MONO mode)
# start_single_setup "100M" "MONO"    # 100M bandwidth
# start_single_setup "40M" "MONO"     # 40M bandwidth

# Stop sessions
# Function to stop split machine setup
stop_split_setup() {
    local bandwidth=$1  # 100M or 40M
    
    if [ "$bandwidth" = "100M" ]; then
        stop_session "VNF_100M" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    elif [ "$bandwidth" = "40M" ]; then
        stop_session "VNF_40M" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    fi
}

# Function to stop single machine setup
stop_single_setup() {
    local bandwidth=$1  # 100M or 40M
    local mode=$2      # NFAPI or MONO
    
    if [ "$bandwidth" = "100M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            stop_session "VNF_100M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            stop_session "MONO_100M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    elif [ "$bandwidth" = "40M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            stop_session "VNF_40M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            stop_session "MONO_40M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    fi
}

start_gNB() {
    local mode=${1:-$CURRENT_MODE}  # Use provided mode or default to CURRENT_MODE
    if [ "$mode" = "MONO" ]; then
        start_single_setup "100M" "MONO"
    else
        start_split_setup "100M"
    fi
}

stop_gNB() {
    local mode=${1:-$CURRENT_MODE}  # Use provided mode or default to CURRENT_MODE
    if [ "$mode" = "MONO" ]; then
        stop_single_setup "100M" "MONO"
    else
        stop_split_setup "100M"
    fi
}

# Function to fetch log files and analyze them
fetch_and_analyze_logs() {
    local mode=$1  # "MONO" or "NFAPI"

    # Create measurement directory if it doesn't exist
    mkdir -p $LOCAL_MEASURE_DIR
    
    if [ "$mode" = "MONO" ]; then
        # For Monolithic mode
        local vnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        local vnf_local_log="$LOCAL_MEASURE_DIR/monolithic-$VNF_LOG_FILE"
        local pnf_local_log="$LOCAL_MEASURE_DIR/monolithic-$PNF_LOG_FILE"
        
        echo "Fetching VNF logs from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$vnf_remote_log" "$vnf_local_log"
        
        echo "Fetching PVNF logs from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$pnf_remote_log" "$pnf_local_log"

        if [ -f "$vnf_local_log" ] && [ -f "$pnf_local_log" ]; then
            echo "Successfully copied VNF and PNF logs"
            python $LOG_ANALYSIS_SCRIPT "$vnf_local_log" "$pnf_local_log"
        else
            echo "Failed to copy one or more log files"
        fi
    elif [ "$mode" = "NFAPI" ]; then
        # For NFAPI mode (need both VNF and PNF logs)
        local vnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        local vnf_local_log="$LOCAL_MEASURE_DIR/nfapi-$VNF_LOG_FILE"
        local pnf_local_log="$LOCAL_MEASURE_DIR/nfapi-$PNF_LOG_FILE"
        
        echo "Fetching VNF logs from $VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST:$vnf_remote_log" "$vnf_local_log"
        
        echo "Fetching PNF logs from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$pnf_remote_log" "$pnf_local_log"
        
        if [ -f "$vnf_local_log" ] && [ -f "$pnf_local_log" ]; then
            echo "Successfully copied VNF and PNF logs"
            python $LOG_ANALYSIS_SCRIPT "$vnf_local_log" "$pnf_local_log"
        else
            echo "Failed to copy one or more log files"
        fi
    else
        echo "Invalid mode. Please specify either 'MONO' or 'NFAPI'."
    fi
}

# Function to clean log files on servers
clean_log_files() {
    local mode=$1  # "MONO" or "NFAPI"    
    if [ "$mode" = "MONO" ]; then
        # For Monolithic mode, both logs are on the same server
        local vnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        
        echo "Removing VNF and PNF logs from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        # Execute with a direct command string that handles the password prompt
        sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "echo $SERVER_PASSWORD | sudo -S rm -f $vnf_remote_log $pnf_remote_log"
        
    elif [ "$mode" = "NFAPI" ]; then
        # For NFAPI mode, logs are on different servers
        local vnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        
        echo "Removing VNF log from $VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST..."
        # Adding -t option to allocate a pseudo-terminal
        sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no $VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST "echo $SERVER_PASSWORD | sudo -S rm -f $vnf_remote_log"
        
        echo "Removing PNF log from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        # Adding -t option to allocate a pseudo-terminal
        sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "echo $SERVER_PASSWORD | sudo -S rm -f $pnf_remote_log"
        
    else
        echo "Invalid mode. Please specify either 'MONO' or 'NFAPI'."
    fi
}

# Function to reset all states and prepare for a clean start
reset_all() {
    local mode=${1:-$CURRENT_MODE}
    
    # Stop any running sessions on the gNB server
    if [ -n "$mode" ]; then
        stop_gNB "$mode"
        clean_log_files "$mode"
    else
        # If no mode is specified, try to stop both modes
        echo "Stopping gNB in both MONO and NFAPI modes..."
        stop_single_setup "100M" "MONO"
        stop_single_setup "40M" "MONO"
        stop_split_setup "100M"
        stop_split_setup "40M"
        clean_log_files "MONO"
        clean_log_files "NFAPI"
    fi
    
    # Stop sessions on CN server
    if [ -n "$CN_SERVER_USER" ] && [ -n "$CN_SERVER_HOST" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$CN_SERVER_USER@$CN_SERVER_HOST" \
            "screen -X -S iperf-server quit 2>/dev/null || true"
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$CN_SERVER_USER@$CN_SERVER_HOST" \
            "screen -X -S ping-session quit 2>/dev/null || true"
    else
        echo "CN server information not set, skipping CN server reset."
    fi
    
    # Execute remote script on main host if needed
    if [ -n "$GNB_SERVER_USER" ] && [ -n "$GNB_SERVER_HOST" ]; then
        # sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST \
        #     "screen -dmS oaiLONvf bash -c 'echo $SERVER_PASSWORD | sudo -S /oai72/Script/oaiLONvf.sh 2>/dev/null || true'"
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST \
            "screen -dmS oaiLONvf bash -c 'echo $SERVER_PASSWORD | sudo -S source /home/oai72_su/juravf.sh || true'"
    else
        echo "gNB server information not set, skipping remote script execution."
    fi
    
    # Optional: Set RU bandwidth
    # if type radio_unit_utils &>/dev/null; then
    #     echo "Setting RU bandwidth to 100M..."
    #     radio_unit_utils "100000000"
    # fi
    
    echo "Reset complete."
}

# Example usage:
# clean_log_files "MONO"  # Clean log files in monolithic mode
# clean_log_files "NFAPI" # Clean log files in NFAPI mode

# Example usage:
# fetch_and_analyze_logs "MONO"  # For monolithic mode
# fetch_and_analyze_logs "NFAPI" # For NFAPI mode

# Split machine setup stop examples
# stop_split_setup "100M"    # Stop 100M bandwidth setup
# stop_split_setup "40M"     # Stop 40M bandwidth setup

# Single machine setup stop examples
# stop_single_setup "100M" "NFAPI"    # Stop 100M bandwidth NFAPI setup
# stop_single_setup "40M" "NFAPI"     # Stop 40M bandwidth NFAPI setup
# stop_single_setup "100M" "MONO"     # Stop 100M bandwidth MONO setup
# stop_single_setup "40M" "MONO"      # Stop 40M bandwidth MONO setup