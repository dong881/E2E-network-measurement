#!/bin/bash

# Global variables
VNF_USER="hpe"
VNF_HOST="192.168.8.26"
Main_USER="oai72"
Main_HOST="192.168.8.43"
PASSWORD="bmwlab"

# Commands for Split Machine Setup (Two Machines)
CMD_VNF_100M_SPLIT="cd ~/OnlyOAI/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.273prb.nfapi.conf --nfapi VNF"
CMD_VNF_40M_SPLIT="cd ~/OnlyOAI/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.106prb.nfapi.conf --nfapi VNF"
CMD_PNF_SPLIT="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-pnf-twoMachine.band78.fhi72.4x4-liteon_new.conf --nfapi PNF --reorder-thread-disable 1 --thread-pool 1,3,5,7,9,11,13,15"

# Commands for Single Machine Setup
CMD_VNF_100M_SINGLE="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.273prb.nfapi.conf --nfapi VNF"
CMD_MONO_100M_SINGLE="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.273prb.fhi72.4x4-liteon_new.conf --thread-pool 1,3,5,7,9,11,13,15"
CMD_VNF_40M_SINGLE="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.106prb.nfapi.conf --nfapi VNF"
CMD_MONO_40M_SINGLE="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.106prb.fhi72.4x4-liteon_new --thread-pool 1,3,5,7,9,11,13,15"
CMD_PNF_SINGLE="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-pnf.band78.fhi72.4x4-liteon_new.conf --nfapi PNF --reorder-thread-disable 1 --thread-pool 1,3,5,7,9,11,13,15"

# PNF Command (Common)

# Function to start a screen session
start_session() {
    local session_name=$1
    local command=$2
    local target_user=$3
    local target_host=$4
    
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "screen -dmS $session_name bash -c '$command'"
}

# Function to stop a screen session
stop_session() {
    local session_name=$1
    local target_user=$2
    local target_host=$3
    
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "screen -X -S $session_name quit"
}

# Function to start split machine setup
start_split_setup() {
    local bandwidth=$1  # 100M or 40M
    
    if [ "$bandwidth" = "100M" ]; then
        start_session "VNF_100M" "$CMD_VNF_100M_SPLIT" "$VNF_USER" "$VNF_HOST"
        start_session "PNF" "$CMD_PNF_SPLIT" "$Main_USER" "$Main_HOST"
    elif [ "$bandwidth" = "40M" ]; then
        start_session "VNF_40M" "$CMD_VNF_40M_SPLIT" "$VNF_USER" "$VNF_HOST"
        start_session "PNF" "$CMD_PNF_SPLIT" "$Main_USER" "$Main_HOST"
    fi
}

# Function to start single machine setup
start_single_setup() {
    local bandwidth=$1  # 100M or 40M
    local mode=$2      # NFAPI or MONO
    
    if [ "$bandwidth" = "100M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            start_session "VNF_100M" "$CMD_VNF_100M_SINGLE" "$Main_USER" "$Main_HOST"
            start_session "PNF" "$CMD_PNF_SINGLE" "$Main_USER" "$Main_HOST"
        else
            start_session "MONO_100M" "$CMD_MONO_100M_SINGLE" "$Main_USER" "$Main_HOST"
        fi
    elif [ "$bandwidth" = "40M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            start_session "VNF_40M" "$CMD_VNF_40M_SINGLE" "$Main_USER" "$Main_HOST"
            start_session "PNF" "$CMD_PNF_SINGLE" "$Main_USER" "$Main_HOST"
        else
            start_session "MONO_40M" "$CMD_MONO_40M_SINGLE" "$Main_USER" "$Main_HOST"
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
        stop_session "VNF_100M" "$VNF_USER" "$VNF_HOST"
        stop_session "PNF" "$Main_USER" "$Main_HOST"
    elif [ "$bandwidth" = "40M" ]; then
        stop_session "VNF_40M" "$VNF_USER" "$VNF_HOST"
        stop_session "PNF" "$Main_USER" "$Main_HOST"
    fi
}

# Function to stop single machine setup
stop_single_setup() {
    local bandwidth=$1  # 100M or 40M
    local mode=$2      # NFAPI or MONO
    
    if [ "$bandwidth" = "100M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            stop_session "VNF_100M" "$Main_USER" "$Main_HOST"
            stop_session "PNF" "$Main_USER" "$Main_HOST"
        else
            stop_session "MONO_100M" "$Main_USER" "$Main_HOST"
        fi
    elif [ "$bandwidth" = "40M" ]; then
        if [ "$mode" = "NFAPI" ]; then
            stop_session "VNF_40M" "$Main_USER" "$Main_HOST"
            stop_session "PNF" "$Main_USER" "$Main_HOST"
        else
            stop_session "MONO_40M" "$Main_USER" "$Main_HOST"
        fi
    fi
}

# Split machine setup stop examples
# stop_split_setup "100M"    # Stop 100M bandwidth setup
# stop_split_setup "40M"     # Stop 40M bandwidth setup

# Single machine setup stop examples
# stop_single_setup "100M" "NFAPI"    # Stop 100M bandwidth NFAPI setup
# stop_single_setup "40M" "NFAPI"     # Stop 40M bandwidth NFAPI setup
# stop_single_setup "100M" "MONO"     # Stop 100M bandwidth MONO setup
# stop_single_setup "40M" "MONO"      # Stop 40M bandwidth MONO setup