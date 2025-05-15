#!/bin/bash
# export ADB_DEVICE="0123456789ABCDEF" # MTK UE device ID
export ADB_DEVICE="R5CN30TMBYR" # Samsung UE device ID
export TEST_DURATION=30 # Duration in seconds (updated from main.sh)
export WAIT_AFTER_REBOOT=60
export WAIT_AFTER_GNB=18

# Test execution parameters from main.sh
export MAX_RETRIES=6
export TEST_UDP=true
export TEST_TCP=false
export DL_START=100
export DL_END=800
export DL_STEP=100
export ENABLE_UL=false
export UL_START=10
export UL_END=120
export UL_STEP=10
export SLEEP_WINDOW=5 # Renamed from SLEEP_window

# Base paths for different servers
VNF_BASE_PATH="/home/hpe/OnlyOAI/openairinterface5g"
PNF_NFAPI_BASE_PATH="/home/oai72_su/oai_mp_f_ming/openairinterface5g"

# Common build directory and log files
BUILD_DIR="cmake_targets/ran_build/build"
VNF_LOG_FILE="VNF.txt"
PNF_LOG_FILE="PNF.txt"

# Local measurement directory
LOCAL_MEASURE_DIR="/home/ming/E2E-network-measurement/Measure/log"

# Analysis script path
LOG_ANALYSIS_SCRIPT="$LOCAL_MEASURE_DIR/../analyze_logs.py"
