#!/bin/bash

# 配置參數（請根據實際環境修改）
RU_IP="192.168.8.77"
RU_USER="user"
RU_PASSWORD="user"
RU_ENABLE_PASSWORD="liteon168"
GNB_SERVER_USER="oai72"
GNB_SERVER_HOST="192.168.8.43"
GNB_SERVER_PASSWORD="bmwlab"
CONTROL_PC_IP="192.168.8.118"
CONTROL_PC_USER="sshuser"
CONTROL_PC_PASSWORD="bmwlab"
CN_SERVER_USER="open5gs"
CN_SERVER_HOST="192.168.8.108"
CN_SERVER_PASSWORD="bmwlab"
SERVER_IP="192.168.70.135"
ADB_DEVICE="0123456789ABCDEF"
TEST_DURATION=5
WAIT_AFTER_REBOOT=60
WAIT_AFTER_GNB=18
OUTPUT_DIR="test_results_$(date +%Y%m%d_%H%M%S)"
CSV_FILE="$OUTPUT_DIR/results.csv"
LOG_FILE="$OUTPUT_DIR/test.log"
VENV_DIR="$OUTPUT_DIR/venv"

# SSH 選項設定
SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

# 確保必要的工具都已安裝
for cmd in expect ssh sshpass python3; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed. Please install it first." >&2
        exit 1
    fi
done

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"
echo "Test started at $(date)" > "$LOG_FILE"

# 函數：檢查命令是否成功
check_status() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed. Check $LOG_FILE for details." >&2
        exit 1
    fi
}

# Function: set_ru_bandwidth
# Description: Sets the bandwidth for a Remote Unit (RU) device via SSH
#
# This function performs the following operations:
# 1. Creates an expect script to handle SSH interaction
# 2. Logs into the RU using provided credentials
# 3. Checks current bandwidth
# 4. Sets new bandwidth value
# 5. Verifies the change
# 6. Reboots the RU if bandwidth was changed
#
# Arguments:
#   $1 - bandwidth value in bps (bits per second)
#
# Environment variables required:
#   RU_USER - Username for RU SSH login
#   RU_IP - IP address of the RU
#   RU_PASSWORD - Password for RU SSH login
#   RU_ENABLE_PASSWORD - Enable password for privileged mode
#   OUTPUT_DIR - Directory for output files
#   LOG_FILE - Path to log file
#   WAIT_AFTER_REBOOT - Time to wait after reboot in seconds
#
# Returns:
#   0 on success, non-zero on failure
#
# Outputs:
#   - Writes progress messages to LOG_FILE
#   - Creates expect script at $OUTPUT_DIR/set_bandwidth.exp
#   - Creates output log at $OUTPUT_DIR/set_bandwidth.out


set_ru_bandwidth() {
    local bw=$1
    echo "Setting RU bandwidth to $bw bps..." | tee -a "$LOG_FILE"
    
    cat << 'EOF' > "$OUTPUT_DIR/set_bandwidth.exp"
#!/usr/bin/expect
log_file -a "$env(OUTPUT_DIR)/set_bandwidth.out"
set timeout 60

spawn ssh $env(RU_USER)@$env(RU_IP)
expect "password:"
send "$env(RU_PASSWORD)\r"
expect ">"
send "enable\r"
expect "Password:"
send "$env(RU_ENABLE_PASSWORD)\r"
expect "#"

# 先檢查當前帶寬
send "show running-config\r"
expect "#"

# 設定新帶寬
send "configure terminal\r"
expect "(config)#"
send "bandwidth $env(bw)\r"
expect "(config)#"
send "exit\r"
expect "#"

# 確認新帶寬
send "show running-config\r"
expect "#"

# 如果需要重啟，就在同一個 session 執行
if {[catch {set old_bw [exec grep "Band Width = " $env(OUTPUT_DIR)/set_bandwidth.out | head -1 | cut -d= -f2 | tr -d " "]}]} {
    set old_bw "unknown"
}
if {$old_bw != $env(bw)} {
    send "reboot\r"
    expect "system is going down"
}
expect eof
EOF

    chmod +x "$OUTPUT_DIR/set_bandwidth.exp"
    
    export RU_USER RU_IP RU_PASSWORD RU_ENABLE_PASSWORD OUTPUT_DIR bw=$bw
    expect "$OUTPUT_DIR/set_bandwidth.exp" >> "$LOG_FILE" 2>&1
    check_status "SSH to RU and set bandwidth"
    
    # 檢查是否執行了重啟
    if grep -q "system is going down" "$OUTPUT_DIR/set_bandwidth.out"; then
        echo "Bandwidth changed to $bw. RU is rebooting..." | tee -a "$LOG_FILE"
        echo "Waiting $WAIT_AFTER_REBOOT seconds for RU to reboot..." | tee -a "$LOG_FILE"
        sleep $WAIT_AFTER_REBOOT
    else
        echo "Bandwidth unchanged. No reboot needed." | tee -a "$LOG_FILE"
    fi
}

# 函數：SSH 到 gNB 並啟動服務（使用 screen 啟動不同模式）
start_gnb() {
    local mode=$1
    local bandwidth=$2
    echo "Starting gNB in $mode mode with bandwidth $bandwidth..." | tee -a "$LOG_FILE"
    export GNB_SERVER_USER GNB_SERVER_HOST GNB_SERVER_PASSWORD

    local session_name
    local command

    if [ "$mode" == "nFAPI" ]; then
        session_name="VNF_${bandwidth}"
        if [ "$bandwidth" == "40000000" ]; then
            command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$GNB_SERVER_PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.106prb.nfapi.conf --nfapi VNF"
        else
            command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$GNB_SERVER_PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.273prb.nfapi.conf --nfapi VNF"
        fi
        sshpass -p "$GNB_SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "screen -dmS $session_name bash -c '$command'"
        check_status "Start gNB VNF"

        session_name="PNF_${bandwidth}"
        command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$GNB_SERVER_PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-pnf.band78.fhi72.4x4-liteon_new.conf --nfapi PNF --reorder-thread-disable 1 --thread-pool 1,3,5,7,9,11,13,15"
        sshpass -p "$GNB_SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "screen -dmS $session_name bash -c '$command'"
        check_status "Start gNB PNF"
    else  # FAPI
        session_name="Monolithic_${bandwidth}"
        if [ "$bandwidth" == "40000000" ]; then
            command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$GNB_SERVER_PASSWORD' | sudo -S ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.106prb.fhi72.4x4-liteon_new --thread-pool 1,3,5,7,9,11,13,15"
        else
            command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$GNB_SERVER_PASSWORD' | sudo -S ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.273prb.fhi72.4x4-liteon_new.conf --thread-pool 1,3,5,7,9,11,13,15"
        fi
        sshpass -p "$GNB_SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "screen -dmS $session_name bash -c '$command'"
        check_status "Start gNB Monolithic"
    fi

    echo "Waiting $WAIT_AFTER_GNB seconds for gNB to initialize..." | tee -a "$LOG_FILE"
    sleep $WAIT_AFTER_GNB
}

# 函數：控制 UE 飛航模式
toggle_airplane_mode() {
    local state=$1
    echo "SSH to $CONTROL_PC_USER@$CONTROL_PC_IP. Setting airplane mode to $state..." | tee -a "$LOG_FILE"
    
    if [ "$state" == "off" ]; then
        sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 0\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false\"" >> "$LOG_FILE" 2>&1
        sleep 5  # 等待網絡穩定
    else
        sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 1\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true\"" >> "$LOG_FILE" 2>&1
    fi

    check_status "Toggle airplane mode to $state on remote CONTROL_PC"
}

# 函數：獲取 UE IP
get_ue_ip() {
    # echo "Fetching UE IP from $CONTROL_PC_IP..." | tee -a "$LOG_FILE"
    UE_IP=$(sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell ip -f inet addr show ccmni0" | grep inet | awk '{print $2}' | cut -d/ -f1)
    if [ -z "$UE_IP" ]; then
        UE_IP=$(sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell ip -f inet addr show ccmni1" | grep inet | awk '{print $2}' | cut -d/ -f1)
    fi
    if [ -z "$UE_IP" ]; then
        echo "Error: Unable to fetch UE IP." >&2
        exit 1
    fi
    echo "UE IP: $UE_IP" | tee -a "$LOG_FILE"
}

