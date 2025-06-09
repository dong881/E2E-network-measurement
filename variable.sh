#!/bin/bash
# ========================================
# FREQUENTLY ADJUSTED PARAMETERS
# ========================================
# Duration in seconds for tests
export TEST_DURATION=$((60*60))
export SLEEP_WINDOW=5

# Downlink test settings
export DL_START=100
export DL_END=800
export DL_STEP=100

# ========================================
# TEST EXECUTION PARAMETERS
# ========================================
# Test execution mode
export TEST_UDP=true    # Enable UDP testing
export TEST_TCP=false   # Enable TCP testing

# Timing settings
export WAIT_AFTER_REBOOT=60
export WAIT_AFTER_GNB=18

# Test retry settings
export MAX_RETRIES=6

# Uplink test settings
export ENABLE_UL=false
export UL_START=10
export UL_END=120
export UL_STEP=10

# ========================================
# NETWORK ADDRESSES & CREDENTIALS
# ========================================
export SSH_OPTIONS="-o StrictHostKeyChecking=no"
export INTERFACE="ogstun"
export TEST_SERVER_IP="10.45.0.1" # IP for iperf/ping tests

# RU related settings
export RU_IP="192.168.8.77"
export RU_USER="user"
export RU_PASSWORD="user"
export RU_ENABLE_PASSWORD="liteon168"

# JURA RU settings
export JURA_RU_IP="192.168.8.93"
export JURA_RU_USER="root"
export JURA_RU_PASSWORD="root"

# gNB server settings
export VNF_GNB_SERVER_USER="hpe"
export VNF_GNB_SERVER_HOST="192.168.8.26"
export GNB_SERVER_USER="oai72_su"
export GNB_SERVER_HOST="192.168.8.82"
# export GNB_SERVER_USER="oai72"
# export GNB_SERVER_HOST="192.168.8.43"

# Control PC settings
export CONTROL_PC_IP="140.118.162.81" # DESKTOP-3NKR1VR for Samsung UE
# export CONTROL_PC_IP="192.168.8.118"
export CONTROL_PC_USER="sshuser"
export SERVER_PASSWORD="bmwlab"

# KSMO host configuration
export KSMO_HOST="192.168.8.121"
export KSMO_USER="ksmo"
export KSMO_HOME="/home/ksmo"

# Core Network settings
export CN_SERVER_USER="oai-cn"
export CN_SERVER_HOST="192.168.8.108"

# UE settings
export ADB_DEVICE="R5CN30TMBYR" # Samsung UE device ID
# export ADB_DEVICE="0123456789ABCDEF" # MTK UE device ID

# ========================================
# PATH SETTINGS
# ========================================
# Base paths for different servers
export VNF_BASE_PATH="~/OnlyOAI/openairinterface5g"
export PNF_BASE_PATH="~/oai_mp_f_ming/openairinterface5g"
# export PNF_BASE_PATH="~/FH_7.2_dev/openairinterface5g"

# Common build directory and log files
export VNF_LOG_FILE="VNF.txt"
export PNF_LOG_FILE="PNF.txt"
export GNB_LOG_FILE="~/ming.log"

# Local measurement directory
export LOCAL_MEASURE_DIR="~/E2E-network-measurement/Measure/log"

# Analysis script path
export LOG_ANALYSIS_SCRIPT="$LOCAL_MEASURE_DIR/../analyze_logs.py"

# Control PC iperf path
# Control Samsung UE NoteBook
export control_pc_iperf_path="C:\\Users\\$CONTROL_PC_USER\\Desktop\\iperf3"
# Control MTK UE NoteBook
# export control_pc_iperf_path="C:\\Users\\$CONTROL_PC_USER\\Desktop\\MTK\\iperf3"

# Measurement file path
export MEASURE_FILE_PATH="$PNF_BASE_PATH/cmake_targets/ran_build/build/measure.txt"