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
export TEST_SERVER_IP="10.45.0.1" # IP for iperf/ping tests
export OUTPUT_DIR="test_results_$(date +%Y%m%d)"
export control_pc_iperf_path="C:\Users\sshuser\Desktop\MTK\iperf3"

# Source the run configuration
source "$(dirname "$0")/run_config.sh"

# mkdir -p "$OUTPUT_DIR"