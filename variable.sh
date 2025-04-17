#!/bin/bash
export INTERFACE="ogstun"
export RU_IP="192.168.8.77"
export RU_USER="user"
export RU_PASSWORD="user"
export RU_ENABLE_PASSWORD="liteon168"
export SERVER_PASSWORD="bmwlab"
export VNF_GNB_SERVER_USER="hpe"
export VNF_GNB_SERVER_HOST="192.168.8.26"
export GNB_SERVER_USER="oai72"
export GNB_SERVER_HOST="192.168.8.43"
export CONTROL_PC_IP="192.168.8.118"
export CONTROL_PC_USER="sshuser"
export CN_SERVER_USER="oai-cn"
export CN_SERVER_HOST="192.168.8.108"
export SERVER_IP="192.168.70.135"
export ADB_DEVICE="0123456789ABCDEF"
export TEST_DURATION=5
export WAIT_AFTER_REBOOT=60
export WAIT_AFTER_GNB=18
export OUTPUT_DIR="test_results_$(date +%Y%m%d)"
export CSV_FILE="$OUTPUT_DIR/results.csv"
export LOG_FILE="$OUTPUT_DIR/test.log"
export VENV_DIR="$OUTPUT_DIR/venv"

# mkdir -p "$OUTPUT_DIR"