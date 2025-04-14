#!/bin/bash

# Global variables
# ADB_DEVICE="0123456789ABCDEF"
source variable.sh

# 函數：檢查操作狀態
check_status() {
    local message=$1
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] $message" | tee -a "$LOG_FILE"
    else
        echo "[ERROR] $message" | tee -a "$LOG_FILE"
    fi
}

# 函數：控制 UE 飛航模式
toggle_airplane_mode() {
    local state=$1
    echo "SSH to $CONTROL_PC_USER@$CONTROL_PC_IP. Setting airplane mode to $state..." | tee -a "$LOG_FILE"
    
    if [ "$state" == "off" ]; then
        ssh "$CONTROL_PC_USER@$CONTROL_PC_IP" "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 0\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false\"" >> "$LOG_FILE" 2>&1
    else
        ssh "$CONTROL_PC_USER@$CONTROL_PC_IP" "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 1\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true\"" >> "$LOG_FILE" 2>&1
    fi

    check_status "Toggle airplane mode to $state on remote CONTROL_PC"
    sleep 5  # 等待網絡穩定
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

# 函數：在 UE 上運行 iperf3 測試
run_iperf() {
    local mode=$1  # 'server' or 'client'
    local server_ip=$2  # 僅客戶端模式需要
    local options=$3  # 額外選項，例如 "-u -b 100M -t 600 -i 1 -l 1300 -p 5201 -R"
    local local_log_path=$4  # 本機儲存日誌的路徑 (可選)
    
    echo "Running iperf3 in $mode mode..." | tee -a "$LOG_FILE"
    
    # 確保我們有 UE IP
    if [ -z "$UE_IP" ]; then
        get_ue_ip
    fi
    
    # 檢查 iperf3 二進制文件是否存在，如果不存在則直接上傳
    local check_iperf=$(sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell ls /data/local/tmp/iperf3 2>/dev/null || echo 'not_exists'")
    
    if [[ "$check_iperf" == *"not_exists"* ]]; then
        echo "iperf3 binary not found on UE. Uploading from Control PC..." | tee -a "$LOG_FILE"
        
        # 使用文檔中提供的固定路徑直接上傳
        local control_pc_iperf_path="C:\\Users\\sshuser\\Desktop\\MTK\\iperf3"
        sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE push \"$control_pc_iperf_path\" /data/local/tmp/iperf3" >> "$LOG_FILE" 2>&1
        
        if [ $? -ne 0 ]; then
            echo "Failed to upload iperf3 binary. Cannot continue." | tee -a "$LOG_FILE"
            return 1
        fi
        
        echo "Successfully uploaded iperf3 binary to UE" | tee -a "$LOG_FILE"
    fi
    
    # 確保 iperf3 有執行權限
    sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell chmod +x /data/local/tmp/iperf3" >> "$LOG_FILE" 2>&1
    
    if [ "$mode" = "server" ]; then
        # 伺服器模式
        echo "Starting iperf3 server on UE ($UE_IP)..." | tee -a "$LOG_FILE"
        sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell /data/local/tmp/iperf3 -s $options" >> "$LOG_FILE" 2>&1 &
        echo "iperf3 server started. Process running in background." | tee -a "$LOG_FILE"
    elif [ "$mode" = "client" ]; then
        # 客戶端模式
        if [ -z "$server_ip" ]; then
            echo "Error: Server IP is required for client mode." | tee -a "$LOG_FILE"
            return 1
        fi
        
        echo "Starting iperf3 client on UE ($UE_IP) connecting to server $server_ip..." | tee -a "$LOG_FILE"
        # 添加 -B 選項以綁定到 UE IP
        local client_cmd="adb -s $ADB_DEVICE shell /data/local/tmp/iperf3 -c $server_ip -B $UE_IP $options"
        echo "Executing: $client_cmd" | tee -a "$LOG_FILE"
        
        # 如果指定了本機日誌路徑，則將結果儲存到UE臨時檔案並下載
        if [ -n "$local_log_path" ]; then
            local timestamp=$(date "+%Y%m%d_%H%M%S")
            local ue_log_file="/data/local/tmp/iperf3_result_${timestamp}.log"
            local control_pc_temp_path="/tmp/iperf3_result_${timestamp}.log"
            
            echo "Saving iperf3 results to $local_log_path" | tee -a "$LOG_FILE"
            
            # 在UE上執行iperf3並將結果儲存到臨時檔案
            sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE shell \"/data/local/tmp/iperf3 -c $server_ip -B $UE_IP $options > $ue_log_file 2>&1\"" | tee -a "$LOG_FILE"
            
            # 從UE下載到控制電腦
            sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "adb -s $ADB_DEVICE pull $ue_log_file $control_pc_temp_path" >> "$LOG_FILE" 2>&1
            check_status "Pulled iperf3 log to control PC"
            
            # 從控制電腦下載到本機
            sshpass -p "$CONTROL_PC_PASSWORD" scp $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP:$control_pc_temp_path "$local_log_path"
            check_status "Downloaded iperf3 log to local machine at $local_log_path"
            
            # 清理臨時檔案
            sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "rm $control_pc_temp_path && adb -s $ADB_DEVICE shell rm $ue_log_file" >> "$LOG_FILE" 2>&1
            
            # 顯示儲存的檔案內容
            echo "iperf3 results saved to $local_log_path. Preview:" | tee -a "$LOG_FILE"
            head -n 20 "$local_log_path" | tee -a "$LOG_FILE"
        else
            # 如果沒有指定本機日誌路徑，則使用原來的方式顯示結果
            sshpass -p "$CONTROL_PC_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP "$client_cmd" | tee -a "$LOG_FILE"
        fi
        check_status "iperf3 client test"
    else
        echo "Error: Invalid mode. Use 'server' or 'client'." | tee -a "$LOG_FILE"
        return 1
    fi
}

# # 示例：開啟飛航模式
# toggle_airplane_mode "on"

# # 示例：關閉飛航模式
# toggle_airplane_mode "off"

## 示：獲取 UE IP (可以透過是否順利取得UE IP判斷gNB是否)
# get_ue_ip

# 示例：在 UE 上運行 iperf3 服務器
# run_iperf "server" "" "-p 5201"

# 示例：在 UE 上運行 iperf3 客戶端
# run_iperf "client" "10.45.0.1" "-u -b 100M -t 10"

# 示例：在 UE 上運行 iperf3 客戶端並儲存日誌到本機
# run_iperf "client" "10.45.0.1" "-u -b 100M -t 10" "/home/ming/iperf3_results.log"

